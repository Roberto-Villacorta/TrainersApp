import os
import sys
from pathlib import Path

def get_app_data_dir():
    """
    Retorna la ruta de la carpeta de datos de la aplicación.
    Windows: %APPDATA%/TrainersApp
    macOS: ~/Library/Application Support/TrainersApp
    Linux: ~/.config/TrainersApp
    """
    app_name = "TrainersApp"
    
    if sys.platform == "win32":
        base_dir = os.environ.get("APPDATA")
    elif sys.platform == "darwin":
        base_dir = os.path.expanduser("~/Library/Application Support")
    else:
        base_dir = os.path.expanduser("~/.config")
        
    if not base_dir:
        # Fallback si no se detecta la carpeta de usuario
        if getattr(sys, 'frozen', False):
            # Si es un ejecutable, usamos la carpeta donde esta el .exe
            base_dir = os.path.dirname(sys.executable)
        else:
            # Si es desarrollo, usamos la carpeta del proyecto
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    app_dir = Path(base_dir) / app_name
    
    try:
        # Crear la carpeta si no existe
        if not app_dir.exists():
            app_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Fallback de emergencia: usar carpeta 'datos_aplicacion' en el directorio del ejecutable/script
        if getattr(sys, 'frozen', False):
            current_dir = Path(os.path.dirname(sys.executable))
        else:
            current_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        app_dir = current_dir / "datos_aplicacion"
        app_dir.mkdir(parents=True, exist_ok=True)
        
    return app_dir

def get_database_path():
    """Retorna la ruta completa a la base de datos SQLite."""
    return get_app_data_dir() / "entrenador_app.db"

def get_models_dir():
    """Retorna la ruta para almacenar los modelos de IA."""
    models_dir = get_app_data_dir() / "models"
    if not models_dir.exists():
        models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir

def get_logs_dir():
    """Retorna la ruta para almacenar los logs."""
    logs_dir = get_app_data_dir() / "logs"
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir
