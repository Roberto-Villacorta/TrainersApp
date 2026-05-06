import logging
import os
import json
import re
import threading
from typing import Dict, Any
from logica.image_processor import ImageProcessorService

logger = logging.getLogger(__name__)


class VLMService:
    _instance = None
    _model = None
    _processor = None
    _lock = threading.Lock()

    @classmethod
    def is_gpu_available(cls):
        """Verifica si hay una GPU NVIDIA disponible para la IA."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Inicialización diferida
        pass

    def _ensure_model_loaded(self):
        """Garantiza que la IA esté lista antes de procesar."""
        if not self.is_gpu_available():
            raise RuntimeError("La función de IA requiere una tarjeta gráfica NVIDIA (GPU) para funcionar.")
            
        if VLMService._model is None:
            with VLMService._lock:
                if VLMService._model is None:
                    self._load_model()

    def _load_model(self):
        if VLMService._model is None:
            logger.info("Iniciando el motor de inteligencia artificial local (MODO GPU EXCLUSIVO)...")
            try:
                import torch
                from transformers import AutoProcessor, BitsAndBytesConfig

                try:
                    from transformers import AutoModelForImageTextToText as AutoVLM
                except ImportError:
                    from transformers import AutoModelForCausalLM as AutoVLM

                model_id = "HuggingFaceTB/SmolVLM-Instruct"
                
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                cache_dir = os.path.join(base_dir, "modelos_vlm")
                os.makedirs(cache_dir, exist_ok=True)

                # Configuración de compresión (4-bit) para evitar usar el disco duro (disk offloading)
                # Esto reduce el uso de memoria de 5GB a ~1.5GB
                try:
                    quantization_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_use_double_quant=True,
                    )
                    logger.info("Configurando compresion de 4 bits para maxima velocidad...")
                except Exception:
                    quantization_config = None
                    logger.info("Compresion de 4 bits no disponible, usando precision estandar.")

                if torch.cuda.is_available():
                    device = "cuda"
                    dtype = torch.float16
                    device_map = "auto"
                else:
                    logger.error("No se detectó GPU CUDA. La IA no puede arrancar.")
                    raise RuntimeError("La función de IA requiere una tarjeta gráfica NVIDIA (GPU) para funcionar.")

                kwargs = {
                    "torch_dtype": dtype,
                    "low_cpu_mem_usage": True,
                    "cache_dir": cache_dir,
                }
                
                if quantization_config:
                    kwargs["quantization_config"] = quantization_config
                
                if device_map:
                    kwargs["device_map"] = device_map

                logger.info("Cargando cerebro digital optimizado...")
                VLMService._processor = AutoProcessor.from_pretrained(model_id, cache_dir=cache_dir)
                VLMService._model = AutoVLM.from_pretrained(model_id, **kwargs)
                
                VLMService._model.eval()
                logger.info("IA lista y optimizada.")
            except Exception as e:
                logger.error(f"No se pudo iniciar la IA: {e}")
                raise

    def _realizar_inferencia(self, image, prompt, max_tokens=500):
        """Helper interno para realizar una inferencia atómica con un prompt específico."""
        import torch
        
        messages = [
            {
                "role": "user",
                "content": [{"type": "image"}, {"type": "text", "text": prompt}]
            }
        ]
        
        input_text = VLMService._processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = VLMService._processor(text=input_text, images=[image], return_tensors="pt").to(VLMService._model.device)
        
        with torch.inference_mode():
            generated_ids = VLMService._model.generate(
                **inputs, 
                max_new_tokens=max_tokens,
                do_sample=False,
                use_cache=True
            )

        output_ids = generated_ids[:, inputs["input_ids"].shape[1]:]
        output_text = VLMService._processor.batch_decode(output_ids, skip_special_tokens=True)[0]
        
        # Extraer JSON de la respuesta de forma robusta
        try:
            start = output_text.find('{')
            end = output_text.rfind('}')
            if start != -1 and end != -1:
                json_str = output_text[start:end+1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # Intento de reparación simple si falla el estándar
                    json_str = self._reparar_json_sucio(json_str)
                    return json.loads(json_str)
        except Exception as e:
            logger.warning(f"No se pudo decodificar ni reparar el JSON. Error: {e}")
            
        return None

    def _reparar_json_sucio(self, s: str) -> str:
        """
        Intenta arreglar fallos comunes de la IA en JSON.
        """
        import re
        s = re.sub(r',\s*([}\]])', r'\1', s)
        s = re.sub(r'}\s*{', '}, {', s)
        s = re.sub(r'"\s+"', '", "', s)
        return s

    def procesar_imagen_rutina_secuencial(self, image_path: str, progress_callback=None) -> Dict[str, Any]:
        """
        Orquesta la extracción por fases (Cabecera -> Tabla Completa).
        """
        self._ensure_model_loaded()
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Archivo no encontrado: {image_path}")

        try:
            # Diccionario base de extracción
            res = {"mesociclo": "", "semana": "", "sesion": "", "ejercicios": []}

            # 1. Fase Cabecera (Mesociclo, Semana)
            self._ejecutar_fase_cabecera(image_path, res, progress_callback)

            # 2. Fase Tabla Completa
            self._ejecutar_fase_tabla(image_path, res, progress_callback)

            if not res["ejercicios"]:
                # Fallback al modo tradicional si la fase secuencial falla
                logger.info("Modo secuencial fallido, intentando fallback...")
                res = self.procesar_imagen_rutina(image_path)
            
            if not res.get("ejercicios"):
                return {"success": False, "error": "No se detectaron ejercicios en la imagen."}

            # Generar el prefijo para la UI (Meso X - Sem Y)
            prefijo = ""
            if res.get("mesociclo") or res.get("semana"):
                prefijo = f"Meso {res.get('mesociclo', '?')} - Sem {res.get('semana', '?')}"
                if res.get("sesion"): prefijo += f" - {res['sesion']}"

            return {
                "success": True, 
                "prefijo": prefijo,
                "data": res # Enviamos el dict completo para el cargador
            }

        except Exception as e:
            logger.error(f"Error en pipeline secuencial: {e}")
            return {"success": False, "error": str(e)}

    def _ejecutar_fase_cabecera(self, path, res_dict, callback):
        """Fase 1: Recorte superior y extracción de metadatos."""
        if callback: callback("Detectando cabecera...")
        img = ImageProcessorService.preparar_para_vlm(path, solo_cabecera=True)
        # Revertimos al prompt original que funcionaba
        prompt = "Read header. JSON: {\"mesociclo\": \"...\", \"semana\": \"...\", \"sesion\": \"...\"}"
        data = self._realizar_inferencia(img, prompt, max_tokens=64)
        if data:
            res_dict.update(data)
        del img

    def _ejecutar_fase_tabla(self, path, res_dict, callback):
        """Fase 2: Imagen completa y extracción de tabla."""
        if callback: callback("Extrayendo tabla de ejercicios...")
        img = ImageProcessorService.preparar_para_vlm(path)
        # Revertimos al prompt original que era infalible
        prompt = """Read all exercise rows in this table.
        For each exercise, extract: name, target rep range, and all sets (reps x weight).
        Ignore crossed out sets.
        Return ONLY JSON: {"ejercicios": [{"nombre": "...", "rango_reps": "...", "series": ["...", ...]}, ...]}"""
        
        data = self._realizar_inferencia(img, prompt, max_tokens=2000)
        if data and "ejercicios" in data:
            res_dict["ejercicios"] = data["ejercicios"]
        del img

    def procesar_imagen_rutina(self, image_path: str) -> Dict[str, Any]:
        """Lectura tradicional (todo de una vez) como fallback o modo rápido."""
        self._ensure_model_loaded()
        try:
            image = ImageProcessorService.preparar_para_vlm(image_path)
            prompt = """Read the handwritten gym routine in this image and output the data in JSON format.
            Identify 'mesociclo', 'semana', 'sesion' and all 'ejercicios' (nombre, rango_reps, series).
            Ignore crossed out sets. Use the following schema:
            {
              "mesociclo": "...", "semana": "...", "sesion": "...",
              "ejercicios": [{"nombre": "...", "rango_reps": "...", "series": ["...", ...]}]
            }"""
            data = self._realizar_inferencia(image, prompt, max_tokens=1500)
            return data if data else {"error": "No se pudieron extraer datos", "ejercicios": []}
        except Exception as e:
            logger.error(f"Error en procesar_imagen_rutina: {e}")
            return {"error": str(e), "ejercicios": []}


