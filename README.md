TrainersApp

Aplicacion de escritorio desarrollada en Python + CustomTkinter para ayudar a entrenadores personales en el seguimiento de sus atletas. Automatiza la estraccion de datos de rutinas de entrenamiento escritas a mano mediante OCR + IA, y centraliza el seguimiento semnal en una base de datos local SQLite.

---

Tabla de contenidos

1. Descripcion
2. Estructura del proyecto
3. Funcionalidades principales
4. Stack tecnologico
5. Instalacion y puesta en marcha
6. Modulo de IA - ia_service
7. Tests
8. Logs
9. Notas de desarollo

---

Descripcion

TrainersApp reduce el trabajo manual de los entrenadores centralizando:

- Seguimiento de atletas: fichas individuales con historial de formularios semanales.
- Procesado automatico de rutinas: el entrenador fotografía el cuaderno de entrenamiento y OCR e IA generan datos estructurados listos para comparar y exportar.
- Comparativas de progreso: graficas y tablas que muestran la evolucion semana a semana, destacando la mejor y peor semana.
- Calendario de llamadas: recordatorios integrados en el Dashboard.

---

Estructura del proyecto

```
TrainersApp/
├── main.py                    # Punto de entrada de la aplicacion
├── requirements.txt           # Dependencias Python
├── conftest.py                # Configuracion de pytest (marcadores)
├── scratch_test_gliner.py     # Script de inspeccion manual de GLiNER
│
├── logica/                    # Capa de logica de negocio
│   ├── ia_service.py          # Servicio de IA: OCR → expansion → GLiNER
│   ├── atletas_service.py     # CRUD de atletas
│   ├── dashboard_service.py   # Datos para el Dashboard
│   ├── exportador.py          # Exportacion a Excel / CSV
│   ├── parser_rutinas.py      # Parser auxiliar de rutinas
│   └── procesador_ocr.py      # Interfaz con pytesseract
│
├── pantallas/                 # Vistas CustomTkinter
├── utils/
│   ├── logger.py              # Logger rotativo (consola + archivo)
│   ├── dialogo_calendario.py
│   └── dialogos_atletas.py
│
├── bbdd/                      # Modelos SQLAlchemy y migraciones
├── datos_locales/             # Datos de configuracion y datos locales
├── modelos_ia/                # Cache local de modelos HuggingFace (auto-generada)
├── logs/                      # Archivos de log rotativos (auto-generada)
│
└── tests/                     # Suite de tests automatizados (pytest)
    ├── __init__.py
    └── test_ia_service.py     # 119 tests del modulo ia_service
```

---

Funcionalidades principales

Paginas de la aplicacion

| Pagina | Descripcion |
|---|---|
| Dashboard | Numero de atletas activos, formularios pendientes y calendario de llamadas |
| Listado de atletas | Vista completa de la cartera, busqueda y alta de nuevos atletas |
| Ficha individual | Historial de formularios, carga de rutinas y progreso semanal del atleta |
| Carga de archivos | El entrenador sube fotos del cuaderno; el sistema procesa automaticamente |

Flujo de procesado de rutinas

```
Foto cuaderno ──► pytesseract (OCR) ──► ia_service ──► Datos estructurados
                                              │
                              ┌───────────────┴───────────────┐
                              │ Texto tabular                  │ Texto libre
                              ▼                               ▼
                         Parser directo               GLiNER (NER neuronal)
                         (sin modelo)                 urchade/gliner_multi-v2.1
```

---

Stack tecnologico

| Capa | Tecnologia |
|---|---|
| Interfaz grafica | `customtkinter >= 5.2.0` |
| Base de datos | `SQLAlchemy >= 2.0.0` + SQLite |
| OCR | `pytesseract >= 0.3.10` + `Pillow >= 10.0.0` |
| IA / NER | `gliner >= 0.2.3` (modelo `urchade/gliner_multi-v2.1`) |
| Exportacion | `pandas >= 2.0.0` + `openpyxl >= 3.1.2` |
| PDF | `pdf2image >= 1.16.3` |
| Tests | `pytest >= 9.0` |
| Logging | `logging` estandar con `RotatingFileHandler` |

---

Instalacion y puesta en marcha

1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd TrainersApp
```

2. Crear y activar el entorno virtual

```powershell
# Crear entorno
python -m venv .venv

# Activar (PowerShell)
.venv\Scripts\activate

# Activar (CMD)
.venv\Scripts\activate.bat
```

Tip VS Code: Ctrl + Shift + P → Python: Select Interpreter → selecciona `.venv`

3. Instalar dependencias

```bash
pip install -r requirements.txt
pip install pytest   # solo si vas a correr los tests
```

La primera vez que se use el modulo de IA, el modelo GLiNER (`urchade/gliner_multi-v2.1`) se descargara automaticamente en `modelos_ia/`. Requiere conexion a internet (unos 200 MB). Las ejecuciones posteriores usan la cache local.

4. Lanzar la aplicacion

```bash
python main.py
```

---

Modulo de IA - ia_service

Ubicacion: `logica/ia_service.py`

Modulo central que extrae datos estrucurados de ejercicios a partir de texto OCR.

Constantes configurables

| Constante | Valor por defecto | Descripcion |
|---|---|---|
| `MODEL_NAME` | `"urchade/gliner_multi-v2.1"` | Modelo GLiNER en HuggingFace Hub |
| `THRESHOLD_DEFAULT` | `0.4` | Umbral de confianza minimo para aceptar entidades |
| `MODEL_DIR` | `<raiz>/modelos_ia` | Carpeta local de cache de modelos |

Clase principal: GlinerService

```python
from logica.ia_service import GlinerService

serv = GlinerService()

# Procesar texto de OCR (tabular o libre)
resultados = serv.procesar_texto_rutina(texto_ocr)

# Procesar con trazabilidad completa (debug / tests)
info = serv.procesar_texto_rutina_debug(texto_ocr)
print(info["modo_detectado"])   # "tabla" | "gliner"
print(info["metadatos"])        # {"mesociclo": "9", "semana": "55", "sesion": "71"}
```

Deteccion automatica de formato

- Tabular (tabs o espacios dobles): parser directo deterministico, sin modelo neuronal.
- Texto libre: el modelo GLiNER extrae entidades como ejercicio, series, repeticiones, peso en kg y descanso.

Expansion de abreviaturas (ABREVIATURAS)

Diccionario de unas 100 entradas que normaliza abreviaturas comunes de gym antes de pasar el texto al modelo:

```
"Elev lat"  →  "Elevaciones Laterales"
"Kckton"    →  "Patada Triceps"
"Sent bulg" →  "Sentadilla Bulgara"
"Curl bien" →  "Curl Predicador"
"pm rum"    →  "Peso Muerto Rumano"
```

Metadatos extraidos

Si el texto contiene una cabecera de planificacion, se estraen automaticamente:

| Campo | Ejemplo |
|---|---|
| `mesociclo` | `"9"` |
| `semana` | `"55"` |
| `sesion` | `"71"` o `"P1"` |

Salida del parser tabular

```python
[
  {
    "ejercicio":      "Press Plano",
    "rango_objetivo": "7-12",
    "series":         [{"reps": 10, "peso_kg": 100.0}, ...],
    "origen":         "tabla",
    "mesociclo":      "9",
    "semana":         "55",
    "sesion":         "71"
  },
  ...
]
```

Salida de GLiNER (texto libre)

```python
[
  {"tipo": "ejercicio",    "texto": "Press Banca",  "confianza": 0.87, "origen": "gliner"},
  {"tipo": "repeticiones", "texto": "10",           "confianza": 0.72, "origen": "gliner"},
  {"tipo": "peso en kg",   "texto": "80",           "confianza": 0.65, "origen": "gliner"},
]
```

---

Tests

La suite de tests se encuentra en `tests/test_ia_service.py` y cubre 119 casos organizados en 9 clases:

| Clase | Que cubre |
|---|---|
| `TestNormalizacion` | `_quitar_acentos`, `_normalizar_texto_base`, `_normalizar_clave_abrev` |
| `TestExpansorAbreviaturas` | Expansion correcta, especificidad, casos borde, diagnostico |
| `TestDeteccionTabla` | Heuristica `_es_tabla` con texto tabular, libre y mixto |
| `TestMetadatos` | `_extraer_metadatos` en varios formatos y casos vacios |
| `TestParserSerie` | `_parsear_serie`: formatos validos, coma decimal, malformados |
| `TestNormalizarNombreEjercicio` | Expansion + capitalizacion, cadenas vacias |
| `TestSplitColumnas` | Split por tabs y espacio doble |
| `TestParserTabular` | Parser completo con fixtures de OCR real |
| `TestGlinerServicePublico` | Metodos publicos sin cargar modelo |
| `TestPreprocesadorTextoLibre` | Conversion `NxPESO`, segundos, `p/mano` |
| `TestGlinerServiceIntegracion` | Flujo completo con texto tavular real |
| `TestGlinerServiceModelo` | Tests con modelo neuronal real (pytest.mark.slow) |

Ejecutar los tests

```bash
# Rapido - sin cargar el modelo GLiNER (unos 4s)
pytest tests/test_ia_service.py -m "not slow" -v

# Completo - incluye tests con el modelo neuronal
pytest tests/test_ia_service.py -v
```

Los tests marcados con `@pytest.mark.slow` requieren que el modelo GLiNER este descargado en `modelos_ia/` o que haya conexion a internet.

Inspeccion manual

Para ejecutar una inspeccion visual formateada del modelo con datos reales, usa el script de consola (no es parte de la suite pytest):

```bash
python scratch_test_gliner.py
```

---

Logs

Los logs de la aplicacion se guardan en `logs/entrenador_app.log` con rotacion automatica:

- Consola: nivel `INFO` y superior.
- Archivo: nivel `DEBUG` y superior (max. 5 MB por 5 archivos de backup).

Formato: `YYYY-MM-DD HH:MM:SS - LEVEL - [modulo:linea] - Mensaje`

---

Notas de desarollo

- Los modelos HuggingFace se descargan en `modelos_ia/` gracias a `HF_HOME`. Esta carpeta no se sube al repositorio (ver `.gitignore`).
- El singleton `GlinerService._modelo` no es thread-safe en la carga inicial. Pre-cargarlo con `GlinerService(cargar_modelo_al_inicio=True)` al arrancar la app evita problemas de concurencia.
- La clave `"martillo"` fue intencionalmente excluida del diccionario `ABREVIATURAS` para evitar re-expansion en cadena sobre textos ya parcialmente expandidos (la abreviatura valida es `"mart"`).