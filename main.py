import customtkinter as ctk
from bbdd.crear_tablas import iniciar_base_datos
from pantallas.dashboard import Dashboard

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Aplicación para Entrenadores")
        self.geometry("1024x768")
        
        # 1. INICIALIZAR LA BASE DE DATOS
        # Esto llamará a la función crear_tablas que generará la BBDD si no existe
        iniciar_base_datos()
        
        # ==========================================
        # CABECERA DE NAVEGACIÓN
        # ==========================================
        self.frame_cabecera = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.frame_cabecera.pack(side="top", fill="x")
        
        self.btn_dashboard = ctk.CTkButton(self.frame_cabecera, text="Dashboard", fg_color="transparent", text_color=("black", "white"), command=lambda: self.mostrar_pantalla("dashboard"))
        self.btn_dashboard.pack(side="left", padx=10, pady=10)
        
        self.btn_atletas = ctk.CTkButton(self.frame_cabecera, text="Listado de Atletas", fg_color="transparent", text_color=("black", "white"), command=lambda: self.mostrar_pantalla("atletas"))
        self.btn_atletas.pack(side="left", padx=10, pady=10)
        
        self.btn_archivos = ctk.CTkButton(self.frame_cabecera, text="Carga de Archivos", fg_color="transparent", text_color=("black", "white"), command=lambda: self.mostrar_pantalla("archivos"))
        self.btn_archivos.pack(side="left", padx=10, pady=10)
        
        # ==========================================
        # CONTENEDOR PRINCIPAL
        # ==========================================
        # Aquí es donde se cargarán dinámicamente las pantallas
        self.contenedor_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.contenedor_principal.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        # Diccionario para gestionar las pantallas
        self.pantallas = {}
        
        # 1. Instanciar Dashboard (ya implementado)
        self.pantallas["dashboard"] = Dashboard(self.contenedor_principal)
        
        # 2. Instanciar Listado de Atletas (Placeholder por ahora)
        self.pantallas["atletas"] = ctk.CTkFrame(self.contenedor_principal)
        ctk.CTkLabel(self.pantallas["atletas"], text="Pantalla 'Listado de Atletas' en construcción", font=ctk.CTkFont(size=20)).pack(expand=True)
        
        # 3. Instanciar Carga de Archivos (Placeholder por ahora)
        self.pantallas["archivos"] = ctk.CTkFrame(self.contenedor_principal)
        ctk.CTkLabel(self.pantallas["archivos"], text="Pantalla 'Carga de Archivos' en construcción", font=ctk.CTkFont(size=20)).pack(expand=True)
        
        # Mostrar el dashboard por defecto al iniciar la app
        self.mostrar_pantalla("dashboard")
        
    def mostrar_pantalla(self, nombre_pantalla):
        # 1. Ocultar todas las pantallas
        for pantalla in self.pantallas.values():
            pantalla.pack_forget()
            
        # 2. Resaltar el botón activo en la cabecera
        botones = {
            "dashboard": self.btn_dashboard,
            "atletas": self.btn_atletas,
            "archivos": self.btn_archivos
        }
        
        for name, btn in botones.items():
            if name == nombre_pantalla:
                btn.configure(fg_color=("gray75", "gray25")) # Resaltado
            else:
                btn.configure(fg_color="transparent")       # Normal
                
        # 3. Mostrar la pantalla seleccionada
        self.pantallas[nombre_pantalla].pack(fill="both", expand=True)

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    app = MainApp()
    app.mainloop()
