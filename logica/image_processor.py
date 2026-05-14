from PIL import Image, ImageOps
import logging

logger = logging.getLogger(__name__)

class ImageProcessorService:
    """
    Servicio especializado en la optimización de imágenes para visión artificial.
    Se encarga de reducir el peso manteniendo la legibilidad máxima.
    """
    
    @staticmethod
    def preparar_para_vlm(image_path: str, max_size=(672, 672), solo_cabecera=False):
        """
        Carga, redimensiona y opcionalmente recorta la imagen para acelerar el proceso.
        solo_cabecera: Si es True, solo devuelve el 20% superior (acelera lectura de Meso/Semana).
        """
        try:
            img = Image.open(image_path)
            
            # Si solo queremos la cabecera, recortamos antes de escalar para no perder detalle
            if solo_cabecera:
                w, h = img.size
                img = img.crop((0, 0, w, int(h * 0.20))) # 20% superior
            
            img.thumbnail(max_size, Image.Resampling.BICUBIC)
            img = img.convert("RGB")
            img = ImageOps.autocontrast(img, cutoff=1)
            
            return img
        except Exception as e:
            logger.error(f"Error procesando imagen {image_path}: {e}")
            raise
