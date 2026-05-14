import customtkinter as ctk
import calendar
from datetime import datetime, date

class DialogoSeleccionarFecha(ctk.CTkToplevel):
    def __init__(self, master, al_seleccionar_callback, fecha_inicial=None):
        super().__init__(master)
        self.title("Seleccionar Fecha")
        self.geometry("350x400")
        self.al_seleccionar_callback = al_seleccionar_callback
        
        # Hazlo modal
        self.transient(master.winfo_toplevel())
        self.after(100, self.grab_set)
        
        ahora = fecha_inicial if isinstance(fecha_inicial, date) else datetime.now().date()
        self.current_year = ahora.year
        self.current_month = ahora.month
        
        # Título
        self.lbl_title = ctk.CTkLabel(self, text="Elija una Fecha", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_title.pack(pady=10)
        
        # Controles
        self.frame_controles = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_controles.pack(fill="x", padx=20, pady=5)
        
        self.btn_prev = ctk.CTkButton(self.frame_controles, text="<", width=30, command=self.mes_anterior)
        self.btn_prev.pack(side="left")
        
        self.lbl_mes_anio = ctk.CTkLabel(self.frame_controles, text="", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_mes_anio.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(self.frame_controles, text=">", width=30, command=self.mes_siguiente)
        self.btn_next.pack(side="right")
        
        # Grid
        self.frame_grid_calendario = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_grid_calendario.pack(fill="both", expand=True, padx=20, pady=10)
        
        dias = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]
        for i, dia in enumerate(dias):
            lbl_dia = ctk.CTkLabel(self.frame_grid_calendario, text=dia, font=ctk.CTkFont(weight="bold"))
            lbl_dia.grid(row=0, column=i, padx=2, pady=5, sticky="nsew")
            self.frame_grid_calendario.grid_columnconfigure(i, weight=1)
            
        self.dias_botones = []
        self.actualizar_calendario()
        
    def actualizar_calendario(self):
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.lbl_mes_anio.configure(text=f"{meses[self.current_month-1]} {self.current_year}")
        
        for btn in self.dias_botones:
            btn.destroy()
        self.dias_botones.clear()
        
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        
        for row, semana in enumerate(cal):
            for col, dia in enumerate(semana):
                if dia != 0:
                    btn_dia = ctk.CTkButton(
                        self.frame_grid_calendario, 
                        text=str(dia), 
                        fg_color=("gray80", "gray25"), 
                        text_color=("black", "white"),
                        hover_color=("gray70", "gray35"),
                        width=30, height=30,
                        command=lambda d=dia: self.seleccionar(d)
                    )
                    btn_dia.grid(row=row+1, column=col, padx=2, pady=2, sticky="nsew")
                    self.dias_botones.append(btn_dia)

    def mes_anterior(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.actualizar_calendario()

    def mes_siguiente(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.actualizar_calendario()
        
    def seleccionar(self, dia):
        fecha_seleccionada = date(self.current_year, self.current_month, dia)
        self.al_seleccionar_callback(fecha_seleccionada)
        self.destroy()
