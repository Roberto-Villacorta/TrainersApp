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
                
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                cache_dir = os.path.join(base_dir, "modelos_vlm")
                os.makedirs(cache_dir, exist_ok=True)

                if torch.cuda.is_available():
                    device = "cuda"
                    dtype = torch.float16
                    logger.info("Tarjeta grafica detectada. Procesamiento acelerado activado.")
                else:
                    device = "cpu"
                    dtype = torch.float32
                    logger.info("Usando el procesador del ordenador (CPU).")

                kwargs = {
                    "torch_dtype": dtype,
                    "low_cpu_mem_usage": True,
                    "device_map": "auto" if device == "cuda" else "cpu",
                    "cache_dir": cache_dir
                }

                try:
                    VLMService._processor = AutoProcessor.from_pretrained(model_id, cache_dir=cache_dir, local_files_only=True)
                    VLMService._model = AutoVLM.from_pretrained(model_id, local_files_only=True, **kwargs)
                    logger.info("Cerebro digital cargado y listo.")
                except Exception:
                    logger.info("Configurando el sistema por primera vez... descargando componentes (solo una vez).")
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

        prompt = """Read the handwritten gym routine in this image and output the data in JSON format.

INSTRUCTIONS:
1. Identify 'Mesociclo', 'Semana', and 'Sesion' from the top header.
2. Extract EVERY exercise row from the table. 
3. For each exercise, capture the exact name written, the rep range (e.g., 2-5, 10-12), and all the sets performed (e.g., 5x30, 11x110).
4. CRITICAL: If a cell is crossed out with a slash or an X, do NOT include that set.
5. Do NOT include any intro or outro text. Output ONLY the raw JSON.

DATA SCHEMA:
{
  "mesociclo": "string",
  "semana": "string",
  "sesion": "string",
  "ejercicios": [
    {
      "nombre": "string (the actual exercise name from the image)",
      "rango_reps": "string (the target reps)",
      "series": ["string (reps x weight)", ...]
    }
  ]
}"""

        try:
            from PIL import Image
            import torch

            if not torch.cuda.is_available():
                torch.set_num_threads(os.cpu_count() or 4)

            image = Image.open(image_path).convert("RGB")
            image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)

            messages = [
                {
                    "role": "user",
                    "content": [{"type": "image"}, {"type": "text", "text": prompt}]
                }
            ]
            
            input_text = VLMService._processor.apply_chat_template(messages, add_generation_prompt=True)
            
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

            output_ids = generated_ids[:, inputs["input_ids"].shape[1]:]
            output_text = VLMService._processor.batch_decode(output_ids, skip_special_tokens=True)[0]

            logger.info("Analisis completado. Extrayendo datos...")
            
            start = output_text.find('{')
            end = output_text.rfind('}')
            if start != -1 and end != -1:
                json_str = output_text[start:end+1]
                return json.loads(json_str)
            
            raise ValueError("La IA no pudo formatear los datos correctamente.")

        except Exception as e:
            logger.error(f"Error al analizar la imagen: {e}")
            return {"error": "No se pudo leer la imagen correctamente.", "ejercicios": []}


