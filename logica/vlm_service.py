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
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Inicialización diferida: el modelo no se carga hasta el primer uso
        pass

    def _ensure_model_loaded(self):
        """Garantiza que la IA esté lista antes de procesar."""
        if VLMService._model is None:
            with VLMService._lock:
                if VLMService._model is None:
                    self._load_model()

    def _load_model(self):
        if VLMService._model is None:
            logger.info("Iniciando el motor de inteligencia artificial local...")
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
                    device = "cpu"
                    dtype = torch.float32
                    device_map = None # En CPU no usamos device_map auto normalmente
                    quantization_config = None # 4-bit solo funciona en NVIDIA/CUDA

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
            logger.debug(f"Respuesta cruda: {output_text}")
            
        return None

    def _reparar_json_sucio(self, s: str) -> str:
        """
        Intenta arreglar fallos comunes de la IA en JSON como comas faltantes 
        o comas sobrantes al final de una lista.
        """
        import re
        # 1. Eliminar comas antes de cerrar llaves o corchetes: ,} -> } o ,] -> ]
        s = re.sub(r',\s*([}\]])', r'\1', s)
        # 2. Intentar poner comas faltantes entre objetos: } { -> }, {
        s = re.sub(r'}\s*{', '}, {', s)
        # 3. Intentar poner comas faltantes entre elementos de lista: " " -> ", "
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
            resultado = {"mesociclo": "", "semana": "", "sesion": "", "ejercicios": []}

            # 1. Fase Cabecera (Mesociclo, Semana)
            self._ejecutar_fase_cabecera(image_path, resultado, progress_callback)

            # 2. Fase Tabla Completa
            self._ejecutar_fase_tabla(image_path, resultado, progress_callback)

            return {"success": True, "data": resultado}

        except Exception as e:
            logger.error(f"Error en pipeline secuencial: {e}")
            if progress_callback: progress_callback(f"Error: {str(e)}. Reintentando modo general...")
            return self.procesar_imagen_rutina(image_path)

    def _ejecutar_fase_cabecera(self, path, res_dict, callback):
        """Fase 1: Recorte superior y extracción de metadatos de la sesión."""
        if callback: callback("Analizando cabecera...")
        img = ImageProcessorService.preparar_para_vlm(path, solo_cabecera=True)
        prompt = "Identify the training cycle. Return JSON: {\"mesociclo\": \"NUMBER\", \"semana\": \"NUMBER\", \"sesion\": \"NUMBER/NAME\"}."
        data = self._realizar_inferencia(img, prompt, max_tokens=64)
        if data:
            res_dict.update(data)
        del img

    def _ejecutar_fase_tabla(self, path, res_dict, callback):
        """Fase 2: Imagen completa y extracción de todos los ejercicios."""
        if callback: callback("Analizando tabla completa de ejercicios...")
        img = ImageProcessorService.preparar_para_vlm(path)
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


