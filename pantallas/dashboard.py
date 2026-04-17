import customtkinter as ctk
import calendar
from datetime import datetime

class Dashboard(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        # Para que el scroll vertical funcione bien en toda la pantalla
        super().__init__(master, **kwargs)
        
        # ==========================================
        # 1. ATLETAS (Arriba)
        # ==========================================
        self.frame_atletas = ctk.CTkFrame(self, corner_radius=15)
        self.frame_atletas.pack(fill="x", padx=20, pady=(20, 10))
        
        self.lbl_titulo_atletas = ctk.CTkLabel(self.frame_atletas, text="Atletas Activos", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_titulo_atletas.pack(pady=(20, 5))
        
        self.lbl_num_atletas = ctk.CTkLabel(self.frame_atletas, text="24", font=ctk.CTkFont(size=64, weight="bold"), text_color="#1f6aa5")
        self.lbl_num_atletas.pack(pady=(5, 20))
        
        # ==========================================
        # 2. FORMULARIOS PENDIENTES (Medio)
        # ==========================================
        self.frame_formularios = ctk.CTkFrame(self, corner_radius=15)
        self.frame_formularios.pack(fill="x", padx=20, pady=10)
        
        self.lbl_titulo_forms = ctk.CTkLabel(self.frame_formularios, text="Formularios Pendientes", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_titulo_forms.pack(pady=(20, 5))
        
        self.lbl_num_forms = ctk.CTkLabel(self.frame_formularios, text="7", font=ctk.CTkFont(size=64, weight="bold"), text_color="#c25757")
        self.lbl_num_forms.pack(pady=(5, 20))
        
        # ==========================================
        # 3. CALENDARIO DE LLAMADAS (Abajo)
        # ==========================================
        self.frame_calendario_main = ctk.CTkFrame(self, corner_radius=15)
        self.frame_calendario_main.pack(fill="x", padx=20, pady=(10, 20))
        
        self.lbl_titulo_cal = ctk.CTkLabel(self.frame_calendario_main, text="Calendario de Llamadas", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_titulo_cal.pack(pady=(20, 10))
        
        # Controles del calendario (mes/año)
        now = datetime.now()
        self.current_year = now.year
        self.current_month = now.month
        
        self.frame_controles = ctk.CTkFrame(self.frame_calendario_main, fg_color="transparent")
        self.frame_controles.pack(fill="x", padx=20, pady=5)
        
        self.btn_prev = ctk.CTkButton(self.frame_controles, text="<", width=40, command=self.mes_anterior)
        self.btn_prev.pack(side="left")
        
        self.lbl_mes_anio = ctk.CTkLabel(self.frame_controles, text="", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_mes_anio.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(self.frame_controles, text=">", width=40, command=self.mes_siguiente)
        self.btn_next.pack(side="right")
        
        # Grid del calendario
        self.frame_grid_calendario = ctk.CTkFrame(self.frame_calendario_main, fg_color="transparent")
        self.frame_grid_calendario.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Nombres de los días de la semana
        dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for i, dia in enumerate(dias):
            lbl_dia = ctk.CTkLabel(self.frame_grid_calendario, text=dia, font=ctk.CTkFont(weight="bold"))
            lbl_dia.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            self.frame_grid_calendario.grid_columnconfigure(i, weight=1)
            
        self.dias_botones = []
        self.actualizar_calendario()

    def actualizar_calendario(self):
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.lbl_mes_anio.configure(text=f"{meses[self.current_month-1]} {self.current_year}")
        
        # Limpiar botones del mes anterior visualizado
        for btn in self.dias_botones:
            btn.destroy()
        self.dias_botones.clear()
        
        # Generar matriz del mes (días en 0 significan que pertenecen al mes anterior o siguiente)
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
                        height=60,
                        command=lambda d=dia: self.abrir_dialogo_llamada(d)
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
        
    def abrir_dialogo_llamada(self, dia):
        # Un cuadro de diálogo sencillo para que el entrenador agende la llamada en ese día
        dialog = ctk.CTkInputDialog(text=f"Agendar llamada para el {dia}/{self.current_month}/{self.current_year}:", title="Nueva Llamada")
        llamada = dialog.get_input()
        if llamada:
            print(f"Llamada guardada: '{llamada}' el {dia}/{self.current_month}/{self.current_year}")
            # En el futuro, aquí se guardaría en la base de datos y podríamos cambiar el color del botón
            # o añadir un indicador para que el entrenador vea que hay una llamada ese día.

# ==========================================
# TEST INDIVIDUAL DE LA PANTALLA
# ==========================================
if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.geometry("800x800")
    app.title("Dashboard Preview")
    
    dashboard = Dashboard(app)
    dashboard.pack(fill="both", expand=True)
    
    app.mainloop()
