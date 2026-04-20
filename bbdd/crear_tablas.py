import os
from bbdd.database import engine, Base
from bbdd.models import *
# Importamos models para que SQLAlchemy lea las clases antes de crear las tablas

def iniciar_base_datos():
    ruta_db = "datos_locales/entrenador_app.db"
    if not os.path.exists(ruta_db):
        print("Iniciando creación de la base de datos...")
        # Asegurarnos de que el directorio existe
        os.makedirs(os.path.dirname(ruta_db), exist_ok=True)
        Base.metadata.create_all(bind=engine)
        print("¡Base de datos 'entrenador_app.db' creada exitosamente con todas sus tablas!")
    else:
        print("La base de datos ya existe. Conectando y verificando tablas...")
        # create_all es seguro de ejecutar aunque la BD exista; añadirá tablas que falten.
        Base.metadata.create_all(bind=engine)
