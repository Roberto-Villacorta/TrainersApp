import customtkinter as ctk
import sys
from bbdd.crear_tablas import iniciar_base_datos
from pantallas.dashboard import Dashboard
from pantallas.listado_atletas import ListadoAtletas
from pantallas.carga_rutinas import CargaRutinas
from pantallas.ficha_atleta import FichaAtleta

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
        
        # 2. Instanciar Listado de Atletas
        self.pantallas["atletas"] = ListadoAtletas(self.contenedor_principal, fg_color="transparent")
        
        # 3. Instanciar Carga de Archivos
        self.pantallas["archivos"] = CargaRutinas(self.contenedor_principal, fg_color="transparent")
        
        # 4. Instanciar Ficha Atleta
        self.pantallas["ficha_atleta"] = FichaAtleta(self.contenedor_principal, master_app=self, fg_color="transparent")
        
        # Mostrar el dashboard por defecto al iniciar la app
        self.pantalla_actual = "dashboard"
        self.mostrar_pantalla("dashboard")
        
        # Bindings globales para permitir scroll con la rueda del ratón en cualquier parte de la app
        self.bind_all("<Button-4>", self._on_mousewheel)
        self.bind_all("<Button-5>", self._on_mousewheel)
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def _on_mousewheel(self, event):
        # Forzar el evento de scroll directamente sobre el canvas interno de CustomTkinter
        # para que funcione sin importar si el ratón está encima de una tarjeta o etiqueta
        if hasattr(self, "pantalla_actual") and self.pantalla_actual in self.pantallas:
            pantalla = self.pantallas[self.pantalla_actual]
            if hasattr(pantalla, "_parent_canvas"):
                delta = 0
                if sys.platform == "darwin" or sys.platform == "apple":
                    delta = int(-1 * event.delta)
                elif sys.platform == "win32":
                    delta = int(-1 * (event.delta / 120))
                else:
                    if event.num == 4:
                        delta = -1
                    elif event.num == 5:
                        delta = 1
                
                self._iniciar_animacion_scroll(pantalla._parent_canvas, delta)

    def _iniciar_animacion_scroll(self, canvas, delta):
        if delta == 0:
            return
            
        bbox = canvas.bbox("all")
        if not bbox: return
        altura_total = bbox[3] - bbox[1]
        
        # Evitamos cálculos irreales si el canvas no tiene altura
        if altura_total == 0: return

        # Regulamos los píxeles (100 pixeles de altura por cada clickcito en la rueda)
        pixeles_por_scroll = 100 * delta
        fraccion_total = pixeles_por_scroll / altura_total
        
        pasos = 15
        fraccion_por_paso = fraccion_total / pasos
        
        def animar(paso):
            if paso < pasos:
                pos_actual = canvas.yview()[0]
                nuevo_y = pos_actual + fraccion_por_paso
                
                if nuevo_y < 0.0: nuevo_y = 0.0
                if nuevo_y > 1.0: nuevo_y = 1.0
                
                canvas.yview_moveto(nuevo_y)
                self.after(10, animar, paso + 1)
                
        animar(0)

    def mostrar_ficha_atleta(self, id_atleta):
        self.pantallas["ficha_atleta"].cargar_atleta(id_atleta)
        self.mostrar_pantalla("ficha_atleta")
        
    def mostrar_pantalla(self, nombre_pantalla):
        # Si venimos a la pantalla de atletas, refrescar por si hay cambios
        if nombre_pantalla == "atletas" and hasattr(self.pantallas["atletas"], "renderizar_lista"):
            self.pantallas["atletas"].renderizar_lista()
            
        # Si volvemos al dashboard, refrescar las metricas y el calendario
        if nombre_pantalla == "dashboard" and hasattr(self.pantallas["dashboard"], "actualizar_dashboard"):
            self.pantallas["dashboard"].actualizar_dashboard()
            
        self.pantalla_actual = nombre_pantalla
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
