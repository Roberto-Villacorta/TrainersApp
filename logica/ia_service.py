import os
import re
from gliner import GLiNER
from utils.logger import app_logger

# Configurar para que todos los modelos descargados vayan a la carpeta local 'modelos_ia'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "modelos_ia")
os.environ["HF_HOME"] = MODEL_DIR

# ─────────────────────────────────────────────────────────────────
# Diccionario de abreviaturas comunes de gimnasio
# Extend este diccionario libremente con los términos de tu sistema
# ─────────────────────────────────────────────────────────────────
ABREVIATURAS = {
    # Ejercicios con punto o espacio (se reemplazan como cadena literal)
    "p. incl":    "press inclinado",
    "p. plan":    "press plano",
    "p. plano":   "press plano",
    "elev. lat":  "elevaciones laterales",
    "elev lat":   "elevaciones laterales",
    "curl predic":"curl predicador",
    "curl bien":  "curl predicador",
    "exten. tras":"extensiones trasnuca",
    "ext. tras":  "extensiones trasnuca",
    "ext. tric":  "extensiones triceps",
    "mat cont":   "martillo continuo",
    "t don":      "tiron dominadas",
    "ext acl":    "extension acl",
    "pres millo": "press y martillo",
    # Ejercicios con word-boundary
    "dom":    "dominadas",
    "pajaro": "pajaro",
    "sent":   "sentadilla",
    "sentadll":"sentadilla",
    "gom":    "gemelos",
    "gem":    "gemelos",
    "pm":     "peso muerto",
    "pes":    "peso muerto",
    "remo":   "remo",
    "kckton": "patada triceps",
    # Genéricos
    "dsc":  "descanso",
    "desc": "descanso",
    "reps": "repeticiones",
    "rep":  "repeticiones",
    "ser":  "series",
}

def _expandir_abreviaturas(texto: str) -> str:
    """Expande abreviaturas a términos completos para mejorar comprensión del modelo."""
    for abrev, completo in ABREVIATURAS.items():
        if "." in abrev or " " in abrev:
            texto = texto.replace(abrev, completo)
        else:
            texto = re.sub(fr'\b{re.escape(abrev)}\b', completo, texto)
    return texto

def _es_tabla(texto: str) -> bool:
    """Detecta si el texto tiene formato tabular (contiene tabs o columnas separadas por espacios múltiples)."""
    lineas = [l for l in texto.strip().splitlines() if l.strip()]
    if len(lineas) < 2:
        return False
    # Si más de la mitad de las líneas contienen tabuladores, es tabla
    con_tab = sum(1 for l in lineas if '\t' in l)
    return con_tab >= len(lineas) // 2

def _parsear_tabla(texto: str) -> list[dict]:
    """
    Parsea texto en formato tabla (separado por tabuladores).
    Formato esperado:
        Ejercicio  Rango   Serie1   Serie2   Serie3
        Dom        30      5 x 30   4 x 30   4 x 30
    
    Devuelve una lista de dicts con ejercicio, rango y lista de series {reps, peso}.
    """
    lineas = [l for l in texto.strip().splitlines() if l.strip()]
    resultados = []

    # Saltar la cabecera (primera línea)
    datos = lineas[1:]

    # Regex para capturar "REP x PESO" o "REP X PESO" o "REP x PESO,5"
    patron_serie = re.compile(r'(\d+)\s*[xX]\s*([\d.,]+)', re.IGNORECASE)

    for linea in datos:
        columnas = re.split(r'\t+', linea.strip())
        if not columnas:
            continue

        nombre_raw = columnas[0].strip()
        if not nombre_raw:
            continue

        nombre_expandido = _expandir_abreviaturas(nombre_raw.lower()).strip().title()
        rango = columnas[1].strip() if len(columnas) > 1 else "—"

        series = []
        for celda in columnas[2:]:
            celda = celda.strip()
            match = patron_serie.search(celda)
            if match:
                reps = int(match.group(1))
                peso_str = match.group(2).replace(",", ".")
                peso = float(peso_str)
                series.append({"reps": reps, "peso_kg": peso})

        resultados.append({
            "ejercicio": nombre_expandido,
            "rango_objetivo": rango,
            "series": series,
            "origen": "tabla"
        })

    return resultados

class GlinerService:
    _modelo = None

    def __init__(self):
        """Inicializa el modelo GLiNER de forma perezosa (Lazy Load) para no bloquear el inicio de la app."""
        self.labels = [
            "ejercicio",
            "series",
            "repeticiones",
            "peso en kg",
            "descanso",
        ]
        self.model_name = "urchade/gliner_multi-v2.1"

    def cargar_modelo(self):
        if GlinerService._modelo is None:
            app_logger.info(f"Cargando modelo GLiNER ({self.model_name}) en {MODEL_DIR}...")
            try:
                GlinerService._modelo = GLiNER.from_pretrained(self.model_name)
                app_logger.info("Modelo GLiNER cargado correctamente.")
            except Exception as e:
                app_logger.error(f"Error cargando GLiNER: {e}")
                raise e

    def _procesar_texto_libre(self, texto: str) -> list[dict]:
        """Usa GLiNER para extraer entidades de texto no estructurado."""
        self.cargar_modelo()

        texto_limpio = texto.lower()
        texto_limpio = _expandir_abreviaturas(texto_limpio)
        # Normalizar "NxM" -> "N repeticiones con M kg"
        texto_limpio = re.sub(r'(\d+)\s*[xX]\s*([\d.,]+)', r'\1 repeticiones con \2 kg', texto_limpio)
        texto_limpio = re.sub(r'\bp/mano\b', 'por mano', texto_limpio)

        app_logger.info("Analizando texto libre con GLiNER...")
        entidades = GlinerService._modelo.predict_entities(texto_limpio, self.labels)

        return [
            {
                "tipo": e["label"],
                "texto": e["text"],
                "confianza": round(e["score"], 2),
                "origen": "gliner"
            }
            for e in entidades if e["score"] > 0.4
        ]

    def procesar_texto_rutina(self, texto_ocr: str):
        """
        Punto de entrada principal.
        - Si el texto es tabular: lo parsea directamente (precisión 100%).
        - Si es texto libre: usa GLiNER para NER.
        Devuelve siempre una lista de dicts con los datos extraídos.
        """
        if _es_tabla(texto_ocr):
            app_logger.info("Formato tabular detectado. Usando parser directo.")
            return _parsear_tabla(texto_ocr)
        else:
            return self._procesar_texto_libre(texto_ocr)
