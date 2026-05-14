import pandas as pd
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class ExportadorExcel:
    """
    Clase para exportar datos de rutinas a archivos Excel (.xlsx).
    """
    
    @staticmethod
    def exportar_rutina(ejercicios_lista: list, output_path: str, nombre_atleta: str = "Atleta"):
        """
        Toma una lista de diccionarios (ejercicios) y genera un Excel.
        """
        try:
            if not ejercicios_lista:
                logger.warning("No hay datos para exportar.")
                return False
                
            logger.info(f"Exportando {len(ejercicios_lista)} ejercicios a {output_path}")
            
            # Preparar datos para DataFrame
            df_data = []
            for ej in ejercicios_lista:
                tipo = ej.get("tipo")
                nombre = ej.get("nombre_ejercicio") or ej.get("texto") or "Desconocido"
                
                # Inferencia automática si no viene el tipo (ej: desde IA)
                if not tipo:
                    nombre_norm = nombre.lower()
                    # Palabras clave para Cardio/HIIT
                    if any(x in nombre_norm for x in ["cinta", "bicicleta", "eliptica", "correr", "nadar", "cardio"]):
                        tipo = "cardio"
                    elif any(x in nombre_norm for x in ["hiit", "sprint", "burpee", "jumping jack", "climber"]):
                        tipo = "hiit"
                    else:
                        tipo = "pesas"
                else:
                    tipo = tipo.lower()
                
                reps_tiempo = ej.get("repeticiones", "")
                peso_intensidad = ej.get("peso_objetivo") or ej.get("peso_kg", "")
                descanso = ej.get("tiempo_descanso", "")

                # Limpieza para que no aparezca "None" en el Excel
                if peso_intensidad is None: peso_intensidad = ""
                if descanso is None: descanso = ""

                df_data.append({
                    "Ejercicio": nombre,
                    "Tipo": tipo.capitalize(),
                    "Series": ej.get("series", ""),
                    "Reps / Tiempo": reps_tiempo,
                    "Peso / Intensidad": peso_intensidad,
                    "Descanso": descanso,
                    "Sesión/Día": ej.get("dia_sesion", "")
                })
                
            df = pd.DataFrame(df_data)
            
            # Crear el Excel con un diseño limpio
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Rutina')
                
                # Ajustar ancho de columnas
                worksheet = writer.sheets['Rutina']
                for idx, col in enumerate(df.columns):
                    # Calcular ancho basado en el contenido y el encabezado
                    max_content_len = df[col].astype(str).map(len).max() if not df.empty else 0
                    max_len = max(max_content_len, len(col)) + 2
                    col_letter = chr(65 + idx)
                    worksheet.column_dimensions[col_letter].width = max_len

            logger.info("Exportación completada.")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando a Excel: {str(e)}")
            return False
