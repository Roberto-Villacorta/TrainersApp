import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    """
    Configura y devuelve el logger principal de la aplicación.
    Maneja tanto la salida por consola como la rotación de archivos de log.
    """
    from utils.paths import get_logs_dir
    # Directorio donde se guardarán los archivos de registro físicos
    log_dir = str(get_logs_dir())
    log_file = os.path.join(log_dir, "entrenador_app.log")

    # Crear logger principal
    logger = logging.getLogger("EntrenadorApp")
    
    # Solo configurar si no tiene handlers ya asignados (para evitar duplicados si se importa múltiples veces)
    if not logger.handlers:
        # Nivel mínimo de captura
        logger.setLevel(logging.DEBUG)

        # Formato de los mensajes: [Fecha/Hora] - [Nivel] - [Archivo:Linea] - Mensaje
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 1. File Handler: Escribe en un archivo. 
        # Rota el archivo si alcanza los 5 MB y mantiene hasta 5 archivos de backup.
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=5*1024*1024, 
            backupCount=5, 
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG) # En el archivo guardamos TODO (DEBUG y superior)
        file_handler.setFormatter(formatter)

        # 2. Console Handler: Escribe en la terminal.
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO) # En consola mostramos INFO, WARNING, ERROR, CRITICAL
        console_handler.setFormatter(formatter)

        # Añadir ambos comportamientos al logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Al importar este módulo, automáticamente se crea/obtiene la instancia del logger configurado.
# De esta forma puedes importar `app_logger` en cualquier archivo de tu aplicación.
app_logger = setup_logger()
