import os
import sys
import logging
logging.basicConfig(level=logging.INFO)

from logica.vlm_service import VLMService

def run():
    vlm = VLMService.get_instance()
    image_path = r"C:\Users\fitne\Downloads\photo_2026-04-21_15-29-23.jpg"
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return
        
    print(f"Processing image: {image_path}")
    res = vlm.procesar_imagen_rutina(image_path)
    print("Final result:")
    print(res)

if __name__ == "__main__":
    run()
