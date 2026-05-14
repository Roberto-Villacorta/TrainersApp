# Guía para Crear el Instalador en macOS (.dmg)

Para generar un instalador de macOS, necesitas realizar el proceso en una computadora con **macOS**, ya que PyInstaller no puede realizar compilación cruzada (no puede crear binarios de Mac desde Windows/Linux).

## 1. Requisitos Previos en Mac

1.  **Python 3.10+**: Instalado en el sistema.
2.  **PyInstaller**: Instalado en tu entorno virtual.
    ```bash
    pip install pyinstaller
    ```
3.  **create-dmg** (Opcional, para el instalador visual):
    ```bash
    brew install create-dmg
    ```

## 2. Paso 1: Generar el paquete .app

Desde la terminal en la raíz del proyecto, ejecuta:

```bash
pyinstaller TrainersApp.spec
```

Esto generará una carpeta `dist/TrainersApp.app`. Esta es la aplicación que ya puede ejecutarse en Mac.

## 3. Paso 2: Crear el archivo .dmg (Instalador)

Existen dos formas principales:

### Opción A: Usando `create-dmg` (Recomendado para un instalador profesional)

Si instalaste `create-dmg` vía Homebrew, ejecuta:

```bash
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
```

### Opción B: Manual (Sin instalar nada extra)

1. Abre **Utilidad de Discos** (Disk Utility) en tu Mac.
2. Ve a `Archivo` -> `Nueva imagen` -> `Imagen de carpeta`.
3. Selecciona la carpeta `dist` o el archivo `.app`.
4. Guárdalo como `.dmg`.

## 4. Notas sobre Seguridad (Gatekeeper)

macOS es muy estricto con las aplicaciones que no vienen de la App Store. Al abrir el `.dmg` o la aplicación por primera vez:

- Es probable que macOS diga que "no se puede abrir porque el desarrollador no está verificado".
- El usuario deberá ir a **Ajustes del Sistema** -> **Privacidad y Seguridad** y hacer clic en **"Abrir de todos modos"**.
- Para evitar esto en el futuro, se requiere una cuenta de Desarrollador de Apple ($99/año) para "firmar" y "notarizar" la aplicación.

## 5. Automatización con GitHub Actions

Si no tienes una Mac física, puedes configurar una **GitHub Action**. GitHub proporciona máquinas virtuales con macOS que pueden ejecutar el comando de PyInstaller y generar el `.dmg` automáticamente cada vez que subas código.

---
*Generado por Antigravity para Roberto Villacorta.*
