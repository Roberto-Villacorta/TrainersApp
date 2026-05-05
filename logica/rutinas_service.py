import logging
import os
from sqlalchemy.orm import Session
from logica.vlm_service import VLMService
from bbdd.repository import RoutineRepository

logger = logging.getLogger(__name__)

class RutinasService:
    """
    Servicio orquestador para procesar imágenes de rutinas usando el VLM (Qwen2-VL) y persistir los resultados.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.vlm_service = VLMService.get_instance()
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

            # 2. Adaptar al formato esperado por el Repository
            ejercicios_db = []
            for ej in ejercicios_vlm:
                nombre_raw = ej.get("nombre", "Desconocido")
                nombre_enriquecido = self._normalizar_nombre(nombre_raw)
                
                rango_reps = ej.get("rango_reps", "")
                series_list = ej.get("series", [])
                
                num_series = len(series_list) if isinstance(series_list, list) else 1
                
                series_verbose_parts = []
                for idx, s in enumerate(series_list, 1):
                    s_str = str(s).lower()
                    if "x" in s_str:
                        parts = s_str.split("x")
                        reps_str = f"{parts[0].strip()} reps"
                        peso_str = f"{parts[1].strip()}kg" if len(parts) > 1 else ""
                        series_verbose_parts.append(f"Serie {idx}: {reps_str} {peso_str}".strip())
                    else:
                        series_verbose_parts.append(f"Serie {idx}: {s_str}")
                
                peso_obj = " | ".join(series_verbose_parts)
                reps_final = f"{rango_reps} reps objetivo" if rango_reps else "No especificado"
                
                ejercicios_db.append({
                    "nombre_ejercicio": nombre_enriquecido,
                    "series": str(num_series),
                    "repeticiones": reps_final,
                    "peso_objetivo": peso_obj,
                    "tiempo_descanso": ""
                })
            
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

    def _normalizar_nombre(self, nombre_ia: str) -> str:
        """
        Intenta expandir abreviaturas y encontrar el nombre canónico del ejercicio.
        Retorna 'Original (Canonico)' si hay coincidencia.
        """
        try:
            from logica.ia_service import ExpansorAbreviaturas, ABREVIATURAS, EJERCICIOS_CANONICOS, _normalizar_texto_base
            import difflib
            
            nombre_clean = nombre_ia.strip()
            nombre_norm = _normalizar_texto_base(nombre_clean)
            
            expansor = ExpansorAbreviaturas(ABREVIATURAS)
            nombre_exp = expansor.expandir(nombre_clean)
            
            # 1. Si hubo expansión por diccionario de abreviaturas
            if nombre_exp.lower() != nombre_norm.lower():
                return f"{nombre_clean} ({nombre_exp.title()})"
            
            # 2. Si no, búsqueda difusa (Fuzzy Match) en el catálogo canónico completo
            coincidencias = difflib.get_close_matches(nombre_norm, EJERCICIOS_CANONICOS, n=1, cutoff=0.7)
            if coincidencias and coincidencias[0].lower() != nombre_norm.lower():
                return f"{nombre_clean} ({coincidencias[0].title()})"
            
            return nombre_clean
        except Exception as e:
            logger.error(f"Error en normalización de nombre: {e}")
            return nombre_ia

