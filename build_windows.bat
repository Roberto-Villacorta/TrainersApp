@echo off
echo --- Iniciando Proceso de Compilacion para Windows ---

:: 1. Asegurar que las dependencias están instaladas
echo Instalando dependencias desde requirements.txt...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

:: 2. Limpiar compilaciones anteriores
if exist build rd /s /q build
if exist dist rd /s /q dist

:: 3. Ejecutar PyInstaller usando el archivo .spec
echo Ejecutando PyInstaller...
python -m PyInstaller TrainersApp.spec --clean --noconfirm

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [EXITO] La aplicacion se ha compilado correctamente.
    echo El ejecutable esta en: dist\TrainersApp\TrainersApp.exe
    echo.
    echo Ahora puedes abrir Inno Setup y compilar 'installer_script.iss'.
) else (
    echo.
    echo [ERROR] Hubo un problema durante la compilacion.
    echo Revisa los mensajes de error arriba.
    pause
)
