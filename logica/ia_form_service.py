import os
from utils.logger import app_logger


class IAFormService:
    """
    Servicio de análisis de formularios semanales mediante GLiNER.

    Interpreta las respuestas de texto libre del formulario del atleta y genera
    métricas de alerta heurísticas (fatiga, dolor, sueño, estrés, rendimiento)
    en una escala del 1 al 5.

    El modelo GLiNER se mantiene como singleton de clase para evitar recargar
    los ~200 MB del modelo en cada formulario guardado. La primera vez que se
    instancia la clase se carga el modelo desde la caché local (o se descarga
    si no está disponible); las instancias posteriores reutilizan el objeto ya
    cargado en memoria.
    """

    _model = None  # Singleton compartido entre todas las instancias

    def __init__(self):
        if IAFormService._model is None:
            try:
                from logica.ia_service import GlinerService, MODEL_DIR
                os.environ["HF_HOME"] = MODEL_DIR

                # Si GlinerService ya cargó el modelo previamente, lo reutilizamos
                # directamente. En caso contrario, forzamos la carga ahora.
                if GlinerService._modelo is None:
                    GlinerService(cargar_modelo_al_inicio=True)

                IAFormService._model = GlinerService._modelo
                app_logger.info("Modelo GLiNER vinculado correctamente para análisis de formularios.")
            except Exception as e:
                app_logger.error(f"Error cargando GLiNER en IAFormService: {e}")
                IAFormService._model = None

    def analizar_formulario(self, respuestas: dict) -> dict:
        """
        Analiza las respuestas de texto libre de un formulario y devuelve
        un resumen textual junto con las alertas calculadas.

        El análisis concatena los campos de texto relevantes (satisfacción,
        adherencia, saciedad y dudas), los pasa por GLiNER con etiquetas de
        alerta predefinidas y traduce las entidades detectadas a valores
        numéricos de alerta mediante reglas heurísticas simples.

        Args:
            respuestas: Dict con claves 'comentario_satisfaccion', 'lleva_mejor',
                        'cuesta_mas', 'comentario_saciedad' y 'dudas'.

        Returns:
            Dict con dos claves:
            - ``resumen``: cadena de texto descriptiva para mostrar en la UI.
            - ``alertas``: dict con 'alerta_fatiga', 'alerta_dolor',
              'alerta_sueno', 'alerta_estres' y 'alerta_rendimiento' (valores 1-5).
        """
        if not IAFormService._model:
            return self._generar_vacio()

        textos = [
            respuestas.get("comentario_satisfaccion", ""),
            respuestas.get("lleva_mejor", ""),
            respuestas.get("cuesta_mas", ""),
            respuestas.get("comentario_saciedad", ""),
            respuestas.get("dudas", ""),
        ]
        texto_completo = ". ".join([str(t) for t in textos if t])

        if not texto_completo.strip():
            return self._generar_vacio()

        # Etiquetas de alerta reconocidas por el modelo en Zero-shot
        labels = ["dolor", "lesión", "cansancio", "fatiga", "estrés", "agobio", "sueño", "mejora", "hambre", "ansiedad"]
        entities = IAFormService._model.predict_entities(texto_completo, labels, threshold=0.3)

        # Valores de alerta iniciales: 1 = sin problema detectado
        alertas = {
            "alerta_fatiga":      1,
            "alerta_dolor":       1,
            "alerta_sueno":       1,
            "alerta_estres":      1,
            "alerta_rendimiento": 1,
        }

        resumen_entidades = []

        for ent in entities:
            label = ent["label"].lower()
            resumen_entidades.append(f"{ent['text']} ({label})")

            # Cada entidad detectada sube 2 puntos el indicador correspondiente
            if label in ["dolor", "lesión"]:
                alertas["alerta_dolor"] = min(5, alertas["alerta_dolor"] + 2)
            elif label in ["cansancio", "fatiga"]:
                alertas["alerta_fatiga"] = min(5, alertas["alerta_fatiga"] + 2)
            elif label in ["estrés", "agobio", "ansiedad"]:
                alertas["alerta_estres"] = min(5, alertas["alerta_estres"] + 2)
            elif label == "sueño":
                alertas["alerta_sueno"] = min(5, alertas["alerta_sueno"] + 2)

        # Si hay fatiga o dolor elevados, la alerta de rendimiento también sube
        if alertas["alerta_fatiga"] > 2 or alertas["alerta_dolor"] > 2:
            alertas["alerta_rendimiento"] = min(5, alertas["alerta_rendimiento"] + 1)

        if resumen_entidades:
            resumen = "IA detectó conceptos clave: " + ", ".join(set(resumen_entidades))
        else:
            resumen = "Análisis IA (GLiNER): No se detectaron alertas significativas."

        return {"resumen": resumen, "alertas": alertas}

    def _generar_vacio(self) -> dict:
        """
        Devuelve una respuesta vacía con todas las alertas al mínimo.
        Se usa cuando el modelo no está disponible o el texto es insuficiente
        para realizar un análisis fiable.
        """
        return {
            "resumen": "Análisis IA no disponible o texto insuficiente.",
            "alertas": {
                "alerta_fatiga":      1,
                "alerta_dolor":       1,
                "alerta_sueno":       1,
                "alerta_estres":      1,
                "alerta_rendimiento": 1,
            },
        }
