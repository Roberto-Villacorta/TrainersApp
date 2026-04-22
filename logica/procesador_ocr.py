import pytesseract
from PIL import Image, ImageOps, ImageFilter
import logging
import os
import sys

logger = logging.getLogger(__name__)

# ===========================================================================
# CONFIGURACIÓN DE TESSERACT (PARA PORTABILIDAD)
# ===========================================================================
def configurar_tesseract():
    """
    Busca el ejecutable de Tesseract en rutas comunes y en la carpeta local 'bin'
    para permitir que la aplicación sea compartida sin instalaciones manuales.
    """
    # 1. Si ya está en el PATH del sistema, no hacemos nada (pytesseract lo encontrará)
    # Pero para asegurar en Windows, definimos rutas probables:
    
    # Ruta relativa para cuando compartas la carpeta con una versión portable en /bin
    ruta_local_bin = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin", "tesseract.exe")
    
    # Rutas típicas de instalación en Windows
    rutas_instalacion = [
        ruta_local_bin,
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        os.path.join(os.environ.get('LOCALAPPDATA', ''), r'Tesseract-OCR\tesseract.exe')
    ]
    
    for ruta in rutas_instalacion:
        if os.path.exists(ruta):
            pytesseract.pytesseract.tesseract_cmd = ruta
            logger.info(f"Tesseract configurado en: {ruta}")
            return True
            
    logger.warning("No se encontró Tesseract en las rutas comunes. Asegúrate de que esté en el PATH.")
    return False

# Ejecutamos la configuración al importar el módulo
configurar_tesseract()

class OCRProcessor:
    """
    Clase encargada de extraer texto de imágenes utilizando Tesseract OCR.
    Optimizado para texto a mano y tablas.
    """
    
    @staticmethod
    def extract_text(image_path: str) -> str:
        """
        Lee una imagen, aplica preprocesamiento optimizado y extrae el texto.
        """
        if not os.path.exists(image_path):
            logger.error(f"Archivo no encontrado: {image_path}")
            return ""
            
        try:
            logger.info(f"Procesando imagen con preprocesamiento optimizado: {image_path}")
            
            with Image.open(image_path) as img:
                # 1. Convertir a escala de grises
                img = img.convert('L')
                
                # 2. Reescalar imagen (Tesseract prefiere una densidad de píxeles mayor)
                # Doblamos el tamaño si la imagen no es ya gigante
                w, h = img.size
                if w < 2000:
                    img = img.resize((w*2, h*2), Image.Resampling.LANCZOS)
                
                # 3. Autocontraste para estirar el histograma y separar fondo de letra
                img = ImageOps.autocontrast(img)
                
                # 4. Binarización suave (Thresholding)
                # Ayuda a quitar el gris del papel y dejar el texto negro
                img = img.point(lambda p: p > 140 and 255)
                
                # 5. Filtro de nitidez suave
                img = img.filter(ImageFilter.SHARPEN)

                # Configuración de Tesseract:
                # --psm 3: Segmentación automática completa (por defecto)
                # --psm 11: Texto disperso (mejor para tablas dibujadas a mano)
                # Intentamos con psm 3 primero por ser más general
                custom_config = r'--oem 3 --psm 3'
                
                texto = pytesseract.image_to_string(img, lang='spa', config=custom_config)
                
                # Si no pilla nada con psm 3, intentamos con psm 11 (texto disperso)
                if len(texto.strip()) < 5:
                    logger.info("Resultado pobre con PSM 3, reintentando con PSM 11...")
                    custom_config = r'--oem 3 --psm 11'
                    texto = pytesseract.image_to_string(img, lang='spa', config=custom_config)

                logger.info(f"Extracción completada. Longitud: {len(texto)} caracteres.")
                return texto.strip()
                
        except Exception as e:
            logger.error(f"Error durante el proceso de OCR: {str(e)}")
            return ""

    @staticmethod
    def extract_text_advanced(image_path: str) -> str:
        """
        Versión agresiva para imágenes muy difíciles.
        """
        try:
            with Image.open(image_path) as img:
                img = img.convert('L')
                img = ImageOps.invert(img) # Invertir a veces ayuda si el fondo es oscuro
                img = ImageOps.autocontrast(img)
                img = ImageOps.invert(img)
                img = img.filter(ImageFilter.DETAIL)
                
                texto = pytesseract.image_to_string(img, lang='spa', config='--psm 6')
                return texto.strip()
        except Exception as e:
            logger.error(f"Error en OCR avanzado: {str(e)}")
            return ""
