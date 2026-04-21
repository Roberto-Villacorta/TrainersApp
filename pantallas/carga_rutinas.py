import customtkinter as ctk

class CargaRutinas(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        # Título de la pantalla
        self.lbl_titulo = ctk.CTkLabel(self, text="Carga de Archivos y Rutinas", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_titulo.grid(row=0, column=0, pady=20, padx=20, sticky="w")
        
        # Contenedor principal de la pantalla
        self.frame_contenido = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_contenido.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        # Placeholder
        self.lbl_info = ctk.CTkLabel(self.frame_contenido, text="Pantalla 'Carga de Rutinas' preparada para desarrollo.\nAquí se podrán arrastrar archivos PDF/Excel o generar rutinas usando la IA.", font=ctk.CTkFont(size=14))
        self.lbl_info.pack(expand=True, pady=40)
