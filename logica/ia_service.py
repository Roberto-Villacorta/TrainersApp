import os
import re
from gliner import GLiNER
from utils.logger import app_logger

# Configurar para que todos los modelos descargados vayan a la carpeta local 'modelos_ia'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "modelos_ia")
os.environ["HF_HOME"] = MODEL_DIR

class GlinerService:
    _modelo = None

    def __init__(self):
        """Inicializa el modelo GLiNER de forma perezosa (Lazy Load) para no bloquear el inicio de la app."""
        # Balance entre labels cortos y descriptivos para maximizar precision
        self.labels = [
            "ejercicio",
            "series",
            "repeticiones",
            "peso en kg o kg",
            "descanso",
        ]
        self.model_name = "urchade/gliner_multi-v2.1"  # Modelo multilenguaje robusto

    def cargar_modelo(self):
        if GlinerService._modelo is None:
            app_logger.info(f"Cargando modelo GLiNER ({self.model_name}) en memoria. Esto puede tardar la primera vez si se está descargando en {MODEL_DIR}...")
            try:
                # Al cargar el modelo, los binarios se alojarán automáticamente en 'modelos_ia' por la variable HF_HOME
                GlinerService._modelo = GLiNER.from_pretrained(self.model_name)
                app_logger.info("Modelo GLiNER cargado correctamente.")
            except Exception as e:
                app_logger.error(f"Error cargando GLiNER: {e}")
                raise e

    def procesar_texto_rutina(self, texto_ocr: str):
        """
        Toma texto caótico (salida de un OCR) y devuelve una lista estructurada
        de parámetros de fitness (ejercicio, series, reps...).
        """
        self.cargar_modelo()
        
        # Preprocesado: normalizar texto caotico de OCR
        texto_limpio = texto_ocr.lower()
        # Reemplazos con word boundaries para no alterar subpalabras
        texto_limpio = re.sub(r'\bdsc\b', 'descanso', texto_limpio)
        texto_limpio = re.sub(r'\bdesc\b', 'descanso', texto_limpio)
        texto_limpio = re.sub(r'\breps\b', 'repeticiones', texto_limpio)
        texto_limpio = re.sub(r'\brep\b', 'repeticiones', texto_limpio)
        texto_limpio = re.sub(r'(\d+)x(\d)', r'\1 series de \2', texto_limpio)  # "4x10" -> "4 series de 10"
        texto_limpio = re.sub(r'\bp/mano\b', 'por mano', texto_limpio)

        app_logger.info("Analizando texto OCR con GLiNER...")
        entidades = GlinerService._modelo.predict_entities(texto_limpio, self.labels)
        
        # Filtrado básico por score o empaquetado de resultados
        resultados_limpios = []
        for entity in entidades:
            if entity["score"] > 0.4:  # Umbral de confianza
                resultados_limpios.append({
                    "tipo": entity["label"],
                    "texto": entity["text"],
                    "confianza": round(entity["score"], 2)
                })
                
        return resultados_limpios
