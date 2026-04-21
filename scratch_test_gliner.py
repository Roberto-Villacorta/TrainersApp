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
    # Formato tabular con rango "num-num" como intervalo de trabajo
    "Ejercicio\tRango\tSerie 1\tSerie 2\tSerie 3\n"
    "Dom\t30\t5 x 30\t4 x 30\t4 x 30\n"
    "Remo\t10-12\t11 x 110\t10 x 110\t\n"
    "P. Incl\t5-8\t7 x 90\t5 x 90\t5 x 90\n"
    "P. Plano\t12-15\t14 x 46\t14 x 46\t\n"
    "Elev. Lat\t12-15\t15 x 20\t15 x 20\t13 x 20\n"
    "Pajaro\t15-18\t18 x 20\t18 x 20\t16 x 20\n"
    "Curl Predic\t8-10\t10 x 37,5\t8 x 37,5\t8 x 37,5\n"
    "Exten. Tras\t8-10\t10 x 80\t10 x 80\t10 x 80",
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
                print(f"  Modo: PARSER TABULAR ({len(resultados)} ejercicios encontrados)\n")
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
