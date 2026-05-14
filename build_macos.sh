#!/bin/bash

# Script para automatizar la creación del .app y el .dmg en macOS

echo "🚀 Iniciando proceso de creación para macOS..."

# 0. Verificar Sistema Operativo
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: Este script solo puede ejecutarse en macOS."
    echo "Estás en: $OSTYPE"
    exit 1
fi

# 1. Gestionar Entorno Virtual (VENV)
if [ -d ".venv" ]; then
    echo "🌐 Entorno virtual detectado. Activando..."
    source .venv/bin/activate
    PYTHON_CMD="python3"
else
    echo "⚠️ No se detectó carpeta .venv. Se intentará usar el Python del sistema..."
    # Si estamos en un sistema gestionado, necesitamos --break-system-packages
    PYTHON_CMD="python3"
    PIP_EXTRA="--break-system-packages"
fi

# 2. Asegurar dependencias
echo "📦 Asegurando dependencias..."
$PYTHON_CMD -m pip install --upgrade pip $PIP_EXTRA
$PYTHON_CMD -m pip install -r requirements.txt $PIP_EXTRA
$PYTHON_CMD -m pip install pyinstaller $PIP_EXTRA

# 3. Limpiar compilaciones anteriores
echo "🧹 Limpiando carpetas build y dist..."
rm -rf build dist

# 4. Ejecutar PyInstaller
echo "🛠️ Generando el paquete .app con PyInstaller..."
$PYTHON_CMD -m PyInstaller TrainersApp.spec --clean --noconfirm

# 5. Verificar si se creó el .app
if [ -d "dist/TrainersApp.app" ]; then
    echo "✅ TrainersApp.app creado con éxito."
else
    echo "❌ Error: No se pudo crear el archivo .app."
    exit 1
fi

# 6. Intentar crear el .dmg si create-dmg está instalado
if command -v create-dmg &> /dev/null
then
    echo "💾 Creando instalador .dmg..."
    create-dmg \
      --volname "TrainersApp Installer" \
      --window-pos 200 120 \
      --window-size 800 400 \
      --icon-size 100 \
      --icon "TrainersApp.app" 200 190 \
      --hide-extension "TrainersApp.app" \
      --app-drop-link 600 185 \
      "dist/TrainersApp_Installer.dmg" \
      "dist/TrainersApp.app"
    echo "🎉 ¡Listo! El instalador está en: dist/TrainersApp_Installer.dmg"
else
    echo "⚠️ 'create-dmg' no está instalado. Puedes descargar el .app directamente o instalarlo con 'brew install create-dmg' para generar el .dmg."
    echo "📂 La aplicación está disponible en: dist/TrainersApp.app"
fi
