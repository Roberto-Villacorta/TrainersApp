# TrainersApp

Aplicación de escritorio profesional desarrollada en **Python + CustomTkinter** diseñada para entrenadores personales. Permite digitalizar entrenamientos, realizar un seguimiento exhaustivo de atletas mediante Inteligencia Artificial y gestionar el control de pagos y suscripciones de forma automatizada.

---

## Tabla de contenidos

1. [Descripción](#descripción)
2. [Estructura del proyecto](#estructura-del-proyecto)
3. [Funcionalidades principales](#funcionalidades-principales)
4. [Stack tecnológico](#stack-tecnológico)
5. [Instalación y puesta en marcha](#instalación-y-puesta-en-marcha)
6. [Módulo de IA y Escaneo](#módulo-de-ia-y-escaneo)
7. [Control de Pagos y Suscripciones](#control-de-pagos-y-suscripciones)
8. [Ayuda y Guía de Uso](#ayuda-y-guía-de-uso)

---

## Descripción

TrainersApp centraliza la gestión de un centro de entrenamiento personal reduciendo la carga administrativa mediante:

- **Digitalización Inteligente**: Escaneo de libretas manuscritas usando modelos VLM (Vision-Language Models) locales.
- **Control de Suscripciones**: Gestión automatizada de pagos cada 3 meses con avisos preventivos al iniciar la aplicación.
- **Análisis de Progreso por IA**: Los reportes semanales son analizados por una IA (GLiNER) para detectar alertas de fatiga, estrés o estancamiento.
- **Ficha del Atleta 360°**: Historial completo de entrenamientos, comparativas gráficas de métricas y acceso rápido a nuevas sesiones.

---

## Estructura del proyecto

El proyecto ha sido optimizado para contener únicamente los archivos esenciales de producción:

```
TrainersApp/
├── main.py                    # Punto de entrada de la aplicación
├── requirements.txt           # Dependencias Python
├── GUIA_DE_USO.md             # Manual de usuario simplificado para no técnicos
│
├── logica/                    # Capa de lógica de negocio y servicios
│   ├── ia_service.py          # Análisis de texto NER (GLiNER)
│   ├── vlm_service.py         # Escaneo de imágenes (Vision AI)
│   ├── atletas_service.py     # Gestión de atletas y suscripciones
│   ├── rutinas_service.py     # Persistencia y lógica de entrenamientos
│   └── stats_service.py       # Procesamiento de métricas para gráficos
│
├── pantallas/                 # Vistas CustomTkinter (Interfaz)
│   ├── dashboard.py           # Resumen general y calendario
│   ├── listado_atletas.py     # Gestión de la cartera de clientes
│   ├── ficha_atleta.py        # Perfil detallado y reportes IA
│   ├── carga_rutinas.py       # Interfaz de escaneo VLM
│   └── sesion_manual.py       # Carga manual optimizada de ejercicios
│
├── utils/                     # Herramientas auxiliares
│   ├── dialogos_ayuda.py      # Sistema de ayuda con ventanas grandes
│   ├── dialogo_calendario.py  # Selector de fecha visual
│   └── logger.py              # Registro de eventos y errores
│
├── bbdd/                      # Modelos SQLAlchemy (SQLite)
├── datos_locales/             # Carpeta de base de datos y configuración
└── modelos_vlm/               # Pesos de los modelos de IA (locales)
```

---

## Funcionalidades principales

### Páginas de la aplicación

| Página | Descripción |
|---|---|
| **Dashboard** | Resumen de atletas activos, formularios pendientes y calendario de llamadas/pagos interactivo. |
| **Listado de Atletas** | Gestión de clientes activos e inactivos, con reactivación automática y control de deudas. |
| **Ficha Individual** | Gráficos Matplotlib comparativos, alertas de IA basadas en reportes y acceso al historial de sesiones. |
| **Carga Manual** | Interfaz optimizada para añadir entrenamientos por mesociclo/semana con series dinámicas y soporte de cardio. |
| **Escaneo VLM** | Uso de IA de visión local para "leer" fotos de libretas y digitalizarlas automáticamente (Requiere GPU). |

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Interfaz gráfica | `customtkinter` (Moderna, modo oscuro/claro) |
| Base de datos | `SQLAlchemy` + SQLite (Local y privada) |
| IA de Visión | `transformers` + `qwen2_vl` (Procesamiento VLM local) |
| IA de Texto | `gliner` (Extracción de entidades en reportes) |
| Gráficos | `matplotlib` (Integración nativa en la UI) |
| Exportación | `pandas` + `openpyxl` (Generación de Excel) |

---

## Instalación y puesta en marcha

### 1. Requisitos previos
- Python 3.10 o superior.
- **Opcional pero recomendado**: Tarjeta gráfica NVIDIA (8GB+ VRAM) para usar el escaneo de fotos por IA.

### 2. Instalación
```bash
# Crear y activar entorno
python -m venv .venv
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Ejecución
```bash
python main.py
```

---

## Control de Pagos y Suscripciones

El sistema implementa una lógica de negocio estricta para asegurar la rentabilidad del entrenador:
- **Ciclos de 3 meses**: Los pagos se renuevan automáticamente cada 90 días.
- **Avisos al iniciar**: Al abrir la app, se detectan atletas con pagos vencidos y se pregunta al entrenador si han pagado.
- **Gestión de Inactivos**: Si un atleta no paga, es movido a la lista de inactivos automáticamente.
- **Reactivación**: Al reactivar a un atleta, se le asigna una nueva fecha de comienzo y el ciclo de 3 meses se reinicia.

---

## Ayuda y Guía de Uso

Para facilitar el uso a personas no familiarizadas con la tecnología:
- **Heurísticas de Nielsen**: El diseño previene errores, ofrece visibilidad del estado del sistema y permite una navegación intuitiva.
- **Ayuda Contextual**: Todas las pantallas tienen un botón **"?"** que abre una ventana grande con instrucciones paso a paso en lenguaje sencillo.
- **Manual Simplificado**: Consulta el archivo `GUIA_DE_USO.md` para una explicación detallada escrita para "todos los públicos".
