from gliner import GLiNER
import pandas as pd

class ParserRutinasGLiNER:
    def __init__(self, ruta_modelo="urchade/gliner_multi-v2.1", umbral_confianza=0.5):
        """
        Inicializa el analizador. 
        Nota: "urchade/gliner_multi-v2.1" es ideal porque entiende español perfectamente.
        Para uso 100% offline, descarga el modelo y pasa la ruta de la carpeta local aquí.
        """
        print("Cargando modelo GLiNER (esto puede tardar unos segundos la primera vez)...")
        self.modelo = GLiNER.from_pretrained(ruta_modelo)
        self.umbral_confianza = umbral_confianza
        
        # Estas son las clases/entidades que el modelo buscará en el texto desordenado
        self.etiquetas_a_buscar = [
            "Ejercicio", 
            "Series", 
            "Repeticiones", 
            "Peso", 
            "Descanso"
        ]

    def procesar_texto(self, texto_ocr):
        """
        Pasa el texto del OCR por GLiNER y agrupa los resultados en una lista de diccionarios.
        """
        # 1. El modelo predice y extrae las entidades
        entidades_brutas = self.modelo.predict_entities(
            texto_ocr, 
            self.etiquetas_a_buscar, 
            threshold=self.umbral_confianza
        )

        # 2. Lógica para agrupar las entidades por "fila" o Ejercicio
        rutina_estructurada = []
        ejercicio_actual = {}

        for entidad in entidades_brutas:
            etiqueta = entidad["label"]
            valor = entidad["text"]

            # Si detectamos un nuevo "Ejercicio", guardamos el anterior y empezamos uno nuevo
            if etiqueta == "Ejercicio":
                if ejercicio_actual:
                    rutina_estructurada.append(ejercicio_actual)
                ejercicio_actual = {"Ejercicio": valor}
            else:
                # Si detectamos series, repeticiones, etc., se lo asignamos al ejercicio actual
                # Solo si ya tenemos un ejercicio abierto
                if "Ejercicio" in ejercicio_actual:
                    ejercicio_actual[etiqueta] = valor

        # Asegurarnos de guardar el último bloque detectado
        if ejercicio_actual:
            rutina_estructurada.append(ejercicio_actual)

        return rutina_estructurada

    def obtener_dataframe(self, texto_ocr):
        """
        Convierte la rutina estructurada en un DataFrame de Pandas, 
        listo para exportar a Excel o guardar en SQLite.
        """
        datos = self.procesar_texto(texto_ocr)
        df = pd.DataFrame(datos)
        
        # Ordenamos las columnas para que tengan un sentido lógico si faltan datos
        columnas_esperadas = ["Ejercicio", "Series", "Repeticiones", "Peso", "Descanso"]
        
        # Asegurar que todas las columnas existan, rellenando con NaN si el modelo no las encontró
        for col in columnas_esperadas:
            if col not in df.columns:
                df[col] = None
                
        # Reordenar y limpiar
        df = df[columnas_esperadas]
        df.fillna("No detectado", inplace=True)
        
        return df

# ==========================================
# EJEMPLO DE USO (Puedes probar esto directamente)
# ==========================================
if __name__ == "__main__":
    # Imagina que este es el texto feo y desordenado que te escupió Tesseract OCR
    texto_prueba_ocr = """
    Lunes - Pecho y Triceps
    Press de banca plano 4 x 10-12 con 60kg desc. 90s
    luego hacemos Aperturas con mancuernas 3 series 15 reps
    Extensiones de triceps en polea 4x12 20 kg
    """

    # Instanciamos nuestra clase
    parser = ParserRutinasGLiNER()

    # Procesamos el texto
    print("\n--- Extrayendo datos con GLiNER ---")
    df_resultado = parser.obtener_dataframe(texto_prueba_ocr)
    
    print("\nDataFrame final (Listo para SQLite o Excel):")
    print(df_resultado.to_string())