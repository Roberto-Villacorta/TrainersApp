import logging
from logica.exercise_mapper import ExerciseMapperService

logger = logging.getLogger(__name__)

class RoutineTransformerService:
    """
    Servicio encargado de transformar los datos crudos extraídos por el VLM 
    al formato estructurado requerido por la base de datos y la interfaz.
    """
    def __init__(self):
        self.mapper = ExerciseMapperService()

    def transformar_datos_vlm_a_db(self, vlm_data: dict) -> list:
        """
        Convierte la salida JSON del VLM al formato esperado por el repositorio.
        """
        ejercicios_vlm = vlm_data.get("ejercicios", [])
        ejercicios_db = []
        
        for ej in ejercicios_vlm:
            nombre_raw = ej.get("nombre", "Desconocido")
            nombre_enriquecido = self.mapper.normalizar_nombre(nombre_raw)
            
            if not nombre_enriquecido:
                logger.info(f"Ignorando texto aleatorio/desconocido: {nombre_raw}")
                continue
            
            series_list = ej.get("series", [])
            rango_reps = ej.get("rango_reps", "")
            
            peso_obj = self._formatear_series_verbose(series_list)
            num_series = len(series_list) if isinstance(series_list, list) else 1
            reps_final = f"{rango_reps} reps objetivo" if rango_reps else "No especificado"
            
            ejercicios_db.append({
                "nombre_ejercicio": nombre_enriquecido,
                "series": str(num_series),
                "repeticiones": reps_final,
                "peso_objetivo": peso_obj,
                "tiempo_descanso": ""
            })
            
        return ejercicios_db

    def _formatear_series_verbose(self, series_list: list) -> str:
        """Convierte una lista de series ['10x40', '10x40'] en un string legible."""
        series_verbose_parts = []
        if not isinstance(series_list, list):
            return str(series_list)
            
        for idx, s in enumerate(series_list, 1):
            s_str = str(s).lower()
            if "x" in s_str:
                parts = s_str.split("x")
                reps_part = parts[0].strip()
                peso_part = parts[1].strip() if len(parts) > 1 else ""
                
                # Aplicar limpieza de peso lógico
                peso_limpio = self._limpiar_peso_logico(peso_part)
                
                reps_str = f"{reps_part} reps"
                peso_str = f"{peso_limpio}kg" if peso_limpio else ""
                series_verbose_parts.append(f"Serie {idx}: {reps_str} {peso_str}".strip())
            else:
                series_verbose_parts.append(f"Serie {idx}: {s_str}")
                
        return " | ".join(series_verbose_parts)

    def _limpiar_peso_logico(self, peso_str: str) -> str:
        """
        Detecta y corrige pesos que no tienen sentido físico (ej: 505 -> 50.5).
        """
        if not peso_str: return ""
        solo_numeros = "".join(filter(str.isdigit, peso_str))
        if not solo_numeros: return peso_str
        
        try:
            val = int(solo_numeros)
            # Si el peso es > 300 y no tiene decimales, es muy probable que falte el punto
            if val > 300 and "." not in peso_str and "," not in peso_str:
                return str(val / 10.0)
        except:
            pass
        return peso_str
