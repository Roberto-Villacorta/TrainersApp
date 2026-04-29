# 🏋️ TrainersApp

> Aplicación de escritorio desarrollada en **Python + CustomTkinter** para ayudar a entrenadores personales en el seguimiento de sus atletas. Automatiza la extracción de datos de rutinas de entrenamiento escritas a mano mediante **OCR + IA**, y centraliza el seguimiento semanal en una base de datos local **SQLite**.

---

## 📋 Tabla de contenidos

1. [Descripción](#descripción)
2. [Estructura del proyecto](#estructura-del-proyecto)
3. [Funcionalidades principales](#funcionalidades-principales)
4. [Stack tecnológico](#stack-tecnológico)
5. [Instalación y puesta en marcha](#instalación-y-puesta-en-marcha)
6. [Módulo de IA — ia\_service](#módulo-de-ia--ia_service)
7. [Tests](#tests)
8. [Logs](#logs)
9. [Solución de problemas](#solución-de-problemas)
10. [Notas de desarrollo](#notas-de-desarrollo)

---

## Descripción

TrainersApp reduce el trabajo manual de los entrenadores centralizando:

- 📁 **Seguimiento de atletas** — fichas individuales con historial de formularios semanales.
- 📷 **Procesado automático de rutinas** — el entrenador fotografía el cuaderno y OCR + IA generan datos estructurados listos para comparar y exportar.
- 📊 **Comparativas de progreso y análisis IA** — gráficas generadas con Matplotlib que comparan la evolución semana a semana, con resúmenes automáticos extraídos por GLiNER de las respuestas del atleta.
- 📅 **Calendario de llamadas y formularios pendientes** — recordatorios integrados en el Dashboard cruzando datos de suscripciones, llamadas y el último domingo registrado.

---

## Estructura del proyecto

```
TrainersApp/
├── main.py                    # Punto de entrada de la aplicación
├── requirements.txt           # Dependencias Python
├── conftest.py                # Configuración de pytest (marcadores)
├── scratch_test_gliner.py     # Script de inspección manual de GLiNER
│
├── logica/                    # Capa de lógica de negocio
│   ├── ia_service.py          # Servicio de IA: OCR → expansión → GLiNER
│   ├── ia_form_service.py     # Servicio IA para análisis de formularios (singleton)
│   ├── atletas_service.py     # CRUD de atletas
│   ├── dashboard_service.py   # Datos para el Dashboard
│   ├── exportador.py          # Exportación a Excel / CSV
│   ├── parser_rutinas.py      # Parser auxiliar de rutinas
│   └── procesador_ocr.py      # Interfaz con pytesseract
│
├── pantallas/                 # Vistas CustomTkinter
│   ├── dashboard.py
│   ├── listado_atletas.py
│   ├── ficha_atleta.py        # Formulario semanal + gráficos comparativos
│   └── carga_rutinas.py
│
├── utils/
│   ├── logger.py              # Logger rotativo (consola + archivo)
│   ├── dialogo_calendario.py
│   └── dialogos_atletas.py
│
├── bbdd/                      # Modelos SQLAlchemy y base de datos
├── datos_locales/             # Datos de configuración locales
├── modelos_ia/                # Caché local de modelos HuggingFace (auto-generada)
├── logs/                      # Archivos de log rotativos (auto-generada)
│
└── tests/                     # Suite de tests automatizados (pytest)
    ├── __init__.py
    └── test_ia_service.py     # 131 tests del módulo ia_service
```

---

## Funcionalidades principales

### Páginas de la aplicación

| Página | Descripción |
|---|---|
| **Dashboard** | Nº de atletas activos, formularios pendientes calculados desde el último domingo y calendario interactivo de llamadas/pagos |
| **Listado de Atletas** | Vista completa de la cartera, búsqueda y alta de nuevos atletas |
| **Ficha Individual** | Formulario de 10 preguntas semanales, historial clicable, gráficos comparativos con Matplotlib y alertas automáticas por IA |
| **Carga de Archivos** | El entrenador sube fotos del cuaderno y el sistema procesa automáticamente con OCR + IA |

### Flujo de procesado de rutinas

```
Foto cuaderno ──► pytesseract (OCR) ──► ia_service ──► Datos estructurados
                                              │
                              ┌───────────────┴───────────────┐
                              │ Texto tabular                  │ Texto libre
                              ▼                               ▼
                         Parser directo               GLiNER (NER neuronal)
                         (sin modelo)                 urchade/gliner_multi-v2.1
```

### Formulario semanal del atleta

Cada ficha incluye un formulario de **10 preguntas semanales** guardadas en la base de datos. Al abrirla verás:

- 🤖 **Resumen de IA** — GLiNER analiza las respuestas de texto libre y detecta automáticamente señales de fatiga, dolor, estrés o mejora.
- 📊 **Gráfico comparativo** — Matplotlib visualiza la evolución entre el formulario actual y el anterior (satisfacción, mejora, consumo de alimentos).
- 🗂️ **Historial clicable** — lista de todos los formularios pasados; al hacer clic se abre una vista de sólo lectura con las respuestas exactas de ese día.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Interfaz gráfica | `customtkinter >= 5.2.0` |
| Base de datos | `SQLAlchemy >= 2.0.0` + SQLite |
| OCR | `pytesseract >= 0.3.10` + `Pillow >= 10.0.0` |
| IA / NER | `gliner >= 0.2.3` (modelo `urchade/gliner_multi-v2.1`) |
| Gráficos | `matplotlib >= 3.7.0` |
| Exportación | `pandas >= 2.0.0` + `openpyxl >= 3.1.2` |
| PDF | `pdf2image >= 1.16.3` |
| Tests | `pytest >= 9.0` |
| Logging | `logging` estándar con `RotatingFileHandler` |

---

## Instalación y puesta en marcha

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd TrainersApp
```

### 2. Crear y activar el entorno virtual

```bash
# Crear entorno
python -m venv .venv

# Activar (PowerShell)
.venv\Scripts\activate

# Activar (CMD)
.venv\Scripts\activate.bat
```

> **VS Code:** `Ctrl + Shift + P` → *Python: Select Interpreter* → selecciona `.venv`

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
pip install pytest   # solo si vas a correr los tests
```

### 4. Requisitos del sistema — OCR

Para que el procesamiento de fotos funcione necesitas **Tesseract OCR** instalado en el sistema:

- **Windows:** Descarga el instalador de [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki). Añade la ruta (ej. `C:\Program Files\Tesseract-OCR`) a las variables de entorno (`PATH`).
- **Idiomas:** Se recomienda instalar los datos de entrenamiento para español (`spa`).

> La primera vez que se use el módulo de IA, el modelo GLiNER (`urchade/gliner_multi-v2.1`) se descargará automáticamente en `modelos_ia/` (~200 MB). Las ejecuciones posteriores usan la caché local.

### 5. Lanzar la aplicación

```bash
python main.py
```

---

## Módulo de IA — ia_service

**Ubicación:** `logica/ia_service.py`

Módulo central que extrae datos estructurados de ejercicios a partir de texto OCR. Incluye normalización inteligente mediante Zero-shot Classification y un pipeline de dos niveles.

### Constantes configurables

| Constante | Valor | Descripción |
|---|---|---|
| `MODEL_NAME` | `"urchade/gliner_multi-v2.1"` | Modelo GLiNER en HuggingFace Hub |
| `THRESHOLD_DEFAULT` | `0.4` | Umbral de confianza mínimo para aceptar entidades |
| `MODEL_DIR` | `modelos_ia` | Carpeta local de caché de modelos |

### Clase principal: `GlinerService`

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

### Normalización inteligente — pipeline híbrido de 3 niveles

El sistema resuelve incluso los casos más difíciles de OCR sucio:

| Tipo | Ejemplo |
|---|---|
| Acrónimos y shorthands | `"pm"` → `"Peso Muerto"`, `"rdl"` → `"Peso Muerto Rumano"` |
| Truncamientos extremos | `"p pla"` → `"Press Plano"` |
| Palabras pegadas | `"elevlatmanc"` → `"Elevaciones Laterales"` |
| Artefactos de OCR | `"PM.RDL_3x100"` → `"Peso Muerto Rumano"` |
| Sinónimos y variantes | `"tiron polea pecho"` → `"Jalón Al Pecho"` |

GLiNER actúa como juez semántico, mientras que el **Segmented Safety Net** rescata ejercicios omitidos por la IA mediante búsqueda estructural por fragmentos. El catálogo nativo supera los **100 ejercicios** (pecho, espalda, pierna, hombro, core, etc.).

### ¿Cómo añadir nuevos ejercicios?

1. Añadirlo a `EJERCICIOS_CANONICOS` en `logica/ia_service.py` para que el Smart Matcher lo reconozca.
2. Añadir una entrada en `ABREVIATURAS` si el OCR suele leerlo de forma errónea o truncada.

### Expansión de abreviaturas (`ABREVIATURAS`)

```
"Kckton"    →  "Patada Tríceps"
"Sent bulg" →  "Sentadilla Búlgara"
"Curl bien" →  "Curl Predicador"
"pm rum"    →  "Peso Muerto Rumano"
```

### Detección automática de formato

- **Tabular** (tabs o espacios dobles): parser directo determinístico. Si hay ejercicios desconocidos, se activa el enriquecimiento con IA de forma autónoma.
- **Texto libre**: el modelo GLiNER extrae entidades como `ejercicio`, `series`, `repeticiones`, `peso en kg` y `descanso`.

### Metadatos extraídos

Si el texto contiene una cabecera de planificación, se extraen automáticamente:

| Campo | Ejemplo |
|---|---|
| `mesociclo` | `"9"` |
| `semana` | `"55"` |
| `sesion` | `"71"` o `"P1"` |

### Salida del parser tabular

```json
[
  {
    "ejercicio":      "Press Plano",
    "rango_objetivo": "7-12",
    "series":         [{"reps": 10, "peso_kg": 100.0}, "..."],
    "origen":         "tabla",
    "mesociclo":      "9",
    "semana":         "55",
    "sesion":         "71"
  }
]
```

### Salida de GLiNER (texto libre)

```json
[
  {"tipo": "ejercicio",    "texto": "Press Banca", "confianza": 0.87, "origen": "gliner"},
  {"tipo": "repeticiones", "texto": "10",          "confianza": 0.72, "origen": "gliner"},
  {"tipo": "peso en kg",   "texto": "80",          "confianza": 0.65, "origen": "gliner"}
]
```

---

## Tests

La suite se encuentra en `tests/test_ia_service.py` y cubre **131 casos** organizados en clases:

| Clase | Qué cubre |
|---|---|
| `TestNormalizacion` | `_quitar_acentos`, `_normalizar_texto_base`, `_normalizar_clave_abrev` |
| `TestExpansorAbreviaturas` | Expansión correcta, especificidad, casos borde, diagnóstico |
| `TestDeteccionTabla` | Heurística `_es_tabla` con texto tabular, libre y mixto |
| `TestMetadatos` | `_extraer_metadatos` en varios formatos y casos vacíos |
| `TestParserSerie` | `_parsear_serie`: formatos válidos, coma decimal, malformados |
| `TestNormalizarNombreEjercicio` | Expansión + capitalización, cadenas vacías |
| `TestSplitColumnas` | Split por tabs y espacio doble |
| `TestParserTabular` | Parser completo con fixtures de OCR real |
| `TestGlinerServicePublico` | Métodos públicos sin cargar modelo |
| `TestPreprocesadorTextoLibre` | Conversión NxPESO, segundos, p/mano |
| `TestGlinerServiceIntegracion` | Flujo completo con texto tabular real |
| `TestGlinerServiceModelo` | Tests con modelo neuronal real (`pytest.mark.slow`) |
| `TestExtremeOcrCases` | Casos de estrés extremo: acrónimos, truncamientos y ruido OCR |

### Ejecutar los tests

```bash
# Rápido — sin cargar el modelo GLiNER (~18s)
.venv\Scripts\python -m pytest tests/test_ia_service.py -m "not slow" -v

# Completo — incluye tests con el modelo neuronal
.venv\Scripts\python -m pytest tests/test_ia_service.py -v
```

> Los tests marcados con `@pytest.mark.slow` requieren que el modelo GLiNER esté descargado en `modelos_ia/` o que haya conexión a internet.

### Inspección manual

```bash
python scratch_test_gliner.py
```

---

## Logs

Los logs se guardan en `logs/entrenador_app.log` con rotación automática:

| Destino | Nivel | Detalles |
|---|---|---|
| Consola | `INFO` y superior | — |
| Archivo | `DEBUG` y superior | Máx. 5 MB × 5 archivos de backup |

**Formato:** `YYYY-MM-DD HH:MM:SS - LEVEL - [modulo:linea] - Mensaje`

---

## Solución de problemas

| Problema | Causa | Solución |
|---|---|---|
| No se detectan ejercicios en fotos | Tesseract no instalado o no en PATH | Instalar Tesseract y verificar `tesseract --version` en consola |
| `ModuleNotFoundError` | Entorno virtual no activado | Ejecutar `.venv\Scripts\activate` antes de `python main.py` |
| La IA tarda mucho la primera vez | Descarga del modelo GLiNER | Esperar a que finalice (~200 MB) |
| Caracteres extraños en el OCR | Baja resolución de imagen | Tomar la foto con luz natural y mayor nitidez |

---

## Notas de desarrollo

- Los modelos HuggingFace se descargan en `modelos_ia/` gracias a `HF_HOME`. Esta carpeta **no se sube al repositorio** (ver `.gitignore`).
- El singleton `GlinerService._modelo` no es thread-safe en la carga inicial. Pre-cargarlo con `GlinerService(cargar_modelo_al_inicio=True)` al arrancar la app evita problemas de concurrencia.
- `IAFormService` comparte el singleton del modelo GLiNER con `GlinerService`, por lo que **no recarga el modelo** (~200 MB) en cada formulario guardado.
- El sistema incluye una lógica de **Deduplicación Final** que prefiere el ejercicio más largo y específico en caso de solapamiento (ej. prefiere `"Sentadilla Búlgara"` frente a `"Sentadilla"`).
