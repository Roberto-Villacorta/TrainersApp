import os
import json
import sys

# Añadir el directorio actual al path para poder importar los módulos locales
sys.path.append(os.getcwd())

from logica.vlm_service import VLMService

def test_extraction():
    print("Iniciando test de extracción VLM (Usando VLMService oficial)...")
    
    # Ruta específica proporcionada por el usuario
    image_path = r"C:\Users\fitne\Downloads\photo_2026-04-21_15-29-23.jpg"
    
    if not os.path.exists(image_path):
        print(f"ERROR: No se encontró la imagen en {image_path}")
        return

    print(f"Probando con imagen: {image_path}")
    
    # Obtener instancia del servicio (esto cargará el modelo)
    service = VLMService.get_instance()
    
    print("\n--- EJECUTANDO ANÁLISIS (MÉTODO TRADICIONAL) ---")
    resultado = service.procesar_imagen_rutina(image_path)
    
    print("\n--- RESULTADO DE LA IA ---")
    print(json.dumps(resultado, indent=2))
    
    if resultado.get("ejercicios") and len(resultado["ejercicios"]) > 0:
        print(f"\n¡EXITO! Se han detectado {len(resultado['ejercicios'])} ejercicios.")
    else:
        print("\nFALLO: La IA no ha devuelto ningún ejercicio.")

if __name__ == "__main__":
    test_extraction()
