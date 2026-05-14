# Instrucciones para Crear el Instalador (Inno Setup)

Este archivo detalla cómo generar el archivo `.exe` de instalación para Windows utilizando el script que acabamos de crear.

## 1. Requisitos Previos

1.  **Inno Setup**: Debes tener instalado Inno Setup en Windows. Puedes descargarlo de [jrsoftware.org](https://jrsoftware.org/isdl.php).
2.  **PyInstaller**: Debes haber ejecutado el comando para generar la carpeta `dist`.
    ```bash
    pyinstaller TrainersApp.spec
    ```
    *Asegúrate de que la carpeta `dist/TrainersApp` existe y contiene el archivo `TrainersApp.exe`.*

## 2. Cómo Generar el Instalador

1.  Abre **Inno Setup Compiler**.
2.  Ve a `File` -> `Open` y selecciona el archivo `installer_script.iss`.
3.  (Opcional) Si quieres añadir un icono personalizado:
    - Busca la línea `SetupIconFile=` en el script.
    - Cambia el valor por la ruta de tu archivo `.ico` (ej: `SetupIconFile=utils\icon.ico`).
4.  Presiona el botón **Compile** (icono de play verde) o presiona `Ctrl + F9`.
5.  Inno Setup procesará los archivos y creará una carpeta llamada `installer_output`.
6.  Dentro de esa carpeta encontrarás `TrainersApp_Setup.exe`, que es el instalador final.

## 3. Notas Técnicas

-   **Persistencia**: El programa está configurado para guardar los datos en `%APPDATA%/TrainersApp`. Esto significa que aunque desinstales y vuelvas a instalar, los datos de los atletas no se perderán a menos que borres manualmente esa carpeta.
-   **Modelos de IA**: La primera vez que el usuario use la función de IA, el programa descargará los modelos necesarios. Esto mantiene el tamaño del instalador pequeño (~200MB en lugar de varios GB).
-   **Arquitectura**: El instalador funcionará en sistemas de 64 bits (x64).

---
*Generado por Antigravity para Roberto Villacorta.*
