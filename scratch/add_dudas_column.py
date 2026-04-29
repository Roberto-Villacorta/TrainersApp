import sqlite3
import os

db_path = "datos_locales/entrenador_app.db"
if not os.path.exists(db_path):
    print(f"Base de datos no encontrada en {db_path}. Se creará al iniciar la app.")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Obtener columnas actuales de formularios_semanales
try:
    cursor.execute("PRAGMA table_info(formularios_semanales)")
    columnas = [info[1] for info in cursor.fetchall()]

    if "dudas" not in columnas and columnas: # si la tabla existe y no tiene la columna
        print("Agregando columna 'dudas' a formularios_semanales...")
        cursor.execute("ALTER TABLE formularios_semanales ADD COLUMN dudas TEXT")
        print("Columna 'dudas' agregada exitosamente.")
    else:
        print("La columna 'dudas' ya existe o la tabla aún no ha sido creada.")
except Exception as e:
    print(f"Error: {e}")

conn.commit()
conn.close()
