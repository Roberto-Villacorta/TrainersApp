from database import engine, Base
from models import *
# Importamos models para que SQLAlchemy lea las clases antes de crear las tablas

def iniciar_base_datos():
    print("Iniciando creación de la base de datos...")
    # Esta línea crea el archivo .db y todas las tablas si no existen
    Base.metadata.create_all(bind=engine)
    print("¡Base de datos 'entrenador_app.db' creada exitosamente con todas sus tablas!")
