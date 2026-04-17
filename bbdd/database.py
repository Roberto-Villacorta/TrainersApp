from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Creamos el archivo de la base de datos local en la carpeta datos_locales
SQLALCHEMY_DATABASE_URL = "sqlite:///datos_locales/entrenador_app.db"

# engine es el "motor" que habla con SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # Necesario en SQLite para evitar errores con interfaces gráficas
)

# SessionLocal será la clase que usaremos para abrir "ventanas" de conexión y hacer consultas
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base es la clase madre de la que heredarán todas nuestras tablas
Base = declarative_base()