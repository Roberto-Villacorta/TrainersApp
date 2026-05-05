import sys
import traceback
import pytesseract
sys.path.append(r'c:\Users\fitne\Desktop\Folder 2\TrainersApp')

def test():
    try:
        from logica.procesador_ocr import OCRProcessor
        from logica.ia_service import GlinerService
        import json
        
        # We don't have the user's image path, but we can call the method with an invalid path
        # Actually, let's see if pytesseract.Output is available
        print("pytesseract.Output:", getattr(pytesseract, 'Output', 'NOT FOUND'))
        
    except Exception as e:
        print("Error:")
        traceback.print_exc()

test()
