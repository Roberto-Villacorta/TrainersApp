import os
from utils.logger import app_logger

class IAFormService:
    """
    Servicio para interpretar las respuestas de texto libre de un formulario 
    utilizando el modelo local GLiNER (Zero-shot NER).
    Reutiliza el singleton de GlinerService para evitar recargar el modelo en cada uso.
    """
    _model = None  # Singleton compartido

    def __init__(self):
        if IAFormService._model is None:
            try:
                from logica.ia_service import GlinerService
                from logica.ia_service import MODEL_NAME, MODEL_DIR
                os.environ["HF_HOME"] = MODEL_DIR
                # Reutilizamos el singleton de GlinerService si ya está cargado,
                # o lo creamos con carga diferida (lazy) para no bloquear el arranque
                svc = GlinerService(cargar_modelo_al_inicio=False)
                # Forzamos la carga ahora que estamos en el contexto del formulario
                if GlinerService._modelo is None:
                    GlinerService(cargar_modelo_al_inicio=True)
                IAFormService._model = GlinerService._modelo
                app_logger.info("Modelo GLiNER vinculado correctamente para análisis de formularios.")
            except Exception as e:
                app_logger.error(f"Error cargando GLiNER en IAFormService: {e}")
                IAFormService._model = None

    def analizar_formulario(self, respuestas: dict) -> dict:
        """
        Analiza las respuestas de texto libre del formulario para extraer entidades 
        y generar métricas de alerta heurísticas.
        """
        if not IAFormService._model:
            return self._generar_vacio()

        # Concatenar respuestas relevantes de texto libre
        textos = [
            respuestas.get("comentario_satisfaccion", ""),
            respuestas.get("lleva_mejor", ""),
            respuestas.get("cuesta_mas", ""),
            respuestas.get("comentario_saciedad", ""),
            respuestas.get("dudas", "")
        ]
        texto_completo = ". ".join([str(t) for t in textos if t])
        
        if not texto_completo.strip():
            return self._generar_vacio()

        labels = ["dolor", "lesión", "cansancio", "fatiga", "estrés", "agobio", "sueño", "mejora", "hambre", "ansiedad"]
        entities = IAFormService._model.predict_entities(texto_completo, labels, threshold=0.3)
        
        alertas = {
            "alerta_fatiga": 1,
            "alerta_dolor": 1,
            "alerta_sueno": 1,
            "alerta_estres": 1,
            "alerta_rendimiento": 1
        }
        
        resumen_entidades = []
        
        for ent in entities:
            label = ent["label"].lower()
            resumen_entidades.append(f"{ent['text']} ({label})")
            
            if label in ["dolor", "lesión"]:
                alertas["alerta_dolor"] = min(5, alertas["alerta_dolor"] + 2)
            elif label in ["cansancio", "fatiga"]:
                alertas["alerta_fatiga"] = min(5, alertas["alerta_fatiga"] + 2)
            elif label in ["estrés", "agobio", "ansiedad"]:
                alertas["alerta_estres"] = min(5, alertas["alerta_estres"] + 2)
            elif label in ["sueño"]:
                alertas["alerta_sueno"] = min(5, alertas["alerta_sueno"] + 2)
                
        # Si se detectaron cosas negativas, subimos el riesgo de rendimiento
        if alertas["alerta_fatiga"] > 2 or alertas["alerta_dolor"] > 2:
            alertas["alerta_rendimiento"] = min(5, alertas["alerta_rendimiento"] + 1)
            
        resumen = "Análisis IA (GLiNER): No se detectaron alertas significativas."
        if resumen_entidades:
            resumen = "IA detectó conceptos clave: " + ", ".join(set(resumen_entidades))
            
        return {
            "resumen": resumen,
            "alertas": alertas
        }

    def _generar_vacio(self):
        return {
            "resumen": "Análisis IA no disponible o texto insuficiente.",
            "alertas": {
                "alerta_fatiga": 1,
                "alerta_dolor": 1,
                "alerta_sueno": 1,
                "alerta_estres": 1,
                "alerta_rendimiento": 1
            }
        }
