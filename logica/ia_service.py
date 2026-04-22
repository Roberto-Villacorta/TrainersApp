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
from typing import List, Dict, Any, Optional

from gliner import GLiNER
from utils.logger import app_logger

# ---------------------------------------------------------------------------
# Configuración de rutas y constantes globales
# ---------------------------------------------------------------------------

#: Directorio raíz del proyecto (un nivel por encima de /logica).
BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Directorio local donde se almacenan los modelos HuggingFace descargados.
MODEL_DIR: str = os.path.join(BASE_DIR, "modelos_ia")

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

def _quitar_acentos(texto: str) -> str:
    """Elimina diacríticos (acentos, tildes, diéresis) de una cadena Unicode.

    Utiliza la descomposición NFD para separar el carácter base de sus marcas
    de combinación (categoría Unicode "Mn") y luego las descarta.

    Args:
        texto: Cadena de texto con posibles caracteres acentuados.

    Returns:
        La misma cadena sin marcas diacríticas.

    Examples:
        >>> _quitar_acentos("Músculo")
        'Musculo'
        >>> _quitar_acentos("büro")
        'buro'
    """
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def _normalizar_texto_base(texto: str) -> str:
    """Normaliza un texto para comparaciones y búsquedas robustas.

    Realiza las siguientes transformaciones en orden:
    - Conversión a minúsculas.
    - Eliminación de acentos mediante :func:`_quitar_acentos`.
    - Reemplazo de guiones tipográficos y barras por sus equivalentes ASCII.
    - Colapso de espacios/tabuladores múltiples en uno solo.
    - Eliminación de espacios alrededor de ``.``, ``-`` y ``/``.

    Args:
        texto: Texto de entrada, puede ser ``None`` o vacío.

    Returns:
        Texto normalizado y sin espacios sobrantes.
        Devuelve ``""`` si la entrada es ``None`` o vacía.

    Examples:
        >>> _normalizar_texto_base("Press  Banca / Plano")
        'press banca/plano'
        >>> _normalizar_texto_base(None)
        ''
    """
    if not texto:
        return ""

    texto = texto.lower()
    texto = _quitar_acentos(texto)

    texto = texto.replace("_", " ")
    # Limpieza de ruidos de unión comunes en OCR (puntos, guiones, barras bajas)
    # Reemplazamos por espacios si están entre letras para segmentar correctamente
    texto = re.sub(r"(?<=[a-z])[\._\-](?=[a-z])", " ", texto)
    
    texto = texto.replace("–", "-")   # guión en dash
    texto = texto.replace("—", "-")   # guión largo em dash
    texto = texto.replace("/", " / ")

    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\s*\.\s*", ".", texto)
    texto = re.sub(r"\s*-\s*", "-", texto)
    texto = re.sub(r"\s*/\s*", "/", texto)

    return texto.strip()


def _normalizar_clave_abrev(clave: str) -> str:
    """Normaliza una clave del diccionario de abreviaturas para tokenización flexible.

    Extiende :func:`_normalizar_texto_base` eliminando también los separadores
    ``.``, ``-`` y ``/`` para obtener tokens sólo de palabras separadas por
    espacios, facilitando la construcción de patrones regex flexibles.

    Args:
        clave: Clave de abreviatura (posiblemente con puntos, guiones, etc.).

    Returns:
        Clave normalizada con separadores eliminados y solo espacios simples.

    Examples:
        >>> _normalizar_clave_abrev("ext. tric")
        'ext tric'
        >>> _normalizar_clave_abrev("p. incl")
        'p incl'
    """
    clave = _normalizar_texto_base(clave)
    clave = clave.replace(".", " ")
    clave = clave.replace("-", " ")
    clave = clave.replace("/", " ")
    clave = re.sub(r"\s+", " ", clave).strip()
    return clave


# ─────────────────────────────────────────────────────────────────
# Catálogo de Ejercicios Canónicos (Memoria de la IA)
# ─────────────────────────────────────────────────────────────────

#: Lista exhaustiva de nombres de ejercicios normalizados.
#: Se utiliza como etiquetas (labels) para GLiNER en el paso de
#: Zero-shot Classification para normalización inteligente.
EJERCICIOS_CANONICOS: List[str] = [
    # Pecho
    "press plano", "press inclinado", "press declinado", "press banca",
    "press con mancuernas", "aperturas", "aperturas con mancuernas",
    "cruce en polea", "fondos", "peck deck", "press hammer",
    # Espalda
    "dominadas", "dominadas supinas", "dominadas pronas", "dominadas neutras",
    "jalon al pecho", "jalon tras nuca", "remo", "remo con mancuernas",
    "remo con barra", "remo en polea", "remo en t", "pullover", "tiron dominadas",
    "remo horizontal", "remo pendlay", "remo unipolar", "lumbares",
    "tiron al pecho", "tiron polea", "tiron", "remo", "jalon",
    # Hombro
    "elevaciones laterales", "elevaciones frontales", "elevaciones posteriores",
    "vuelos laterales", "vuelos frontales", "vuelos posteriores",
    "pajaro", "face pull", "press hombro", "press militar", "press arnold",
    "encogimientos", "press tras nuca", "upright row", "jalon en polea",
    # Pierna
    "sentadilla", "sentadilla trasera", "sentadilla frontal", "sentadilla bulgara",
    "zancadas", "prensa", "extension cuadriceps", "curl femoral",
    "curl femoral tumbado", "curl femoral sentado", "hip thrust", "puente gluteo",
    "abduccion", "aduccion", "gemelos", "elevaciones de gemelos",
    "peso muerto", "peso muerto convencional", "peso muerto sumo",
    "peso muerto rumano", "hack squat", "leg press", "step up", "glute bridge",
    "sentadilla hack", "zancada", "elevacion de talones",
    # Brazos
    "curl", "curl con barra", "curl con barra z", "curl con mancuernas",
    "curl martillo", "martillo continuo", "curl predicador", "curl concentrado",
    "curl bayesian", "extensiones triceps", "extensiones triceps cuerda",
    "extensiones triceps polea", "extensiones trasnuca", "press cerrado",
    "patada triceps", "dips", "skullcrushers", "frances", "curl araña",
    "press frances", "jalon de triceps",
    # Core / Cardio / Otros
    "abdominales", "crunch", "plancha", "elevaciones de piernas", "ab wheel",
    "cinta", "bicicleta", "remo ergometro", "descanso", "burpees", "jumping jacks"
]


# ─────────────────────────────────────────────────────────────────
# DICCIONARIO DE ABREVIATURAS
# ─────────────────────────────────────────────────────────────────

#: Diccionario que mapea abreviaturas y formas coloquiales de ejercicios
#: a sus nombres completos normalizados.
#:
#: Las claves se normalizan automáticamente al construir :class:`ExpansorAbreviaturas`,
#: por lo que no es necesario que sean exactas en cuanto a tildes o mayúsculas.
#: Sin embargo, **no deben tener espacios sobrantes** en los extremos.
ABREVIATURAS: Dict[str, str] = {
    # ── Press / Pecho ────────────────────────────────────────────────────
    "press inc":       "press inclinado",
    "p inc":           "press inclinado",
    "p incl":          "press inclinado",
    "ban inc":         "press inclinado",
    "ban incl":        "press inclinado",
    "p plano":         "press plano",
    "p plan":          "press plano",
    "p pla":           "press plano",
    "p. plan":         "press plano",
    "p. pla":          "press plano",
    "p. plano":        "press plano",
    "press plan":      "press plano",
    "press pla":       "press plano",
    "press plano":     "press plano",
    "p decl":          "press declinado",
    "p. decl":         "press declinado",
    "press decl":      "press declinado",
    "press banca":     "press banca",
    "p banca":         "press banca",
    "pb":              "press banca",
    "press manc":      "press con mancuernas",
    "p manc":          "press con mancuernas",
    "apert":           "aperturas",
    "apert manc":      "aperturas con mancuernas",
    "cruce polea":     "cruce en polea",
    "fond":            "fondos",
    "fondo":           "fondos",
    "fondos":          "fondos",

    # ── Hombro ───────────────────────────────────────────────────────────
    "elev lat":        "elevaciones laterales",
    "elev. lat":       "elevaciones laterales",
    "elev lateral":    "elevaciones laterales",
    "elev laterales":  "elevaciones laterales",
    "elev front":      "elevaciones frontales",
    "elev. front":     "elevaciones frontales",
    "elev post":       "elevaciones posteriores",
    "elev. post":      "elevaciones posteriores",
    "vuel lat":        "elevaciones laterales",
    "vuelos lat":      "elevaciones laterales",
    "vuel":            "elevaciones laterales",
    "pajaro":          "pajaro",
    "paj":             "pajaro",
    "face pull":       "face pull",
    "facepull":        "face pull",
    "fp":              "face pull",
    "fce pull":        "face pull",
    "press homb":      "press hombro",
    "p homb":          "press hombro",
    "ph":              "press hombro",
    "press mil":       "press militar",
    "press mill":      "press militar",
    "press millo":     "press y martillo",
    "militar":         "press militar",
    "arnold":          "press arnold",
    "p arnold":        "press arnold",

    # ── Espalda / Tirón ──────────────────────────────────────────────────
    "dom":             "dominadas",
    "domin":           "dominadas",
    "dominadas":       "dominadas",
    "dom sup":         "dominadas supinas",
    "dom pron":        "dominadas pronas",
    "dom neut":        "dominadas neutras",
    "t don":           "tiron dominadas",
    "jal":             "jalon",
    "jalon":           "jalon",
    "jal pech":        "jalon al pecho",
    "jal pecho":       "jalon al pecho",
    "j pecho":         "jalon al pecho",
    "jal tras":        "jalon tras nuca",
    "remo":            "remo",
    "remo manc":       "remo con mancuernas",
    "remo barra":      "remo con barra",
    "remo polea":      "remo en polea",
    "r polea":         "remo en polea",
    "remo t":          "remo en t",
    "rm t":            "remo en t",
    "pullover":        "pullover",
    "pull over":       "pullover",

    # ── Bíceps ───────────────────────────────────────────────────────────
    "curl":            "curl",
    "curl barra":      "curl con barra",
    "curl z":          "curl con barra z",
    "curl manc":       "curl con mancuernas",
    "curl alt":        "curl alterno",
    "curl mart":       "curl martillo",
    "mart":            "curl martillo",
    "mat cont":        "martillo continuo",
    "curl predic":     "curl predicador",
    "curl pred":       "curl predicador",
    "curl bien":       "curl predicador",
    "curl conc":       "curl concentrado",
    "curl bayes":      "curl bayesian",
    "bayes":           "curl bayesian",
    "cur b z":         "curl con barra z",

    # ── Tríceps ──────────────────────────────────────────────────────────
    "ext tric":        "extensiones triceps",
    "ext. tric":       "extensiones triceps",
    "ext triceps":     "extensiones triceps",
    "ext tri":         "extensiones triceps",
    "ext cuerda":      "extensiones triceps cuerda",
    "ext polea":       "extensiones triceps polea",
    "ext tras":        "extensiones trasnuca",
    "ext. tras":       "extensiones trasnuca",
    "exten tras":      "extensiones trasnuca",
    "exten. tras":     "extensiones trasnuca",
    "press cerr":      "press cerrado",
    "kckton":          "patada triceps",
    "kickback":        "patada triceps",
    "pat tr":          "patada triceps",

    # ── Pierna ───────────────────────────────────────────────────────────
    "sent":            "sentadilla",
    "sentadll":        "sentadilla",
    "sentadila":       "sentadilla",
    "sentadilla":      "sentadilla",
    "sent tras":       "sentadilla trasera",
    "sent front":      "sentadilla frontal",
    "sent bulg":       "sentadilla bulgara",
    "bulg":            "sentadilla bulgara",
    "zanc":            "zancadas",
    "zanc cam":        "zancadas caminando",
    "prensa":          "prensa",
    "prens":           "prensa",
    "ext cuad":        "extension cuadriceps",
    "ext quad":        "extension cuadriceps",
    "curl fem":        "curl femoral",
    "curl fem tumb":   "curl femoral tumbado",
    "curl fem sent":   "curl femoral sentado",
    "hip thrust":      "hip thrust",
    "hip thr":         "hip thrust",
    "ht":              "hip thrust",
    "puente gl":       "puente gluteo",
    "abductor":        "abduccion",
    "abduct":          "abduccion",
    "aductor":         "aduccion",
    "adduct":          "aduccion",
    "gom":             "gemelos",
    "gem":             "gemelos",
    "gemelos":         "gemelos",
    "elev gem":        "elevaciones de gemelos",

    # ── Bisagra / Posterior ──────────────────────────────────────────────
    "pm":              "peso muerto",
    "pes":             "peso muerto",
    "peso m":          "peso muerto",
    "pm conv":         "peso muerto convencional",
    "pm sumo":         "peso muerto sumo",
    "pm rum":          "peso muerto rumano",
    "pm rdl":          "peso muerto rumano",
    "rdl":             "peso muerto rumano",
    "b dias":          "good morning",
    "buenos dias":     "good morning",
    "gm":              "good morning",

    # ── Core ─────────────────────────────────────────────────────────────
    "abs":             "abdominales",
    "crunch":          "crunch",
    "plancha":         "plancha",
    "plank":           "plancha",
    "elev piernas":    "elevaciones de piernas",
    "leg raise":       "elevaciones de piernas",
    "rueda":           "ab wheel",
    "ab wheel":        "ab wheel",

    # ── Cardio / Genéricos ───────────────────────────────────────────────
    "cinta":           "cinta",
    "bici":            "bicicleta",
    "remo erg":        "remo ergometro",
    "dsc":             "descanso",
    "desc":            "descanso",
    "reps":            "repeticiones",
    "rep":             "repeticiones",
    "rps":             "repeticiones",
    "ser":             "series",
    "sers":            "series",
    "kg":              "kg",
    "kms":             "kilometros",
    "km":              "kilometros",
    "seg":             "segundos",
    "s":               "segundos",
    "min":             "minutos",

    # ── Legacy / Otros ───────────────────────────────────────────────────
    "ext acl":         "extension acl",
    "pres millo":      "press y martillo",
    "vuelalat":        "elevaciones laterales",
    "ban inc":         "press inclinado",
    "ban incl":        "press inclinado",
    "ban pla":         "press plano",
}


# ─────────────────────────────────────────────────────────────────
# EXPANSOR DE ABREVIATURAS
# ─────────────────────────────────────────────────────────────────

class ExpansorAbreviaturas:
    """Motor de expansión de abreviaturas basado en regex.

    Convierte abreviaturas y nombres coloquiales de ejercicios a su forma
    completa normalizada. Los patrones se compilan una sola vez al instanciar
    la clase y se ordenan de mayor a menor longitud para evitar conflictos
    de solapamiento (p.ej. ``"curl fem tumb"`` debe expandirse antes que
    ``"curl fem"``).

    Args:
        abreviaturas: Diccionario ``{abreviatura: expansion}``.
            Las claves se normalizan internamente; no es necesario que
            estén en minúsculas ni sin tildes.

    Attributes:
        abreviaturas_originales (Dict[str, str]): El diccionario tal como se pasó.
        abreviaturas (Dict[str, str]): Diccionario con claves normalizadas.
        patrones (List[tuple]): Lista de ``(regex_compilado, expansion)``
            ordenada por longitud descendente.

    Example::

        expansor = ExpansorAbreviaturas(ABREVIATURAS)
        print(expansor.expandir("Elev lat 3x12"))
        # → "elevaciones laterales 3x12"
    """

    def __init__(self, abreviaturas: Dict[str, str]) -> None:
        self.abreviaturas_originales = abreviaturas
        self.abreviaturas = self._normalizar_diccionario(abreviaturas)
        #: Conjunto de expansiones conocidas para lookup O(1).
        #: Incluye los valores del dict y el catálogo canónico completo.
        self.valores_conocidos: set = set(self.abreviaturas.values()) | set(
            _normalizar_texto_base(e) for e in EJERCICIOS_CANONICOS
        )
        self.patrones = self._compilar_patrones()

    def _normalizar_diccionario(
        self, abreviaturas: Dict[str, str]
    ) -> Dict[str, str]:
        """Normaliza todas las claves y valores del diccionario de entrada.

        Args:
            abreviaturas: Diccionario original.

        Returns:
            Nuevo diccionario con claves procesadas por
            :func:`_normalizar_clave_abrev` y valores por
            :func:`_normalizar_texto_base`. Se descartan entradas con
            clave vacía tras la normalización.
        """
        normalizadas: Dict[str, str] = {}
        for clave, valor in abreviaturas.items():
            k = _normalizar_clave_abrev(clave)
            v = _normalizar_texto_base(valor)
            if k:
                normalizadas[k] = v
        return normalizadas

    def _crear_regex_flexible(self, clave: str) -> re.Pattern:
        """Construye un patrón regex que tolera separadores entre tokens.

        Cada token de la clave se separa con un patrón que acepta
        espacios, puntos, guiones y barras (``[\\s\\.\\-\\/]*``), lo que
        permite reconocer ``"ext.tric"``, ``"ext-tric"`` y ``"ext tric"``
        con el mismo patrón.

        Los límites de palabra (``(?<!\\w)`` / ``(?!\\w)``) evitan
        coincidencias parciales dentro de otra palabra.

        Args:
            clave: Clave normalizada (solo palabras separadas por espacios).

        Returns:
            Patrón regex compilado, insensible a mayúsculas.
        """
        tokens = [re.escape(t) for t in clave.split()]
        separador = r"[\s\.\-\/_]*"
        patron = separador.join(tokens)
        regex = rf"(?<!\w){patron}(?!\w)"
        return re.compile(regex, flags=re.IGNORECASE)

    def _compilar_patrones(self) -> List[tuple]:
        """Compila todos los patrones regex ordenados por longitud descendente.

        El orden garantiza que las abreviaturas más largas se apliquen
        primero, evitando que una clave corta consuma parte de una clave
        más larga.

        Returns:
            Lista de tuplas ``(re.Pattern, str)`` lista para usarse en
            :meth:`expandir`.
        """
        items = sorted(
            self.abreviaturas.items(),
            key=lambda x: len(x[0]),
            reverse=True,
        )
        return [
            (self._crear_regex_flexible(clave), expansion)
            for clave, expansion in items
        ]

    def expandir(self, texto: str) -> str:
        """Expande todas las abreviaturas reconocidas en el texto de entrada.

        El proceso es:
        1. Normalizar el texto con :func:`_normalizar_texto_base`.
        2. Aplicar cada patrón en orden (mayor → menor longitud).
        3. Colapsar espacios múltiples resultantes.

        Si una iteración completa no produce cambios, se detiene antes de
        terminar el bucle (early-exit) para evitar re-expansiones.

        Args:
            texto: Texto de entrada con posibles abreviaturas.

        Returns:
            Texto con abreviaturas expandidas. Devuelve ``""`` si la
            entrada es vacía o ``None``.

        Example::

            expansor.expandir("curl mart 3x12")
            # → "curl martillo 3x12"
        """
        if not texto:
            return ""

        texto_norm = _normalizar_texto_base(texto)

        for patron, expansion in self.patrones:
            anterior = texto_norm
            texto_norm = patron.sub(expansion, texto_norm)

        texto_norm = re.sub(r"\s+", " ", texto_norm).strip()
        return texto_norm

    def diagnosticar(self, texto: str) -> Dict[str, Any]:
        """Devuelve información detallada del proceso de expansión para debug/test.

        A diferencia de :meth:`expandir`, este método registra cada
        sustitución realizada indicando el match original, su posición y
        la expansión aplicada.

        Args:
            texto: Texto de entrada a analizar.

        Returns:
            Diccionario con las claves:

            - ``"original"`` (str): Texto de entrada sin modificar.
            - ``"normalizado"`` (str): Texto tras normalización base.
            - ``"expandido"`` (str): Texto final con abreviaturas expandidas.
            - ``"abreviaturas_detectadas"`` (List[dict]): Lista de dicts con
              ``"match"``, ``"span"`` y ``"expansion"`` para cada sustitución.

        Example::

            info = expansor.diagnosticar("Elev lat 20x13,75")
            # info["expandido"] → "elevaciones laterales 20x13.75"
            # info["abreviaturas_detectadas"] → [{"match": "elev lat", ...}]
        """
        original = texto or ""
        normalizado = _normalizar_texto_base(original)
        expandido = normalizado
        matches: List[Dict[str, Any]] = []

        for patron, expansion in self.patrones:
            encontrados = list(patron.finditer(expandido))
            if encontrados:
                for m in encontrados:
                    matches.append({
                        "match": m.group(0),
                        "span": m.span(),
                        "expansion": expansion,
                    })
                expandido = patron.sub(expansion, expandido)

        expandido = re.sub(r"\s+", " ", expandido).strip()

        return {
            "original": original,
            "normalizado": normalizado,
            "expandido": expandido,
            "abreviaturas_detectadas": matches,
        }


#: Instancia global del expansor, construida una sola vez con el diccionario
#: :data:`ABREVIATURAS`. Se reutiliza en todas las llamadas del módulo.
EXPANSOR: ExpansorAbreviaturas = ExpansorAbreviaturas(ABREVIATURAS)


def _expandir_abreviaturas(texto: str) -> str:
    """Wrapper de módulo que delega en la instancia global :data:`EXPANSOR`.

    Args:
        texto: Texto con posibles abreviaturas de ejercicios.

    Returns:
        Texto con abreviaturas expandidas, o ``""`` si la entrada es vacía.
    """
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

        resultados.append({
            "ejercicio":      ejercicio,
            "rango_objetivo": rango,
            "series":         series,
            "origen":         "tabla",
            "mesociclo":      meta["mesociclo"],
            "semana":         meta["semana"],
            "sesion":         meta["sesion"],
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
                GlinerService._modelo = GLiNER.from_pretrained(self.model_name)
                app_logger.info("Modelo GLiNER cargado correctamente.")
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
            nombre_titulo = ej["ejercicio"]
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
                ej = {**ej, "ejercicio": nombre_corregido}

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