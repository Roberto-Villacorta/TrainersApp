# -*- coding: utf-8 -*-
"""
Módulo de servicio de Inteligencia Artificial para extracción de rutinas.

Este módulo proporciona herramientas para extraer datos estructurados de
ejercicios a partir de texto sin formato o tabular obtenido mediante OCR.
El flujo principal es el siguiente:

1. Se normaliza y limpia el texto de entrada.
2. Se detecta automáticamente si el texto tiene formato tabular o libre.
3. Si es tabular → parser directo (rápido, sin modelo neuronal).
4. Si es texto libre → modelo GLiNER (NER multilingüe).

Uso básico::

    from logica.ia_service import GlinerService

    serv = GlinerService()
    resultados = serv.procesar_texto_rutina(texto_ocr)

Uso de debug::

    info = serv.procesar_texto_rutina_debug(texto_ocr)
    print(info["modo_detectado"])   # "tabla" | "gliner"
    print(info["resultado"])        # lista de ejercicios / entidades

Constantes de configuración:
    MODEL_NAME (str): Nombre del modelo GLiNER en HuggingFace.
    THRESHOLD_DEFAULT (float): Umbral de confianza mínimo para entidades GLiNER.
    MODEL_DIR (str): Ruta local donde se guardan los modelos descargados.
"""

import os
import re
import math
import unicodedata
import difflib
from typing import Dict, List, Optional, Any, Tuple, Union
from utils.logger import app_logger
from utils.text_utils import normalizar_texto_base as _normalizar_texto_base, quitar_acentos as _quitar_acentos
from logica.exercise_data import EJERCICIOS_CANONICOS, ABREVIATURAS, ExpansorAbreviaturas
from utils.paths import get_models_dir

# ---------------------------------------------------------------------------
# Configuración de rutas y constantes globales
# ---------------------------------------------------------------------------

#: Directorio local donde se almacenan los modelos HuggingFace descargados.
MODEL_DIR: str = str(get_models_dir() / "gliner")

#: Nombre del modelo GLiNER en HuggingFace Hub.
MODEL_NAME: str = "urchade/gliner_multi-v2.1"

#: Umbral de confianza mínimo (score) para aceptar una entidad detectada por GLiNER.
#: Las entidades con score < THRESHOLD_DEFAULT se descartan.
#: Se baja a 0.3 para permitir una normalización zero-shot más flexible.
THRESHOLD_DEFAULT: float = 0.3

# Redirigir descarga de modelos HuggingFace a la carpeta local.
os.environ["HF_HOME"] = MODEL_DIR


# ─────────────────────────────────────────────────────────────────
# NORMALIZACIÓN DE TEXTO
# ─────────────────────────────────────────────────────────────────



def _normalizar_clave_abrev(clave: str) -> str:
    """Mapeo legacy a la nueva lógica en exercise_data."""
    from logica.exercise_data import _normalizar_clave_abrev as norm_clave
    return norm_clave(clave)

# Instancia global del expansor para mantener compatibilidad con el resto del código
EXPANSOR: ExpansorAbreviaturas = ExpansorAbreviaturas(ABREVIATURAS)

def _expandir_abreviaturas(texto: str) -> str:
    """Delega la expansión al motor especializado en exercise_data."""
    return EXPANSOR.expandir(texto)


# ─────────────────────────────────────────────────────────────────
# DETECCIÓN DE FORMATO TABULAR
# ─────────────────────────────────────────────────────────────────

#: Tokens que identifican líneas de metadatos (encabezado del plan de entrenamiento).
#: Estas líneas se excluyen del análisis heurístico de columnas en :func:`_es_tabla`.
_TOKENS_METADATOS: tuple = ("mesociclo", "semana", "sesion", "session", "week")


def _es_tabla(texto: str) -> bool:
    """Detecta si el texto tiene estructura tabular (columnas alineadas o con tab).

    Heurística en dos pasos:

    1. **Tabulaciones**: si al menos la mitad de las líneas contienen ``\\t``,
       se considera tabla.
    2. **Espaciado múltiple**: si al menos la mitad de las líneas *de datos*
       (excluyendo líneas de metadatos) contienen dos o más espacios
       consecutivos entre tokens, se considera tabla.

    Las líneas de metadatos ("Mesociclo", "Semana", "Sesion"…) se excluyen
    del análisis para evitar falsos positivos en textos con una sola línea
    de cabecera.

    Args:
        texto: Texto posiblemente tabular.

    Returns:
        ``True`` si el texto parece tabular, ``False`` en caso contrario.

    Examples:
        >>> _es_tabla("Ejercicio\\tReps\\tPeso\\nPress Banca\\t3\\t80")
        True
        >>> _es_tabla("Haz 3 series de press banca con 80 kg")
        False
    """
    lineas = [l for l in texto.strip().splitlines() if l.strip()]
    if len(lineas) < 2:
        return False

    # Criterio 1: mayoría de líneas con tabuladores
    con_tab = sum(1 for l in lineas if "\t" in l)
    if con_tab >= max(1, len(lineas) // 2):
        return True

    # Criterio 2: líneas de datos (sin metadatos) con espaciado múltiple
    lineas_datos = [
        l for l in lineas
        if not any(
            token in _normalizar_texto_base(l)
            for token in _TOKENS_METADATOS
        )
    ]

    if not lineas_datos:
        return False

    umbral = max(1, math.ceil(len(lineas_datos) / 2))
    con_columnas = sum(
        1 for l in lineas_datos if re.search(r"\S+\s{2,}\S+", l)
    )
    return con_columnas >= umbral


# ─────────────────────────────────────────────────────────────────
# EXTRACCIÓN DE METADATOS
# ─────────────────────────────────────────────────────────────────

def _extraer_metadatos(texto: str) -> Dict[str, Optional[str]]:
    """Extrae metadatos de planificación (mesociclo, semana, sesión) del texto.

    Busca patrones del tipo ``"Mesociclo 9"``, ``"Semana 55"``,
    ``"Sesion P1"`` usando expresiones regulares sobre el texto normalizado.

    Args:
        texto: Texto OCR que puede contener líneas de cabecera.

    Returns:
        Diccionario con claves ``"mesociclo"``, ``"semana"`` y ``"sesion"``.
        Cada valor es la cadena encontrada (p.ej. ``"9"``, ``"55"``, ``"P1"``)
        o ``None`` si no se encontró.

    Examples:
        >>> _extraer_metadatos("Mesociclo 9  Semana 55  Sesion P1")
        {'mesociclo': '9', 'semana': '55', 'sesion': 'p1'}
    """
    t = _normalizar_texto_base(texto)
    meta: Dict[str, Optional[str]] = {
        "mesociclo": None,
        "semana": None,
        "sesion": None,
    }

    m = re.search(r"\bmesociclo\s*([a-z0-9]+)\b", t, re.IGNORECASE)
    if m:
        meta["mesociclo"] = m.group(1)

    s = re.search(r"\bsemana\s*([a-z0-9]+)\b", t, re.IGNORECASE)
    if s:
        meta["semana"] = s.group(1)

    se = re.search(r"\b(?:sesion|ses)\s*([a-z0-9]+)\b", t, re.IGNORECASE)
    if se:
        meta["sesion"] = se.group(1)

    return meta


# ─────────────────────────────────────────────────────────────────
# HELPERS DE PARSING
# ─────────────────────────────────────────────────────────────────

#: Patrón para detectar series con formato ``NxPESO`` o ``N × PESO``.
#: Captura grupos nombrados ``reps`` (entero) y ``peso`` (decimal con coma o punto).
_PATRON_SERIE: re.Pattern = re.compile(
    r"(?P<reps>\d+)\s*[xX×]\s*(?P<peso>[\d.,]+)",
    re.IGNORECASE,
)


def _normalizar_nombre_ejercicio(nombre: str) -> str:
    """Normaliza el nombre de un ejercicio para presentación.

    Pasos:
    1. Expande abreviaturas con :func:`_expandir_abreviaturas`.
    2. Colapsa espacios múltiples.
    3. Aplica ``.title()`` para capitalizar cada primera letra.

    Args:
        nombre: Nombre crudo del ejercicio (puede contener abreviaturas).

    Returns:
        Nombre normalizado y capitalizado, o ``""`` si la entrada es vacía.

    Examples:
        >>> _normalizar_nombre_ejercicio("elev lat")
        'Elevaciones Laterales'
        >>> _normalizar_nombre_ejercicio("")
        ''
    """
    if not nombre:
        return ""
    nombre = _expandir_abreviaturas(nombre)
    nombre = re.sub(r"\s+", " ", nombre).strip()
    return nombre.title()


def _parsear_serie(celda: str) -> Optional[Dict[str, Any]]:
    """Intenta extraer repeticiones y peso de una celda de tabla.

    Reconoce el formato ``NxPESO``, ``N × PESO`` y variantes (mayúsculas,
    coma decimal). Si la celda no contiene el patrón esperado, o si los
    valores no son convertibles a número, devuelve ``None``.

    Args:
        celda: Contenido de una celda del OCR (p.ej. ``"10x42,5"``).

    Returns:
        Diccionario ``{"reps": int, "peso_kg": float}`` o ``None`` si la
        celda está vacía, malformada o no contiene series.

    Examples:
        >>> _parsear_serie("10x42,5")
        {'reps': 10, 'peso_kg': 42.5}
        >>> _parsear_serie("—")
        None
        >>> _parsear_serie("10xabc")
        None
    """
    if not celda:
        return None

    celda = _normalizar_texto_base(celda)
    match = _PATRON_SERIE.search(celda)
    if not match:
        return None

    try:
        reps = int(match.group("reps"))
        peso_str = match.group("peso").replace(",", ".")
        peso = float(peso_str)
    except (ValueError, AttributeError):
        return None

    return {"reps": reps, "peso_kg": peso}


def _split_columnas(linea: str) -> List[str]:
    """Divide una línea en columnas usando tabulaciones o espaciado múltiple.

    Preferencia: si la línea contiene tabulaciones (``\\t``), se parte
    por ellas. Caso contrario, se usa dos o más espacios consecutivos
    como separador.

    Args:
        linea: Línea de texto (ya sin newline al final).

    Returns:
        Lista de strings no vacíos con el contenido de cada columna.

    Examples:
        >>> _split_columnas("Press Banca\\t7-12\\t10x80")
        ['Press Banca', '7-12', '10x80']
        >>> _split_columnas("Sentadilla  5-8  8x120  8x120")
        ['Sentadilla', '5-8', '8x120', '8x120']
    """
    if "\t" in linea:
        return [c.strip() for c in re.split(r"\t+", linea.strip()) if c.strip()]
    return [c.strip() for c in re.split(r"\s{2,}", linea.strip()) if c.strip()]


# ─────────────────────────────────────────────────────────────────
# PARSER TABULAR
# ─────────────────────────────────────────────────────────────────

#: Nombres de columnas que indican una fila de cabecera a descartar.
_CABECERAS_TABLA: tuple = ("ejercicio", "exercise", "serie", "rango")

#: Tokens que identifican filas de metadatos (se descartan en el parser tabular).
_TOKENS_SKIP_TABLA: tuple = ("ejercicio", "exercise", "mesociclo", "semana", "sesion")


def _parsear_tabla(texto: str) -> List[Dict[str, Any]]:
    """Parsea texto tabular OCR y extrae una lista de ejercicios estructurados.

    Formato esperado (con tabs o espaciado doble)::

        Mesociclo 9  Semana 55  Sesion 71
        Ejercicio  Rango  Serie 1  Serie 2  Serie 3  Serie 4
        Press Banca  7-12  10x80  9x80  8x82
        Remo  6-10  10x110  9x115

    Lógica:
    1. Extrae metadatos de la primera línea si contiene palabras clave.
    2. Detecta y omite filas de cabecera (Ejercicio / Exercise / Rango…).
    3. Para cada fila de datos: columna 0 → ejercicio, columna 1 → rango,
       columnas 2+ → series (parseadas con :func:`_parsear_serie`).
    4. Omite filas cuyo primer token es un token de metadatos.

    Args:
        texto: Texto tabular procedente de OCR.

    Returns:
        Lista de diccionarios con la estructura::

            {
                "ejercicio":      str,            # nombre normalizado
                "rango_objetivo": str,            # p.ej. "7-12" o "—"
                "series":         List[dict],     # [{"reps": int, "peso_kg": float}, ...]
                "origen":         "tabla",
                "mesociclo":      str | None,
                "semana":         str | None,
                "sesion":         str | None,
            }

        Lista vacía si el texto está vacío o no contiene filas de datos.
    """
    lineas = [l for l in texto.strip().splitlines() if l.strip()]
    resultados: List[Dict[str, Any]] = []

    if not lineas:
        return resultados

    meta = _extraer_metadatos(texto)

    # Determinar desde qué línea empiezan los datos (saltar cabecera si existe)
    datos = lineas[:]
    primera_norm = _normalizar_texto_base(lineas[0])
    if any(x in primera_norm for x in _CABECERAS_TABLA):
        datos = lineas[1:]

    for linea in datos:
        columnas = _split_columnas(linea)
        if not columnas:
            continue

        nombre_raw = columnas[0].strip()
        if not nombre_raw:
            continue

        nombre_norm = _normalizar_texto_base(nombre_raw)

        # Saltar filas de metadatos o cabeceras residuales
        if any(token in nombre_norm for token in _TOKENS_SKIP_TABLA):
            continue

        ejercicio = _normalizar_nombre_ejercicio(nombre_raw)
        rango = columnas[1].strip() if len(columnas) > 1 else "—"

        series: List[Dict[str, Any]] = []
        for celda in columnas[2:]:
            parsed = _parsear_serie(celda)
            if parsed:
                series.append(parsed)

        # Adaptar al formato esperado por la interfaz y la base de datos
        rep_val = rango if rango != "—" else (str(series[0]["reps"]) if series else "?")
        peso_val = str(series[0]["peso_kg"]) if series else "?"

        resultados.append({
            "nombre_ejercicio": ejercicio,
            "repeticiones":     rep_val,
            "peso_objetivo":    peso_val,
            "series":           str(len(series)) if series else "0",
            "origen":           "tabla",
            "mesociclo":        meta["mesociclo"],
            "semana":           meta["semana"],
            "sesion":           meta["sesion"],
        })

    return resultados


def _match_acronimo(texto: str, canonico: str) -> bool:
    """Comprueba si un texto es un acrónimo de un nombre canónico.

    Ejemplos:
        'pm' -> 'peso muerto' (p m)
        'rdl' -> 'rumanian deadlift' (aunque aquí usamos 'peso muerto rumano')
    """
    if not texto or len(texto) < 2:
        return False

    tokens_canon = _normalizar_texto_base(canonico).split()
    if len(tokens_canon) < len(texto):
        return False

    # El acrónimo debe coincidir con la primera letra de los primeros N tokens
    # O ser una sub-secuencia de las iniciales
    iniciales = "".join(t[0] for t in tokens_canon if t)
    return texto in iniciales


def _buscar_mejor_coincidencia_semantica(nombre: str) -> Optional[str]:
    """Busca la mejor coincidencia del catálogo basándose en fragmentos y acrónimos.

    Util para casos de truncamiento extremo sin espacios (ej: 'elevlatmanc').
    Orquesta tres estrategias:
    1. Coincidencia exacta/prefijo.
    2. Acrónimos (pm -> peso muerto).
    3. Similitud estructural (difflib).

    Args:
        nombre: Nombre sucio o truncado.

    Returns:
        Nombre canónico si se encuentra una coincidencia clara, else None.
    """
    clean = _normalizar_texto_base(nombre).replace(" ", "")
    if len(clean) < 2:
        return None

    # 1. Coincidencia por prefijo o contenido exacto (O(n))
    for canonico in EJERCICIOS_CANONICOS:
        canon_norm = _normalizar_texto_base(canonico).replace(" ", "")
        if canon_norm.startswith(clean) or clean in canon_norm:
            # Si el match es muy corto, ser más exigente
            if len(clean) <= 3 and not canon_norm.startswith(clean):
                continue
            return canonico

    # 2. Match por Acrónimo
    for canonico in EJERCICIOS_CANONICOS:
        if _match_acronimo(clean, canonico):
            return canonico

    # 3. Búsqueda por ratio de similitud (SequenceMatcher)
    mejor_match = None
    max_ratio = 0.0
    es_muy_corto = len(clean) <= 4

    for canonico in EJERCICIOS_CANONICOS:
        canon_norm = _normalizar_texto_base(canonico).replace(" ", "")
        
        # Calcular ratio de similitud estructural
        ratio = difflib.SequenceMatcher(None, clean, canon_norm).ratio()
        
        # Bonus extra si el nombre sucio es un prefijo de alguna palabra del canon
        tokens_canon = canonico.lower().split()
        if any(palabra.startswith(clean[:2]) for palabra in tokens_canon if len(palabra) >= 2):
            ratio += 0.15

        if ratio > max_ratio:
            max_ratio = ratio
            mejor_match = canonico

    # Umbral dinámico
    umbral = 0.45 if not es_muy_corto else 0.65
    if mejor_match and max_ratio >= umbral:
        return mejor_match

    return None


# ─────────────────────────────────────────────────────────────────
# SERVICIO PRINCIPAL — GlinerService
# ─────────────────────────────────────────────────────────────────

class GlinerService:
    """Servicio principal de extracción de datos de rutinas de entrenamiento.

    Orquesta dos estrategias de extracción:

    - **Parser tabular** (:func:`_parsear_tabla`): rápido, determinista,
      no requiere modelo. Se activa cuando :func:`_es_tabla` devuelve ``True``.
    - **GLiNER** (NER neuronal): extrae entidades (ejercicio, series,
      repeticiones, peso, descanso) de texto libre mediante el modelo
      ``urchade/gliner_multi-v2.1``.

    El modelo GLiNER se carga de forma perezosa (lazy-loading) la primera
    vez que se necesita y se almacena como atributo de clase (singleton)
    para evitar cargarlo múltiples veces en la misma sesión.

    .. warning::
        El singleton ``_modelo`` no es thread-safe. En entornos con múltiples
        hilos concurrentes la primera carga puede ejecutarse varias veces.
        Se recomienda pre-cargar el modelo con ``cargar_modelo()`` durante
        la inicialización de la aplicación.

    Args:
        cargar_modelo_al_inicio: Si ``True``, carga el modelo GLiNER
            inmediatamente en el constructor. Por defecto ``False`` (lazy).
        threshold: Umbral de confianza mínimo para aceptar entidades GLiNER.
            Entidades con score **menor** que este valor se descartan.
            Por defecto :data:`THRESHOLD_DEFAULT` (0.4).

    Attributes:
        labels (List[str]): Etiquetas de entidad que reconoce GLiNER.
        model_name (str): Nombre del modelo en HuggingFace Hub.
        threshold (float): Umbral de confianza activo.

    Example::

        serv = GlinerService()
        resultados = serv.procesar_texto_rutina(texto_ocr)

        # Forzar carga previa del modelo (útil en aplicaciones de escritorio)
        serv = GlinerService(cargar_modelo_al_inicio=True)
    """

    #: Singleton del modelo GLiNER compartido entre todas las instancias.
    _modelo: Any = None

    def __init__(
        self,
        cargar_modelo_al_inicio: bool = False,
        threshold: float = THRESHOLD_DEFAULT,
    ) -> None:
        self.labels: List[str] = [
            "ejercicio",
            "series",
            "repeticiones",
            "peso en kg",
            "descanso",
        ]
        self.model_name: str = MODEL_NAME
        self.threshold: float = threshold

        if cargar_modelo_al_inicio:
            self.cargar_modelo()

    # ── Carga del modelo ─────────────────────────────────────────────────

    def cargar_modelo(self) -> None:
        """Carga el modelo GLiNER desde HuggingFace (o caché local) si aún no está cargado.

        Es idempotente: si el modelo ya está en ``GlinerService._modelo``,
        no hace nada. Registra el proceso en el logger de la aplicación.

        Raises:
            Exception: Cualquier error de descarga o carga del modelo
                se registra en el logger y se re-lanza para que el
                caller pueda manejarlo.
        """
        if GlinerService._modelo is None:
            app_logger.info(
                f"Cargando modelo GLiNER ({self.model_name}) en {MODEL_DIR}..."
            )
            try:
                from gliner import GLiNER
                GlinerService._modelo = GLiNER.from_pretrained(self.model_name)
                app_logger.info("Modelo GLiNER cargado correctamente.")
            except ImportError:
                app_logger.error("La librería 'gliner' no está instalada. Ejecute 'pip install gliner'.")
                raise RuntimeError("La función de IA avanzada (GLiNER) no está disponible porque falta la librería necesaria.")
            except Exception as e:
                app_logger.error(f"Error cargando GLiNER: {e}")
                raise

    # ── Métodos públicos de utilidad (también usados en tests) ───────────

    def expandir_abreviaturas(self, texto: str) -> str:
        """Expande abreviaturas de ejercicios en el texto dado.

        Wrapper público de :func:`_expandir_abreviaturas` para uso directo
        en tests o scripts de inspección sin acceder a funciones privadas.

        Args:
            texto: Texto con posibles abreviaturas.

        Returns:
            Texto con abreviaturas expandidas.
        """
        return _expandir_abreviaturas(texto)

    def diagnosticar_abreviaturas(self, texto: str) -> Dict[str, Any]:
        """Devuelve diagnóstico detallado de las expansiones aplicadas.

        Wrapper público de :meth:`ExpansorAbreviaturas.diagnosticar`.

        Args:
            texto: Texto a diagnosticar.

        Returns:
            Diccionario con ``original``, ``normalizado``, ``expandido`` y
            ``abreviaturas_detectadas``. Ver :meth:`ExpansorAbreviaturas.diagnosticar`.
        """
        return EXPANSOR.diagnosticar(texto)

    def es_tabla(self, texto: str) -> bool:
        """Comprueba si el texto tiene estructura tabular.

        Wrapper público de :func:`_es_tabla`.

        Args:
            texto: Texto a evaluar.

        Returns:
            ``True`` si se detecta formato tabular.
        """
        return _es_tabla(texto)

    def extraer_metadatos(self, texto: str) -> Dict[str, Optional[str]]:
        """Extrae metadatos de planificación del texto.

        Wrapper público de :func:`_extraer_metadatos`.

        Args:
            texto: Texto con posible cabecera de mesociclo/semana/sesión.

        Returns:
            Diccionario ``{"mesociclo": ..., "semana": ..., "sesion": ...}``.
        """
        return _extraer_metadatos(texto)

    def parsear_tabla(self, texto: str) -> List[Dict[str, Any]]:
        """Fuerza el uso del parser tabular sobre el texto dado.

        Útil en tests para verificar el parser sin pasar por la detección
        automática de formato.

        Wrapper público de :func:`_parsear_tabla`.

        Args:
            texto: Texto tabular.

        Returns:
            Lista de ejercicios estructurados.
        """
        return _parsear_tabla(texto)

    def preprocesar_texto_libre(self, texto: str) -> str:
        """Devuelve el texto preprocesado que se enviará a GLiNER.

        Útil para inspeccionar qué ve exactamente el modelo antes de la
        predicción. Wrapper público de :meth:`_preprocesar_texto_libre`.

        Args:
            texto: Texto libre de entrada.

        Returns:
            Texto normalizado y con expresiones expandidas listo para GLiNER.
        """
        return self._preprocesar_texto_libre(texto)

    # ── Métodos privados ─────────────────────────────────────────────────

    def _preprocesar_texto_libre(self, texto: str) -> str:
        """Preprocesa texto libre para optimizar la extracción de entidades por GLiNER.

        Pasos:
        1. Normalización base (:func:`_normalizar_texto_base`).
        2. Expansión de abreviaturas (:func:`_expandir_abreviaturas`).
        3. Conversión de formato ``NxPESO`` → ``"N repeticiones con PESO kg"``.
        4. Normalización de expresiones ``p/mano`` y ``x/mano`` → ``"por mano"``.
        5. Conversión de segundos en formato ``''`` / ``"`` y ``Ns`` → ``"N segundos"``.
        6. Colapso final de espacios.

        Args:
            texto: Texto libre (OCR de imagen no tabular).

        Returns:
            Texto enriquecido listo para ser consumido por GLiNER.
        """
        texto = _normalizar_texto_base(texto)
        texto = _expandir_abreviaturas(texto)

        # "10 x 80" → "10 repeticiones con 80 kg"
        texto = re.sub(
            r"(\d+)\s*[xX×]\s*([\d.,]+)\b",
            r"\1 repeticiones con \2 kg",
            texto,
            flags=re.IGNORECASE,
        )

        # "p/mano" / "x mano" → "por mano"
        texto = re.sub(r"\bp\s*/\s*mano\b", "por mano", texto, flags=re.IGNORECASE)
        texto = re.sub(r"\bx\s*mano\b", "por mano", texto, flags=re.IGNORECASE)

        # "30''" / "30s" → "30 segundos"
        texto = re.sub(r"(\d+)\s*(?:''|\")", r"\1 segundos", texto)
        texto = re.sub(r"\b(\d+)\s*s\b", r"\1 segundos", texto)

        # SEGMENTACIÓN UNIVERSAL: Separar números de letras pegados (ej: 100kgpress -> 100 kg press)
        texto = re.sub(r"(\d+)([a-z])", r"\1 \2", texto)
        texto = re.sub(r"([a-z])(\d+)", r"\1 \2", texto)

        texto = re.sub(r"\s+", " ", texto).strip()
        return texto

    def _procesar_texto_libre(self, texto: str) -> List[Dict[str, Any]]:
        """Procesa texto libre con el modelo GLiNER y una red de seguridad segmentada.

        Pipeline:
        1. Pre-expansión de abreviaturas para normalizar términos antes de la IA.
        2. Clasificación Zero-shot con GLiNER.
        3. Red de seguridad segmentada: busca ejercicios del catálogo en los
           fragmentos del texto que la IA pudiera haber omitido.

        Args:
            texto: Texto libre de rutina de entrenamiento.

        Returns:
            Lista de entidades detectadas con normalización aplicada.
        """
        self.cargar_modelo()

        # 1. Pre-expansión (ayuda a GLiNER a ver nombres completos)
        texto_expandido = _expandir_abreviaturas(texto)
        texto_limpio = self._preprocesar_texto_libre(texto_expandido)
        
        app_logger.info("Analizando texto libre con GLiNER...")
        entidades = GlinerService._modelo.predict_entities(texto_limpio, self.labels)

        resultados: List[Dict[str, Any]] = []
        for e in entidades:
            score = round(e["score"], 2)
            if score < self.threshold:
                continue

            texto_entidad = e["text"].strip()
            if e["label"] == "ejercicio":
                # Intentamos mejorar el match de GLiNER con el Smart Matcher
                match_smart = _buscar_mejor_coincidencia_semantica(texto_entidad)
                texto_entidad = _normalizar_nombre_ejercicio(match_smart if match_smart else texto_entidad)

            resultados.append({
                "tipo":      e["label"],
                "texto":     texto_entidad,
                "confianza": score,
                "origen":    "gliner",
            })

        # --- RED DE SEGURIDAD SEGMENTADA ---
        # Si hay partes del texto que parecen ejercicios (por Smart Matcher)
        # y GLiNER no los detectó, los rescatamos.
        fragmentos = re.split(r"[\s_/,;]+", texto_expandido)
        for frag in fragmentos:
            frag_limpio = frag.strip()
            if len(frag_limpio) < 3:
                continue
            
            # ¿Este fragmento ya está cubierto por algún ejercicio detectado?
            ya_detectado = False
            for res in resultados:
                if res["tipo"] == "ejercicio" and frag_limpio.lower() in res["texto"].lower():
                    ya_detectado = True
                    break
            
            if not ya_detectado:
                match_seguridad = _buscar_mejor_coincidencia_semantica(frag_limpio)
                if match_seguridad:
                    # Evitar duplicados exactos en resultados
                    nombre_norm = _normalizar_nombre_ejercicio(match_seguridad)
                    if not any(r["texto"] == nombre_norm for r in resultados):
                        resultados.append({
                            "tipo":      "ejercicio",
                            "texto":     nombre_norm,
                            "confianza": 0.5,
                            "origen":    "segmented_safety_net"
                        })

        # --- DEDUPLICACIÓN FINAL ---
        # Ordenamos por longitud de texto (descendente) para conservar el más específico
        resultados.sort(key=lambda x: len(x["texto"]), reverse=True)
        finales: List[Dict[str, Any]] = []
        for res in resultados:
            if res["tipo"] == "ejercicio":
                # Si ya tenemos un ejercicio que contiene a este como substring, lo omitimos
                # Ej: "Dominadas" vs "Dominadas Neutras" -> Nos quedamos con la larga
                if any(res["texto"].lower() in f["texto"].lower() for f in finales if f["tipo"] == "ejercicio"):
                    continue
            finales.append(res)

        return finales

    # ── Métodos de entrada principal ─────────────────────────────────────

    def _enriquecer_nombre_ejercicio(self, nombre: str, rango: str = "") -> str:
        """Normaliza un nombre de ejercicio combinando IA y lógica estructural.

        Pipeline Maestro:
        1. Limpieza de OCR y expansión de abreviaturas.
        2. Búsqueda directa en catálogo (Smart Matcher).
        3. Clasificación Zero-shot con GLiNER si lo anterior es incierto.

        Returns:
            Nombre normalizado en Title Case.
        """
        # 1. Limpieza inicial y expansión rápida
        nombre_limpio = _normalizar_texto_base(nombre)
        if not nombre_limpio:
            return nombre.title()

        # Intentamos expandir antes de buscar estructuralmente, por si es una abrev conocida
        nombre_expandido = _expandir_abreviaturas(nombre_limpio)
        
        # 2. Motor Estructural (Smart Matcher) - Maneja truncamientos extremos
        # Esto resuelve casos como 'elevlatmanc' o 'pmrum' sin IA pesada
        match_semantico = _buscar_mejor_coincidencia_semantica(nombre_expandido)
        if match_semantico:
            return _normalizar_nombre_ejercicio(match_semantico)

        # 3. GLiNER (IA) - Para casos de lenguaje natural ruidoso
        # Primero intentamos con candidatos cercanos
        candidatos = difflib.get_close_matches(
            nombre_limpio, EJERCICIOS_CANONICOS, n=5, cutoff=0.2
        )
        etiquetas = candidatos if candidatos else ["ejercicio"]

        contexto = f"un ejercicio de {nombre_limpio}"
        if rango:
            contexto += f" {rango}"

        try:
            entidades = GlinerService._modelo.predict_entities(contexto, etiquetas)
            if entidades:
                entidades.sort(key=lambda x: x["score"], reverse=True)
                mejor = entidades[0]
                if mejor["score"] >= self.threshold:
                    if mejor["label"] in EJERCICIOS_CANONICOS:
                        return _normalizar_nombre_ejercicio(mejor["label"])
                    return _normalizar_nombre_ejercicio(mejor["text"])
        except Exception as exc:
            app_logger.warning(f"Error en enriquecimiento IA para '{nombre}': {exc}")

        return nombre.title()

    def _enriquecer_ejercicios_tabla(
        self, resultados: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Post-procesa los nombres de ejercicio del parser tabular usando GLiNER.

        Para cada ejercicio cuyo nombre **no es** una clave conocida en
        :data:`ABREVIATURAS` ni un valor de expansión registrado, delega en
        :meth:`_enriquecer_nombre_ejercicio` para que GLiNER intente una
        mejora. Los nombres ya conocidos (abreviaturas expandidas o nombres
        completos del diccionario) se dejan sin modificar.

        Esto mantiene al diccionario de abreviaturas limitado a shorthands
        reales del gym, dejando al modelo de IA la responsabilidad de cubrir
        variantes OCR, truncaciones y términos no catalogados.

        Si se detectan nombres no reconocidos, se carga el modelo GLiNER
        automáticamente.

        Args:
            resultados: Lista de ejercicios del parser tabular.

        Returns:
            La misma lista con nombres potencialmente corregidos por GLiNER.
        """
        enriquecidos: List[Dict[str, Any]] = []
        for ej in resultados:
            nombre_titulo = ej["nombre_ejercicio"]
            nombre_norm = _normalizar_texto_base(nombre_titulo)

            # Determinar si GLiNER debe intervenir:
            # - No es clave en el dict (no es una abreviatura conocida)
            # - No es valor de expansión (no es ya el resultado correcto)
            es_reconocido = (
                nombre_norm in EXPANSOR.abreviaturas
                or nombre_norm in EXPANSOR.valores_conocidos
            )

            if not es_reconocido:
                # Cargar el modelo solo si realmente lo necesitamos (lazy loading)
                self.cargar_modelo()
                
                app_logger.debug(
                    f"Nombre '{nombre_titulo}' no reconocido por ABREVIATURAS. "
                    "Intentando con GLiNER..."
                )
                nombre_corregido = self._enriquecer_nombre_ejercicio(
                    nombre_titulo, ej.get("rango_objetivo", "")
                )
                ej = {**ej, "nombre_ejercicio": nombre_corregido}

            enriquecidos.append(ej)
        return enriquecidos

    def procesar_texto_rutina(self, texto_ocr: str) -> List[Dict[str, Any]]:
        """Punto de entrada principal para extraer datos de una rutina de entrenamiento.

        Detecta automáticamente el formato del texto y delega al parser
        más adecuado:

        - **Texto tabular** → :func:`_parsear_tabla` (sin modelo).
        - **Texto libre** → :meth:`_procesar_texto_libre` (requiere GLiNER).

        Args:
            texto_ocr: Texto extraído por OCR de una imagen de plan de entrenamiento.
                Puede ser tabular (con tabs o columnas alienadas) o texto libre.

        Returns:
            - Si es tabular: lista de ejercicios con la estructura de
              :func:`_parsear_tabla`.
            - Si es libre: lista de entidades con la estructura de
              :meth:`_procesar_texto_libre`.
            - Lista vacía si el texto está vacío o solo contiene espacios.

        Example::

            serv = GlinerService()
            resultado = serv.procesar_texto_rutina(
                "Press Banca\\t7-12\\t10x80\\t9x80"
            )
            # resultado[0]["ejercicio"] == "Press Banca"
        """
        if not texto_ocr or not texto_ocr.strip():
            return []

        if _es_tabla(texto_ocr):
            app_logger.info("Formato tabular detectado. Usando parser directo.")
            resultado = _parsear_tabla(texto_ocr)
            # Enriquecer nombres con GLiNER (la carga es automática si se necesita)
            return self._enriquecer_ejercicios_tabla(resultado)

        return self._procesar_texto_libre(texto_ocr)

    def procesar_texto_rutina_debug(self, texto_ocr: str) -> Dict[str, Any]:
        """Versión de diagnóstico de :meth:`procesar_texto_rutina` con trazabilidad completa.

        Devuelve el resultado de la extracción junto con información
        intermedia del procesamiento: texto expandido, modo detectado,
        metadatos encontrados y texto preprocesado para GLiNER.

        No sustituye al método principal; lo complementa para depuración
        y testing.

        Args:
            texto_ocr: Texto extraído por OCR (tabular o libre).

        Returns:
            Diccionario con las claves:

            - ``"entrada_original"`` (str): El texto tal como se recibió.
            - ``"modo_detectado"`` (str | None): ``"tabla"``, ``"gliner"`` o ``None``.
            - ``"es_tabla"`` (bool): Resultado de :func:`_es_tabla`.
            - ``"metadatos"`` (dict): Resultado de :func:`_extraer_metadatos`.
            - ``"texto_expandido"`` (str): Texto tras expansión de abreviaturas.
            - ``"texto_preprocesado_gliner"`` (str): Texto listo para GLiNER.
            - ``"resultado"`` (list): Mismo resultado que :meth:`procesar_texto_rutina`.

        Example::

            info = serv.procesar_texto_rutina_debug("Curl bien 3x15")
            print(info["modo_detectado"])          # "gliner"
            print(info["texto_expandido"])         # "curl predicador 3x15"
        """
        if not texto_ocr or not texto_ocr.strip():
            return {
                "entrada_original":          texto_ocr,
                "modo_detectado":            None,
                "es_tabla":                  False,
                "metadatos":                 {"mesociclo": None, "semana": None, "sesion": None},
                "texto_expandido":           "",
                "texto_preprocesado_gliner": "",
                "resultado":                 [],
            }

        es_tabla = _es_tabla(texto_ocr)
        metadatos = _extraer_metadatos(texto_ocr)
        texto_expandido = _expandir_abreviaturas(texto_ocr)
        texto_preprocesado = self._preprocesar_texto_libre(texto_ocr)

        if es_tabla:
            resultado = _parsear_tabla(texto_ocr)
            # Enriquecer con GLiNER (la carga es automática si se necesita)
            resultado = self._enriquecer_ejercicios_tabla(resultado)
            modo = "tabla"
        else:
            resultado = self._procesar_texto_libre(texto_ocr)
            modo = "gliner"

        return {
            "entrada_original":          texto_ocr,
            "modo_detectado":            modo,
            "es_tabla":                  es_tabla,
            "metadatos":                 metadatos,
            "texto_expandido":           texto_expandido,
            "texto_preprocesado_gliner": texto_preprocesado,
            "resultado":                 resultado,
        }