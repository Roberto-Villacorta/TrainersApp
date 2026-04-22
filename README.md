TrainersApp

Aplicacion de escritorio desarrollada en Python + CustomTkinter para ayudar a entrenadores personales en el seguimiento de sus atletas. Automatiza la extraccion de datos de rutinas de entrenamiento escritas a mano mediante OCR + IA, y centraliza el seguimiento semanal en una base de datos local SQLite.

Tabla de contenidos

1. Descripcion
2. Estructura del proyecto
3. Funcionalidades principales
4. Stack tecnologico
5. Instalacion y puesta en marcha
6. Modulo de IA - ia_service
7. Tests
8. Logs
9. Notas de desarrollo

Descripcion

TrainersApp reduce el trabajo manual de los entrenadores centralizando:

Seguimiento de atletas: fichas individuales con historial de formularios semanales.
Procesado automatico de rutinas: el entrenador fotografía el cuaderno de entrenamiento y OCR e IA generan datos estructurados listos para comparar y exportar.
Comparativas de progreso: graficas y tablas que muestran la evolucion semana a semana, destacando la mejor y peor semana.
Calendario de llamadas: recordatorios integrados en el Dashboard.

Estructura del proyecto

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
    └── test_ia_service.py     # 127 tests del modulo ia_service

Funcionalidades principales

Paginas de la aplicacion

Pagina: Dashboard | Descripcion: Numero de atletas activos, formularios pendientes y calendario de llamadas
Pagina: Listado de atletas | Descripcion: Vista completa de la cartera, busqueda y alta de nuevos atletas
Pagina: Ficha individual | Descripcion: Historial de formularios, carga de rutinas y progreso semanal del atleta
Pagina: Carga de archivos | Descripcion: El entrenador sube fotos del cuaderno; el sistema procesa automaticamente

Flujo de procesado de rutinas

Foto cuaderno ──► pytesseract (OCR) ──► ia_service ──► Datos estructurados
                                              │
                              ┌───────────────┴───────────────┐
                              │ Texto tabular                  │ Texto libre
                              ▼                               ▼
                         Parser directo               GLiNER (NER neuronal)
                         (sin modelo)                 urchade/gliner_multi-v2.1

Stack tecnologico

Capa: Interfaz grafica | Tecnologia: customtkinter >= 5.2.0
Capa: Base de datos | Tecnologia: SQLAlchemy >= 2.0.0 + SQLite
Capa: OCR | Tecnologia: pytesseract >= 0.3.10 + Pillow >= 10.0.0
Capa: IA / NER | Tecnologia: gliner >= 0.2.3 (modelo urchade/gliner_multi-v2.1)
Capa: Exportacion | Tecnologia: pandas >= 2.0.0 + openpyxl >= 3.1.2
Capa: PDF | Tecnologia: pdf2image >= 1.16.3
Capa: Tests | Tecnologia: pytest >= 9.0
Capa: Logging | Tecnologia: logging estandar con RotatingFileHandler

Instalacion y puesta en marcha

1. Clonar el repositorio

git clone <url-del-repo>
cd TrainersApp

2. Crear y activar el entorno virtual

Crear entorno
python -m venv .venv

Activar (PowerShell)
.venv\Scripts\activate

Activar (CMD)
.venv\Scripts\activate.bat

Tip VS Code: Ctrl + Shift + P → Python: Select Interpreter → selecciona .venv

3. Instalar dependencias

pip install -r requirements.txt
pip install pytest   # solo si vas a correr los tests

Requisitos del Sistema (OCR)

Para que el procesamiento de fotos funcione, debes tener instalado Tesseract OCR en tu sistema:

Windows: Descarga el instalador de UB-Mannheim (https://github.com/UB-Mannheim/tesseract/wiki). Asegurate de añadir la ruta (ej: C:\Program Files\Tesseract-OCR) a las variables de entorno (PATH) o configurar pytesseract.pytesseract.tesseract_cmd en el codigo.
Idiomas: Se recomienda instalar los datos de entrenamiento para español (spa).

La primera vez que se use el modulo de IA, el modelo GLiNER (urchade/gliner_multi-v2.1) se descargara automaticamente en modelos_ia/. Requiere conexion a internet (unos 200 MB). Las ejecuciones posteriores usan la cache local.

4. Lanzar la aplicacion

python main.py

Modulo de IA - ia_service
 
Ubicacion: logica/ia_service.py
 
Modulo central que extrae datos estructurados de ejercicios a partir de texto OCR. Ahora incluye normalizacion inteligente mediante Zero-shot Clasificacion y un pipeline de dos niveles.
 
Constantes configurables
 
MODEL_NAME: "urchade/gliner_multi-v2.1" (Modelo GLiNER en HuggingFace Hub)
THRESHOLD_DEFAULT: 0.4 (Umbral de confianza minimo para aceptar entidades)
MODEL_DIR: modelos_ia (Carpeta local de cache de modelos)
 
Clase principal: GlinerService
 
from logica.ia_service import GlinerService
 
serv = GlinerService()
 
Procesar texto de OCR (tabular o libre)
La IA se carga automaticamente si se necesia normalizar algo desconocido
resultados = serv.procesar_texto_rutina(texto_ocr)
 
Procesar con trazabilidad completa (debug / tests)
info = serv.procesar_texto_rutina_debug(texto_ocr)
print(info["modo_detectado"])   # "tabla" | "gliner"
print(info["metadatos"])        # {"mesociclo": "9", "semana": "55", "sesion": "71"}
 
Normalizacion inteligente con Zero-shot y Smart Matcher
 
El sistema ya no depende solo de un diccionario fijo. Usa un motor hibrido de 3 niveles para resolver incluso los casos mas dificiles de OCR sucio:
 
Acronimos y Shorthands: "pm" → "Peso Muerto", "rdl" → "Peso Muerto Rumano"
Truncamientos extremos: "p pla" → "Press Plano"
Palabras pegadas: "elevlatmanc" → "Elevaciones Laterales"
Artefactos de OCR: "PM.RDL_3x100" → "Peso Muerto Rumano"
Sinonimos y variantes: "tiron polea pecho" → "Jalon Al Pecho"
 
Esto permite que el sistema sea extremadamente robusto ante errores de lectura de la camara o abreviaturas personales del atleta. La IA (GLiNER) actua como juez semantico, mientras que un Segmented Safety Net rescata ejercicios omitidos por la IA mediante busqueda estructural por fragmentos.
 
El motor hibrido garantiza un 100% de deteccion en los casos de prueba limite, manejando incluso multiples ejercicios concatenados en una sola linea de texto libre.
 
La aplicacion conoce mas de 100 ejercicios de forma nativa (pecho, espalda, pierna, hombro, core, etc.). Este catalogo se usa como un puente semantico para pasar de texto sucio a datos limpios sin añadir miles de abreviaturas manuales.

¿Como añadir nuevos ejercicios?

Si el sistema no reconoce un ejercicio especifico, puedes:
1. Añadirlo a EJERCICIOS_CANONICOS en logica/ia_service.py para que el Smart Matcher lo reconozca.
2. Añadir una abreviatura en el diccionario ABREVIATURAS si el OCR suele leerlo de forma erronea o truncada.
 
Deteccion automatica de formato
 
Tabular (tabs o espacios dobles): parser directo deterministico. Si hay ejercicios desconocidos, se activa el enriquecimiento con IA de forma autonoma.
Texto libre: el modelo GLiNER extrae entidades como ejercicio, series, repeticiones, peso en kg y descanso.
 
Expansion de abreviaturas (ABREVIATURAS)
 
Diccionario que normaliza formas coloquiales de gym antes de la IA:
 
"Kckton"    →  "Patada Triceps"
"Sent bulg" →  "Sentadilla Bulgara"
"Curl bien" →  "Curl Predicador"
"pm rum"    →  "Peso Muerto Rumano"
 
Metadatos extraidos
 
Si el texto contiene una cabecera de planificacion, se estraen automaticamente:
 
Campo: mesociclo | Ejemplo: "9"
Campo: semana | Ejemplo: "55"
Campo: sesion | Ejemplo: "71" o "P1"
 
Salida del parser tabular
 
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

Salida de GLiNER (texto libre)

[
  {"tipo": "ejercicio",    "texto": "Press Banca",  "confianza": 0.87, "origen": "gliner"},
  {"tipo": "repeticiones", "texto": "10",           "confianza": 0.72, "origen": "gliner"},
  {"tipo": "peso en kg",   "texto": "80",           "confianza": 0.65, "origen": "gliner"},
]

Tests

La suite de tests se encuentra en tests/test_ia_service.py y cubre 127 casos organizados en 10 clases:

Clase: TestNormalizacion | Que cubre: _quitar_acentos, _normalizar_texto_base, _normalizar_clave_abrev
Clase: TestExpansorAbreviaturas | Que cubre: Expansion correcta, especificidad, casos borde, diagnostico
Clase: TestDeteccionTabla | Que cubre: Heuristica _es_tabla con texto tabular, libre y mixto
Clase: TestMetadatos | Que cubre: _extraer_metadatos en varios formatos y casos vacios
Clase: TestParserSerie | Que cubre: _parsear_serie: formatos validos, coma decimal, malformados
Clase: TestNormalizarNombreEjercicio | Que cubre: Expansion + capitalizacion, cadenas vacias
Clase: TestSplitColumnas | Que cubre: Split por tabs y espacio doble
Clase: TestParserTabular | Que cubre: Parser completo con fixtures de OCR real
Clase: TestGlinerServicePublico | Que cubre: Metodos publicos sin cargar modelo
Clase: TestPreprocesadorTextoLibre | Que cubre: Conversion NxPESO, segundos, p/mano
Clase: TestGlinerServiceIntegracion | Que cubre: Flujo completo con texto tavular real
Clase: TestGlinerServiceModelo | Que cubre: Tests con modelo neuronal real (pytest.mark.slow)
Clase: TestExtremeOcrCases | Que cubre: Casos de estres extremo: acronimos, truncamientos y ruido OCR

Ejecutar los tests

Rapido - sin cargar el modelo GLiNER (unos 4s)
pytest tests/test_ia_service.py -m "not slow" -v

Completo - incluye tests con el modelo neuronal
pytest tests/test_ia_service.py -v

Los tests marcados con @pytest.mark.slow requieren que el modelo GLiNER este descargado en modelos_ia/ o que haya conexion a internet.

Inspeccion manual

Para ejecutar una inspeccion visual formateada del modelo con datos reales, usa el script de consola (no es parte de la suite pytest):

python scratch_test_gliner.py

Logs

Los logs de la aplicacion se guardan en logs/entrenador_app.log con rotacion automatica:

Consola: nivel INFO y superior.
Archivo: nivel DEBUG y superior (max. 5 MB por 5 archivos de backup).

Formato: YYYY-MM-DD HH:MM:SS - LEVEL - [modulo:linea] - Mensaje

Solución de Problemas

Problema: No se detectan ejercicios en fotos | Causa: Tesseract no instalado o no en PATH | Solucion: Instalar Tesseract y verificar tesseract --version en consola.
Problema: Error ModuleNotFoundError | Causa: Entorno virtual no activado | Solucion: Ejecutar .venv\Scripts\activate antes de python main.py.
Problema: La IA tarda mucho la primera vez | Causa: Descarga del modelo GLiNER | Solucion: Esperar a que finalice la descarga (aprox. 200MB).
Problema: Caracteres extraños en el OCR | Causa: Baja resolución de imagen | Solucion: Intentar tomar la foto con luz natural y mayor nitidez.

Notas de desarrollo

Los modelos HuggingFace se descargan en modelos_ia/ gracias a HF_HOME. Esta carpeta no se sube al repositorio (ver .gitignore).
El singleton GlinerService._modelo no es thread-safe en la carga inicial. Pre-cargarlo con GlinerService(cargar_modelo_al_inicio=True) al arrancar la app evita problemas de concurrencia.
El sistema incluye una logica de Deduplicacion Final que prefiere el ejercicio mas largo y especifico en caso de solapamiento (ej: prefiere "Sentadilla Bulgara" frente a "Sentadilla").
