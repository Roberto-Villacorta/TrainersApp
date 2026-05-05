import logging
import os
import json
import re
import threading
from typing import Dict, Any

logger = logging.getLogger(__name__)


class VLMService:
    _instance = None
    _model = None
    _processor = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._load_model()

    def _load_model(self):
        if VLMService._model is None:
            logger.info("Iniciando el motor de inteligencia artificial local...")
            try:
                import torch
                from transformers import AutoProcessor

                try:
                    from transformers import AutoModelForImageTextToText as AutoVLM
                except ImportError:
                    try:
                        from transformers import AutoModelForVision2Seq as AutoVLM
                    except ImportError:
                        from transformers import AutoModelForCausalLM as AutoVLM

                model_id = "HuggingFaceTB/SmolVLM-Instruct"
                
                # Ruta compatible con Windows y Linux
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                cache_dir = os.path.join(base_dir, "modelos_vlm")
                os.makedirs(cache_dir, exist_ok=True)

                # Detección de aceleración por tarjeta gráfica (GPU)
                if torch.cuda.is_available():
                    device = "cuda"
                    dtype = torch.float16
                    logger.info("¡Tarjeta gráfica detectada! El procesamiento será muy rápido.")
                else:
                    device = "cpu"
                    dtype = torch.float32
                    logger.info("Usando el procesador del ordenador (CPU). Esto puede tardar un poco.")

                kwargs = {
                    "torch_dtype": dtype,
                    "low_cpu_mem_usage": True,
                    "device_map": "auto" if device == "cuda" else "cpu",
                    "cache_dir": cache_dir
                }

                try:
                    # Intento de carga rápida sin conexión
                    VLMService._processor = AutoProcessor.from_pretrained(model_id, cache_dir=cache_dir, local_files_only=True)
                    VLMService._model = AutoVLM.from_pretrained(model_id, local_files_only=True, **kwargs)
                    logger.info("Cerebro digital cargado y listo para trabajar.")
                except Exception:
                    logger.info("Configurando el sistema por primera vez... descargando componentes necesarios (solo una vez).")
                    VLMService._processor = AutoProcessor.from_pretrained(model_id, cache_dir=cache_dir)
                    VLMService._model = AutoVLM.from_pretrained(model_id, **kwargs)
                
                VLMService._model.eval()
            except Exception as e:
                logger.error(f"No se pudo iniciar la IA: {e}")
                raise

    def procesar_imagen_rutina(self, image_path: str) -> Dict[str, Any]:
        """Lee la foto y extrae los ejercicios usando inteligencia artificial."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Archivo no encontrado: {image_path}")

        # Prompt mejorado para evitar que la IA invente nombres como "Ex1"
        prompt = """Analyze this photo of a handwritten gym notebook. Extract EVERY exercise written in the table.
Return ONLY a JSON object. No conversation, no explanations.

IMPORTANT RULES:
1. Exercise Name: Use the EXACT name written in the notebook (e.g. "Dom", "Remo", "P. inclinado"). DO NOT use "Ex1" or "Exercise".
2. Multi-row: Extract ALL exercises on the page from top to bottom.
3. Crossed out cells: If a cell has an 'X' or a line through it, skip that specific set.
4. Format: Return a list of exercises, each with 'nombre', 'rango_reps' and a list of 'series' (e.g. ["10x50", "8x50"]).

Expected JSON format:
{
  "mesociclo": "9",
  "semana": "54",
  "sesion": "T2",
  "ejercicios": [
    {
      "nombre": "NOMBRES REALES AQUÍ",
      "rango_reps": "RANGO AQUÍ",
      "series": ["reps x peso", "reps x peso"]
    }
  ]
}"""

        try:
            from PIL import Image
            import torch

            # Aprovechar todos los núcleos del procesador si no hay GPU
            if not torch.cuda.is_available():
                torch.set_num_threads(os.cpu_count() or 4)

            # Optimizar imagen para lectura rápida
            image = Image.open(image_path).convert("RGB")
            # Reducimos tamaño para que la IA no se agobie con píxeles innecesarios
            image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)

            messages = [
                {
                    "role": "user",
                    "content": [{"type": "image"}, {"type": "text", "text": prompt}]
                }
            ]
            
            input_text = VLMService._processor.apply_chat_template(messages, add_generation_prompt=True)
            
            # Mover datos al dispositivo correcto (GPU o CPU)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            inputs = VLMService._processor(text=input_text, images=[image], return_tensors="pt").to(device)

            logger.info(f"Leyendo la foto: {os.path.basename(image_path)}...")
            
            with torch.inference_mode():
                generated_ids = VLMService._model.generate(
                    **inputs, 
                    max_new_tokens=1500,
                    do_sample=False,
                    use_cache=True
                )

            # Traducir los códigos de la IA a texto legible
            output_ids = generated_ids[:, inputs["input_ids"].shape[1]:]
            output_text = VLMService._processor.batch_decode(output_ids, skip_special_tokens=True)[0]

            # Buscar el bloque de datos (JSON) dentro de la respuesta
            start = output_text.find('{')
            end = output_text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(output_text[start:end+1])
            
            raise ValueError("La IA no pudo formatear los datos correctamente.")

        except Exception as e:
            logger.error(f"Error al analizar la imagen: {e}")
            return {"error": "No se pudo leer la imagen correctamente.", "ejercicios": []}

