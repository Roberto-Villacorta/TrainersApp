import os
import subprocess
import sys
import platform

def run_command(command):
    print(f"Ejecutando: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line, end="")
    process.wait()
    if process.returncode != 0:
        print(f"Error al ejecutar: {command}")
        return False
    return True

def get_pip_suffix():
    """Detecta si se requiere --break-system-packages (PEP 668)."""
    if platform.system() == "Windows":
        return ""
    
    # En Linux/macOS, si no estamos en un venv, podríamos necesitar el flag
    if not (hasattr(sys, 'real_prefix') or (target := getattr(sys, 'base_prefix', sys.prefix)) != sys.prefix):
        return " --break-system-packages"
    return ""

def main():
    print(f"--- Iniciando Proceso de Compilación ({platform.system()}) ---")

    # 1. Asegurar dependencias
    print("📦 Asegurando dependencias...")
    python_exe = sys.executable
    pip_suffix = get_pip_suffix()
    
    if not run_command(f'"{python_exe}" -m pip install --upgrade pip{pip_suffix}'):
        # Si falla el upgrade de pip, intentamos seguir igual
        pass
        
    if os.path.exists("requirements.txt"):
        if not run_command(f'"{python_exe}" -m pip install -r requirements.txt{pip_suffix}'):
            print("⚠️ Error instalando desde requirements.txt. Intentando continuar...")
    
    if not run_command(f'"{python_exe}" -m pip install pyinstaller{pip_suffix}'):
        return

    # 2. Limpiar compilaciones anteriores
    print("🧹 Limpiando compilaciones anteriores...")
    if os.path.exists("build"):
        import shutil
        try:
            shutil.rmtree("build")
        except:
            pass
    if os.path.exists("dist"):
        import shutil
        try:
            shutil.rmtree("dist")
        except:
            pass

    # 3. Ejecutar PyInstaller
    print("🛠️ Ejecutando PyInstaller...")
    # Aseguramos que usamos el módulo pyinstaller instalado
    if not run_command(f'"{python_exe}" -m PyInstaller TrainersApp.spec --clean --noconfirm'):
        return

    print("\n✅ ¡Proceso completado con éxito!")
    if platform.system() == "Windows":
        print("El ejecutable está en: dist\\TrainersApp\\TrainersApp.exe")
    elif platform.system() == "Darwin":
        print("La aplicación está en: dist/TrainersApp.app")
        print("Si tienes 'create-dmg' instalado, puedes generar el instalador con ./build_macos.sh")
    else:
        print(f"Empaquetado finalizado para {platform.system()}.")

if __name__ == "__main__":
    main()
