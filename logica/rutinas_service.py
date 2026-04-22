import logging
import os
from sqlalchemy.orm import Session
from logica.procesador_ocr import OCRProcessor
from logica.ia_service import GlinerService
from logica.exportador import ExportadorExcel
from bbdd.repository import RoutineRepository

logger = logging.getLogger(__name__)

class RutinasService:
    """
    Servicio orquestador para procesar imágenes de rutinas y persistir los resultados.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.ia_service = GlinerService() # Singleton pattern inside
        self.repo = RoutineRepository(session)
        
    def procesar_y_guardar_imagen(self, atleta_id: int, image_path: str, nombre_rutina: str = None) -> dict:
        """
        1. Extrae texto con OCR.
        2. Procesa con IA (GLiNER).
        3. Guarda en BBDD.
        4. Retorna los datos procesados.
        """
        try:
            # 1. OCR
            texto_extraido = OCRProcessor.extract_text(image_path)
            if not texto_extraido:
                return {"success": False, "error": "No se pudo extraer texto de la imagen."}
            
            logger.info(f"Texto OCR extraído: {texto_extraido[:100]}...")
            
            # 2. IA - Gliner
            # Usamos procesar_texto_rutina para detectar automáticamente el formato
            resultados = self.ia_service.procesar_texto_rutina(texto_extraido)
            
            if not resultados:
                return {"success": False, "error": "La IA no pudo identificar ejercicios en el texto."}
            
            # 3. Preparar nombre de rutina si no viene
            if not nombre_rutina:
                nombre_rutina = f"Rutina OCR {os.path.basename(image_path)}"
            
            # 4. Guardar en BBDD
            success_db = self.repo.guardar_rutina_completa(atleta_id, nombre_rutina, resultados)
            
            if success_db:
                return {
                    "success": True, 
                    "data": resultados, 
                    "texto_ocr": texto_extraido,
                    "nombre_rutina": nombre_rutina
                }
            else:
                return {"success": False, "error": "Error al guardar en la base de datos."}
                
        except Exception as e:
            logger.error(f"Error en el pipeline de rutinas: {str(e)}")
            return {"success": False, "error": str(e)}

    def exportar_a_excel(self, ejercicios_data: list, output_path: str):
        """
        Exporta los datos actuales a un archivo Excel.
        """
        return ExportadorExcel.exportar_rutina(ejercicios_data, output_path)
