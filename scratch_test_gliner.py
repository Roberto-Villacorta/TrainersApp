# -*- coding: utf-8 -*-
"""
Script de prueba para el GlinerService.
Evalua la precision del modelo con distintos tipos de texto de rutinas de gym.
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from logica.ia_service import GlinerService

# ──────────────────────────────────────────────
# CASOS DE PRUEBA
# ──────────────────────────────────────────────
test_cases = [
    (
        "Texto limpio - formato natural",
        "Press de Banca 4 series de 10 repeticiones con 60kg, descanso de 90 segundos."
    ),
    (
        "Texto caotico - OCR defectuoso con mayusculas mixtas",
        "EJERciI0 3 Sentadillas bUlgAraS 3x12 15kg p/mano 1 min dsc."
    ),
    (
        "Notacion resumida con abreviaturas",
        "Curl biceps barra Z: 4s x 8r (30kg) - 60s descanso"
    ),
    (
        "Multiples ejercicios en bloque",
        "Rutina de hoy:\nPeso muerto 5x5 a 100 kilos. descansa 2 minutos.\nRemo en polea baja 4x10-12 reps 40kg."
    ),
    (
        "Formato lista numerada clasica",
        "1. Sentadilla libre: 5 series x 8 repeticiones, 80 kg. Descanso: 3 min\n"
        "2. Prensa de piernas: 4x15, 120kg. Desc: 90seg\n"
        "3. Extensiones de cuadriceps: 3 series de 12 reps con 40 kilos"
    ),
    (
        "Slang y errores tipograficos",
        "pressbanc 5ser 8rep 70k decnso 2m\n"
        "dominadas asistidas 4x6 lastre 10kg"
    ),
    (
        "Cardio sin pesos",
        "Caminata inclinada 5 series de 3 minutos al 8% de pendiente. Descanso 1 min entre series."
    ),
    (
        "Notas a mano muy informales",
        "hombros - press militar(mancuernas) : 4 tandas de 10-12 rep x 22kg cada mano\n"
        "elevaciones laterales 3x15 con 10kg desc 45 seg"
    ),
]

# ──────────────────────────────────────────────
# EJECUCION
# ──────────────────────────────────────────────
SEP = "=" * 65
SEP_MED = "-" * 65

def nivel_confianza(c):
    if c >= 0.75: return "[ALTO] "
    if c >= 0.5:  return "[MEDIO]"
    return "[BAJO] "

print("\n" + SEP)
print("  TEST SUITE - GlinerService")
print(SEP)
print("  Inicializando modelo...")

serv = GlinerService()

total_extraidos = 0
tests_ok = 0

for i, (desc, texto) in enumerate(test_cases, 1):
    print("\n" + SEP_MED)
    print(f"  TEST {i}/{len(test_cases)}: {desc}")
    print(SEP_MED)
    input_preview = texto[:90].replace("\n", " | ")
    print(f"  Input: {input_preview}{'...' if len(texto) > 90 else ''}")
    print()

    try:
        resultados = serv.procesar_texto_rutina(texto)
        if resultados:
            tests_ok += 1
            for r in resultados:
                total_extraidos += 1
                nivel = nivel_confianza(r['confianza'])
                print(f"  {nivel} [{r['tipo'].upper()}] -> '{r['texto']}' (conf: {r['confianza']})")
        else:
            print("  [WARN] Sin entidades detectadas (por encima del umbral de confianza).")
    except Exception as e:
        print(f"  [ERROR] {e}")

print("\n" + SEP)
print("  RESUMEN FINAL")
print(f"  Tests con resultado:     {tests_ok}/{len(test_cases)}")
print(f"  Total entidades totales: {total_extraidos}")
pct = round(tests_ok / len(test_cases) * 100)
print(f"  Tasa de cobertura:       {pct}%")
print(SEP + "\n")
