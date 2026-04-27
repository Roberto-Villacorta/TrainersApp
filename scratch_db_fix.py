import sqlite3
import os

db_path = "datos_locales/entrenador_app.db"
if not os.path.exists(db_path):
    print(f"Error: Base de datos no encontrada en {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Obtener columnas actuales
cursor.execute("PRAGMA table_info(atletas)")
columnas = [info[1] for info in cursor.fetchall()]

print(f"Columnas actuales en atletas: {columnas}")

columnas_a_agregar = []
if "foto_perfil" not in columnas:
    columnas_a_agregar.append("foto_perfil BLOB")
if "fecha_comienzo" not in columnas:
    columnas_a_agregar.append("fecha_comienzo DATE")

for col in columnas_a_agregar:
    try:
        print(f"Agregando columna: {col}")
        cursor.execute(f"ALTER TABLE atletas ADD COLUMN {col}")
        print(f"Columna {col} agregada exitosamente.")
    except Exception as e:
        print(f"Error al agregar columna {col}: {e}")

conn.commit()
conn.close()
print("Operación finalizada.")
