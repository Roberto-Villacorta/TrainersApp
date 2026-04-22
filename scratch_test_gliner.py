# -*- coding: utf-8 -*-
"""
Script de INSPECCIÓN MANUAL para GlinerService.

Este script está pensado para ejecutarse de forma interactiva y ver la salida
formateada en consola. NO es parte de la suite de tests automatizados.

Para correr los tests automatizados usa:
    pytest tests/test_ia_service.py -m "not slow" -v   ← sin modelo GLiNER
    pytest tests/test_ia_service.py -v                 ← todos (incluye GLiNER)

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
    # OCR manual imagen 1 (Mesociclo 9, Semana 55, Sesion 71)
    "Mesociclo 9\tSemana 55\tSesion 71\n"
    "Ejercicio\tRango\tSerie 1\tSerie 2\tSerie 3\tSerie 4\n"
    "P. Plan\t7-12\t3x120\t10x100\t9x100\t8x100\n"
    "rem\t6-10\t5x120\t10x110\t9x115\t8x115\n"
    "Mat cont\t11-20\t20x42,5\t19x42,5\t\t\n"
    "T don\t8-10\t10x110\t9x110\t\t\n"
    "Elev lat\t20-25\t27x13,75\t24x13,75\t20x13,75\t\n"
    "Curl bien\t9-14\t15x17,5\t18x17,5\t1x18,75\t8x20\n"
    "Kckton\t12-15\t17x16,11\t17x15,75\t15x18,75\t",

    # OCR manual imagen 2 (Mesociclo 9, Semana 51, Sesion P1)
    "Mesociclo 9\tSemana 51\tSesion P1\n"
    "Ejercicio\tRango\tSerie 1\tSerie 2\tSerie 3\tSerie 4\n"
    "Ext acl\t8-10\t10x40\t10x40\t10x70\t10x47,5\n"
    "Sentadll\t1-3/5-8\t3x120\t3x125\t8x100\t\n"
    "Abductor\t11-20\t20x85\t20x85\t15x85\t8x160\n"
    "Aductor\t20-21\t21x70\t21x70\t21x70\t\n"
    "Gom\t21-30\t30x60\t30x60\t26x30\t\n"
    "Pres millo\t10-12\t8x27\t11x30\t11x30\t",

    # VALIDACIÓN FINAL: 5 CASOS LÍMITE (TRUNCAMIENTOS, RUIDO Y PEQUEÑAS VARIANTES)
    "p pla\t7-12\t3x120\text tri\t10-12\t10x30",
    "PM.RDL_3x100\nB.DIAS_3x80\nEXT.CUERDA_12x15",
    "Ejercicio\tS1\nPressManc\t10x30\nMartilloCont\t15x20",
    "elevlatmanc\t12-15\t15x10\ncurlz\t8-10\t10x40",
    "tiron polea pecho\t8-10\t10x80\nextension de cuadriceps maq\t12-15\t15x60",
    
    # BATERÍA B: CASOS DE ESTRÉS EXTREMOS (FRAGMENTACIÓN Y FALTA DE VOCALES)
    "vuelalat\t15x12\tcur b z\t10x30\tpm-rum/3x100",
    "sntdll blgr\t8-10\t10x60\nhiptrust\t12x100\npress_ban_incl\t10x80",
    "fce pull\t15x20\tr.polea\t10x50\tj.pecho\t12x60",
    "jalon.p.pecho_10x80.0kg",
    "4x12_100kg_press_ban_plano_manc",
    "dominada.neutra.lastre.10kg"
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

# Normalizar entradas: acepta tanto (desc, texto) como texto plano directo
casos_normalizados = []
for c in test_cases:
    if isinstance(c, tuple):
        if len(c) == 2:
            casos_normalizados.append(c)
        else:
            casos_normalizados.append((f"Caso {len(casos_normalizados)+1}", c[0]))
    else:
        casos_normalizados.append((f"Caso {len(casos_normalizados)+1}", c))

for i, (desc, texto) in enumerate(casos_normalizados, 1):
    print("\n" + SEP_MED)
    print(f"  TEST {i}/{len(casos_normalizados)}: {desc}")
    print(SEP_MED)
    # Mostrar el texto completo si es corto, sino preview linea a linea
    lineas = texto.strip().splitlines()
    for linea in lineas[:6]:
        print(f"  | {linea.strip()}")
    if len(lineas) > 6:
        print(f"  | ... ({len(lineas)-6} lineas mas)")
    print()

    try:
        resultados = serv.procesar_texto_rutina(texto)
        if not resultados:
            print("  [WARN] Sin entidades detectadas.")
        else:
            tests_ok += 1
            # Detectar si es salida de parser tabular o de GLiNER
            if resultados and "ejercicio" in resultados[0]:
                # Formato tabular estructurado
                print(f"  Modo: PARSER TABULAR ({len(resultados)} ejercicios encontrados)")
                # Mostrar metadatos si existen
                meta = resultados[0]
                if meta.get("mesociclo") or meta.get("semana") or meta.get("sesion"):
                    print(f"  Mesociclo: {meta.get('mesociclo','—')}  |  Semana: {meta.get('semana','—')}  |  Sesion: {meta.get('sesion','—')}")
                print()
                for ej in resultados:
                    total_extraidos += 1
                    rango = ej['rango_objetivo']
                    if '-' in str(rango):
                        rango_str = f"intervalo {rango} reps"
                    else:
                        rango_str = f"objetivo {rango} reps"
                    print(f"  [EJERCICIO] {ej['ejercicio']}  ({rango_str})")
                    if ej['series']:
                        for s_num, s in enumerate(ej['series'], 1):
                            print(f"             Serie {s_num}: {s['reps']} reps x {s['peso_kg']} kg")
                    else:
                        print("             (sin series detectadas)")
                    print()
            else:
                # Formato GLiNER libre
                print(f"  Modo: GLINER  ({len(resultados)} entidades encontradas)\n")
                for r in resultados:
                    total_extraidos += 1
                    if r['confianza'] >= 0.75:
                        nivel = "[ALTO] "
                    elif r['confianza'] >= 0.5:
                        nivel = "[MEDIO]"
                    else:
                        nivel = "[BAJO] "
                    print(f"  {nivel} [{r['tipo'].upper()}] -> '{r['texto']}' (conf: {r['confianza']})")
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback; traceback.print_exc()


# Actualizar total para el resumen
test_cases = casos_normalizados

print("\n" + SEP)
print("  RESUMEN FINAL")
print(f"  Tests con resultado:     {tests_ok}/{len(test_cases)}")
print(f"  Total entidades totales: {total_extraidos}")
pct = round(tests_ok / len(test_cases) * 100)
print(f"  Tasa de cobertura:       {pct}%")
print(SEP + "\n")
