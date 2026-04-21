import sqlite3

try:
    conn = sqlite3.connect('datos_locales/entrenador_app.db')
    cursor = conn.cursor()
    # Agregar columna a Atletas
    cursor.execute('ALTER TABLE atletas ADD COLUMN foto_perfil BLOB')
    print('Columna foto_perfil agregada a atletas')
    # Eliminar columna en SQLite requiere version 3.35+, lo intentamos
    cursor.execute('ALTER TABLE metricas_corporales DROP COLUMN foto_progreso_ruta')
    print('Columna foto_progreso_ruta eliminada de metricas')
    conn.commit()
except Exception as e:
    print('Error o columna ya modificada: ', e)
finally:
    conn.close()
