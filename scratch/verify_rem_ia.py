from logica.ia_service import GlinerService
import logging

logging.basicConfig(level=logging.INFO)
serv = GlinerService()
texto = "Ejercicio\tRango\tSerie 1\nrem\t6-10\t5x120"
res = serv.procesar_texto_rutina(texto)
print(f"RESULTADO: {res[0]['ejercicio']}")
if res[0]['ejercicio'] == "Remo":
    print("SUCCESS: 'rem' mapped to 'Remo'")
else:
    print(f"FAILURE: 'rem' mapped to '{res[0]['ejercicio']}'")
