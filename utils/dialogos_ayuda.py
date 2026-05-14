import customtkinter as ctk

class DialogoAyuda(ctk.CTkToplevel):
    def __init__(self, master, titulo, mensaje):
        super().__init__(master)
        self.title(titulo)
        self.geometry("600x500")
        
        # Hacerlo modal
        self.transient(master.winfo_toplevel())
        self.after(100, self.grab_set)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Título
        self.lbl_titulo = ctk.CTkLabel(self, text=titulo, font=ctk.CTkFont(size=22, weight="bold"))
        self.lbl_titulo.grid(row=0, column=0, pady=20, padx=20, sticky="w")
        
        # Contenido con Scroll
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        self.lbl_contenido = ctk.CTkLabel(self.scroll, text=mensaje, font=ctk.CTkFont(size=15), 
                                          justify="left", wraplength=520)
        self.lbl_contenido.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Botón Cerrar
        self.btn_cerrar = ctk.CTkButton(self, text="Entendido", command=self.destroy, fg_color="#1f6aa5")
        self.btn_cerrar.grid(row=2, column=0, pady=20)
