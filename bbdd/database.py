from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from utils.paths import get_database_path

# Usamos la ruta centralizada para la base de datos (AppData/Application Support)
db_path = get_database_path()
# Usamos as_posix() para asegurar que las barras sean correctas en la URL de SQLite (especialmente en Windows)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path.as_posix()}"

# engine es el "motor" que habla con SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # Necesario en SQLite para evitar errores con interfaces gráficas
)

# SessionLocal será la clase que usaremos para abrir "ventanas" de conexión y hacer consultas
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base es la clase madre de la que heredarán todas nuestras tablas
Base = declarative_base()