import os
import sqlite3
from bbdd.database import engine, Base
from bbdd.models import *
from utils.logger import app_logger
# Importamos models para que SQLAlchemy lea las clases antes de crear las tablas

def iniciar_base_datos():
    ruta_db = "datos_locales/entrenador_app.db"
    if not os.path.exists(ruta_db):
        app_logger.info("Iniciando creación de la base de datos...")
        # Asegurarnos de que el directorio existe
        os.makedirs(os.path.dirname(ruta_db), exist_ok=True)
        Base.metadata.create_all(bind=engine)
        app_logger.info("¡Base de datos 'entrenador_app.db' creada exitosamente con todas sus tablas!")
    else:
        app_logger.info("La base de datos ya existe. Conectando y verificando tablas...")
        # create_all es seguro de ejecutar aunque la BD exista; añadirá tablas que falten.
        Base.metadata.create_all(bind=engine)
        
        # Migraciones manuales para añadir columnas que SQLite y create_all no detectan automáticamente
        try:
            conn = sqlite3.connect(ruta_db)
            cursor = conn.cursor()
            
            # Revisar tabla atletas
            cursor.execute("PRAGMA table_info(atletas)")
            columnas = [info[1] for info in cursor.fetchall()]
            
            if "foto_perfil" not in columnas:
                app_logger.info("Añadiendo columna 'foto_perfil' a 'atletas'...")
                cursor.execute("ALTER TABLE atletas ADD COLUMN foto_perfil BLOB")
                
            if "fecha_comienzo" not in columnas:
                app_logger.info("Añadiendo columna 'fecha_comienzo' a 'atletas'...")
                cursor.execute("ALTER TABLE atletas ADD COLUMN fecha_comienzo DATE")
                
            conn.commit()
            conn.close()
        except Exception as e:
            app_logger.error(f"Error al verificar/actualizar esquema de la base de datos: {e}")
