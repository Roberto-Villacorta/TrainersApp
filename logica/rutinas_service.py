import logging
import os
from sqlalchemy.orm import Session
from logica.vlm_service import VLMService
from logica.routine_transformer import RoutineTransformerService
from bbdd.repository import RoutineRepository

logger = logging.getLogger(__name__)

class RutinasService:
    """
    Servicio orquestador para procesar imágenes de rutinas usando el VLM (Qwen2-VL) y persistir los resultados.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.vlm_service = VLMService.get_instance()
        self.transformer = RoutineTransformerService()
        self.repo = RoutineRepository(session)
        
        
    def procesar_imagen_vlm_a_diccionario(self, image_path: str) -> dict:
        """
        Llama al VLM y convierte el JSON al formato esperado por el frontend y BBDD.
        """
        try:
            logger.info(f"Enviando imagen a VLMService: {image_path}")
            
            # 1. IA - VLM
            vlm_data = self.vlm_service.procesar_imagen_rutina(image_path)
            
            if "error" in vlm_data and not vlm_data.get("ejercicios"):
                return {"success": False, "error": vlm_data["error"]}
                
            ejercicios_vlm = vlm_data.get("ejercicios", [])
            
            if not ejercicios_vlm:
                return {"success": False, "error": "La IA no pudo extraer ningún ejercicio de la libreta."}

            # 2. Adaptar al formato esperado por el Repository usando el nuevo servicio
            ejercicios_db = self.transformer.transformar_datos_vlm_a_db(vlm_data)
            
            if not ejercicios_db:
                return {"success": False, "error": "No se encontraron ejercicios validos en la imagen tras filtrar ruido."}

            # 3. Construir un nombre de rutina enriquecido con Mesociclo y Semana
            meso = vlm_data.get("mesociclo", "")
            sem = vlm_data.get("semana", "")
            ses = vlm_data.get("sesion", "")
            
            nombre_generado = []
            if meso: nombre_generado.append(f"Meso {meso}")
            if sem: nombre_generado.append(f"Sem {sem}")
            if ses: nombre_generado.append(f"Ses {ses}")
            
            prefijo = " - ".join(nombre_generado)
            
            return {
                "success": True, 
                "data": ejercicios_db, 
                "prefijo": prefijo,
                "texto_ocr": str(vlm_data)  # crudo para debug
            }
            
        except Exception as e:
            logger.error(f"Error parseando VLM: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def procesar_imagen_vlm_secuencial(self, image_path: str, progress_callback=None) -> dict:
        """
        Versión mejorada: Procesa la imagen por etapas (Cabecera -> Lista -> Detalles)
        para mejorar la precisión y dar feedback en tiempo real.
        """
        try:
            logger.info(f"Enviando imagen a VLMService (MODO SECUENCIAL): {image_path}")
            
            # 1. IA - VLM en modo secuencial
            vlm_data = self.vlm_service.procesar_imagen_rutina_secuencial(image_path, progress_callback)
            
            if "error" in vlm_data and not vlm_data.get("ejercicios"):
                return {"success": False, "error": vlm_data["error"]}
                
            ejercicios_vlm = vlm_data.get("ejercicios", [])
            
            if not ejercicios_vlm:
                return {"success": False, "error": "La IA no pudo extraer ningún ejercicio."}

            # 2. Adaptar al formato esperado por el Repository
            ejercicios_db = self.transformer.transformar_datos_vlm_a_db(vlm_data)
            
            # 3. Construir prefijo
            meso = vlm_data.get("mesociclo", "")
            sem = vlm_data.get("semana", "")
            ses = vlm_data.get("sesion", "")
            nombre_gen = []
            if meso: nombre_gen.append(f"Meso {meso}")
            if sem: nombre_gen.append(f"Sem {sem}")
            if ses: nombre_gen.append(f"Ses {ses}")
            prefijo = " - ".join(nombre_gen)
            
            return {
                "success": True, 
                "data": ejercicios_db, 
                "prefijo": prefijo
            }
        except Exception as e:
            logger.error(f"Error en RutinasService secuencial: {e}")
            return {"success": False, "error": str(e)}

    def procesar_y_guardar_imagen(self, atleta_id: int, image_path: str, nombre_rutina: str = None) -> dict:
        """
        1. Procesa imagen directamente con Qwen2-VL.
        2. Adapta el JSON al formato de BBDD.
        3. Guarda en BBDD.
        4. Retorna los datos procesados.
        """
        try:
            resultado_parseo = self.procesar_imagen_vlm_a_diccionario(image_path)
            if not resultado_parseo["success"]:
                return resultado_parseo
                
            ejercicios_db = resultado_parseo["data"]
            prefijo = resultado_parseo.get("prefijo", "")
            
            if not nombre_rutina:
                if prefijo:
                    nombre_rutina = prefijo
                else:
                    nombre_rutina = f"Rutina {os.path.basename(image_path)}"
            else:
                if prefijo and prefijo not in nombre_rutina:
                    nombre_rutina = f"{prefijo} | {nombre_rutina}"
            
            # 4. Guardar en BBDD
            success_db = self.repo.guardar_rutina_completa(atleta_id, nombre_rutina, ejercicios_db)
            
            if success_db:
                resultado_parseo["nombre_generado"] = nombre_rutina
                return resultado_parseo
            else:
                return {"success": False, "error": "Error al guardar la rutina en la base de datos."}
                
        except Exception as e:
            logger.error(f"Error procesando rutina: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}


