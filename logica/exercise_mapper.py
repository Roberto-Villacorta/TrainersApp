import logging
import difflib
from utils.text_utils import normalizar_texto_base
from logica.exercise_data import ExpansorAbreviaturas, ABREVIATURAS, EJERCICIOS_CANONICOS

logger = logging.getLogger(__name__)

class ExerciseMapperService:
    """
    Servicio encargado de mapear nombres de ejercicios crudos a nombres canónicos 
    o enriquecidos mediante expansión de abreviaturas y búsqueda difusa.
    """
    def __init__(self):
        self.expansor = ExpansorAbreviaturas(ABREVIATURAS)
        self.catalogo = EJERCICIOS_CANONICOS

    def normalizar_nombre(self, nombre_ia: str) -> str | None:
        """
        Normaliza un nombre de ejercicio detectado por la IA.
        Retorna el nombre enriquecido o None si parece ruido.
        """
        try:
            nombre_clean = nombre_ia.strip()
            if not nombre_clean:
                return None
                
            nombre_norm = normalizar_texto_base(nombre_clean)
            
            # 1. Coincidencia exacta
            if nombre_norm in self.catalogo:
                return nombre_norm.title()
                
            # 2. Expansión de abreviaturas
            nombre_exp = self.expansor.expandir(nombre_clean)
            if nombre_exp.lower() != nombre_norm.lower():
                return nombre_exp.title()
            
            # 3. Búsqueda difusa (Fuzzy Match)
            coincidencias = difflib.get_close_matches(nombre_norm, self.catalogo, n=1, cutoff=0.5)
            if coincidencias:
                return coincidencias[0].title()
            
            return nombre_clean.title()
        except Exception as e:
            logger.error(f"Error en normalización de nombre: {e}")
            return None
