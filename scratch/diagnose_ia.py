from gliner import GLiNER
import logging

logging.basicConfig(level=logging.INFO)
model = GLiNER.from_pretrained('urchade/gliner_multi-v2.1')

# Catálogo simplificado para diagnóstico
labels = [
    "elevaciones laterales", 
    "jalon al pecho", "tiron dominadas", "tiron polea",
    "press plano", "press con mancuernas",
    "peso muerto rumano"
]

test_cases = [
    "un ejercicio de elevlatmanc",
    "un ejercicio de tiron polea pecho",
    "un ejercicio de p pla",
    "un ejercicio de pm rdl",
    "un ejercicio de pressmanc"
]

print("\nDIAGNOSTICO DE SCORES GLINER")
print("="*60)
for text in test_cases:
    entities = model.predict_entities(text, labels)
    print(f"\nFRASE: '{text}'")
    if not entities:
        print("  !!! NO SE DETECTARON ENTIDADES")
    for e in entities:
        print(f"  -> Match: '{e['text']}'")
        print(f"     Etiqueta: {e['label']}")
        print(f"     Confianza: {e['score']:.4f}")
