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
                # El formato de ej depende de si viene de Gliner o de la BBDD
                # Normalizamos para el Excel
                df_data.append({
                    "Ejercicio": ej.get("nombre_ejercicio") or ej.get("texto") or "Desconocido",
                    "Series": ej.get("series", ""),
                    "Repeticiones": ej.get("repeticiones", ""),
                    "Peso (kg)": ej.get("peso_objetivo") or ej.get("peso_kg", ""),
                    "Descanso": ej.get("tiempo_descanso", ""),
                    "Sesión/Día": ej.get("dia_sesion", "")
                })
                
            df = pd.DataFrame(df_data)
            
            # Crear el Excel con un diseño limpio
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Rutina')
                
                # Ajustar ancho de columnas (opcional pero profesional)
                worksheet = writer.sheets['Rutina']
                for idx, col in enumerate(df.columns):
                    max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.column_dimensions[chr(65 + idx)].width = max_len

            logger.info("Exportación completada.")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando a Excel: {str(e)}")
            return False
