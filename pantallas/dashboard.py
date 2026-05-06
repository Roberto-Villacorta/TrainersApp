import customtkinter as ctk
import calendar
import threading
import queue
from datetime import datetime
from bbdd.database import SessionLocal
from logica.dashboard_service import DashboardService
from utils.logger import app_logger

class DialogoGestionLlamadas(ctk.CTkToplevel):
    def __init__(self, master_dashboard, dia, fecha_llamada, llamadas):
        super().__init__(master_dashboard)
        self.title(f"Llamadas del {dia}/{fecha_llamada.month}/{fecha_llamada.year}")
        self.geometry("450x400")
        self.master_dashboard = master_dashboard
        self.fecha_llamada = fecha_llamada
        self.llamadas = llamadas
        
        # Hazlo modal
        self.transient(master_dashboard.winfo_toplevel())
        self.after(100, self.grab_set)

        self.lbl_titulo = ctk.CTkLabel(self, text=f"Llamadas Programadas", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_titulo.pack(pady=10)

        self.frame_lista = ctk.CTkScrollableFrame(self)
        self.frame_lista.pack(fill="both", expand=True, padx=10, pady=10)

        self.renderizar_lista()

        self.btn_nueva = ctk.CTkButton(self, text="+ Añadir nueva llamada", command=self.agregar_nueva)
        self.btn_nueva.pack(pady=10)

    def renderizar_lista(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        if not self.llamadas:
            lbl = ctk.CTkLabel(self.frame_lista, text="No hay llamadas para este día.")
            lbl.pack(pady=20)
            return

        for ll in self.llamadas:
            frame_item = ctk.CTkFrame(self.frame_lista)
            frame_item.pack(fill="x", pady=5, padx=5)
            
            lbl_nombre = ctk.CTkLabel(frame_item, text=ll["nombre"], font=ctk.CTkFont(weight="bold"))
            lbl_nombre.pack(side="left", padx=10)
            
            btn_borrar = ctk.CTkButton(frame_item, text="Borrar", width=50, fg_color="#c25757", hover_color="#a14242", 
                                       command=lambda id_ll=ll["id"]: self.borrar_llamada(id_ll))
            btn_borrar.pack(side="right", padx=5, pady=5)
            
            btn_editar = ctk.CTkButton(frame_item, text="Editar", width=50, 
                                       command=lambda id_ll=ll["id"], nom=ll["nombre"]: self.editar_llamada(id_ll, nom))
            btn_editar.pack(side="right", padx=5, pady=5)

    def borrar_llamada(self, id_ll):
        from tkinter import messagebox
        if messagebox.askyesno("Borrar Llamada", "¿Estás seguro de que quieres borrar esta llamada específica?"):
            with SessionLocal() as session:
                ds = DashboardService(session)
                if ds.eliminar_llamada_por_id(id_ll):
                    app_logger.info(f"Llamada {id_ll} eliminada individualmente.")
            self.llamadas = [ll for ll in self.llamadas if ll["id"] != id_ll]
            self.renderizar_lista()
            self.master_dashboard.actualizar_calendario()

    def editar_llamada(self, id_ll, nombre_actual):
        dialog = ctk.CTkInputDialog(text="Nuevo nombre para la llamada:", title="Editar Llamada")
        nuevo_nombre = dialog.get_input()
        if nuevo_nombre and nuevo_nombre != nombre_actual:
            with SessionLocal() as session:
                ds = DashboardService(session)
                if ds.actualizar_llamada(id_ll, nuevo_nombre):
                    app_logger.info(f"Llamada {id_ll} actualizada a {nuevo_nombre}.")
            for ll in self.llamadas:
                if ll["id"] == id_ll:
                    ll["nombre"] = nuevo_nombre
            self.renderizar_lista()
            self.master_dashboard.actualizar_calendario()

    def agregar_nueva(self):
        dialog = ctk.CTkInputDialog(text="Nombre de la nueva llamada:", title="Añadir Llamada")
        nombre = dialog.get_input()
        if nombre:
            with SessionLocal() as session:
                ds = DashboardService(session)
                if ds.agregar_llamada(nombre, self.fecha_llamada):
                    app_logger.info(f"Nueva llamada agregada desde diálogo múltiple: {nombre}")
            with SessionLocal() as session:
                ds = DashboardService(session)
                nuevas_llamadas = ds.obtener_llamadas_mes(self.fecha_llamada.year, self.fecha_llamada.month)
                self.llamadas = [{"id": ll.id, "nombre": ll.nombre} for ll in nuevas_llamadas if ll.fecha.day == self.fecha_llamada.day]
            self.renderizar_lista()
            self.master_dashboard.actualizar_calendario()

class Dashboard(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        # Para que el scroll vertical funcione bien en toda la pantalla
        super().__init__(master, **kwargs)
        
        # Obtener datos reales de la base de datos
        with SessionLocal() as session:
            dashboard_service = DashboardService(session)
            metricas = dashboard_service.obtener_metricas_dashboard()
        
        # ==========================================
        # 1. ATLETAS (Arriba)
        # ==========================================
        self.frame_atletas = ctk.CTkFrame(self, corner_radius=15)
        self.frame_atletas.pack(fill="x", padx=20, pady=(20, 10))
        
        self.btn_help = ctk.CTkButton(self.frame_atletas, text="?", width=30, height=30, corner_radius=15,
                                      fg_color="gray", hover_color="gray50", command=self.mostrar_ayuda)
        self.btn_help.place(relx=0.97, rely=0.1, anchor="ne")
        
        self.lbl_titulo_atletas = ctk.CTkLabel(self.frame_atletas, text="Atletas Activos", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_titulo_atletas.pack(pady=(20, 5))
        
        self.lbl_num_atletas = ctk.CTkLabel(self.frame_atletas, text=str(metricas["atletas_activos"]), font=ctk.CTkFont(size=64, weight="bold"), text_color="#1f6aa5")
        self.lbl_num_atletas.pack(pady=(5, 20))
        
        # ==========================================
        # 2. FORMULARIOS PENDIENTES (Medio)
        # ==========================================
        self.frame_formularios = ctk.CTkFrame(self, corner_radius=15)
        self.frame_formularios.pack(fill="x", padx=20, pady=10)
        
        self.lbl_titulo_forms = ctk.CTkLabel(self.frame_formularios, text="Formularios Pendientes", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_titulo_forms.pack(pady=(20, 5))
        
        self.lbl_num_forms = ctk.CTkLabel(self.frame_formularios, text=str(metricas["formularios_pendientes"]), font=ctk.CTkFont(size=64, weight="bold"), text_color="#c25757")
        self.lbl_num_forms.pack(pady=(5, 20))
        
        # ==========================================
        # 3. CALENDARIO DE LLAMADAS (Abajo)
        # ==========================================
        self.frame_calendario_main = ctk.CTkFrame(self, corner_radius=15)
        self.frame_calendario_main.pack(fill="x", padx=20, pady=(10, 20))
        
        self.lbl_titulo_cal = ctk.CTkLabel(self.frame_calendario_main, text="Calendario de reservas y fechas de pago", font=ctk.CTkFont(size=24, weight="bold"))
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
        # Caché de llamadas y suscripciones del mes visible
        self._cache_llamadas: dict = {}
        self._cache_suscripciones: dict = {}
        # Cola para comunicación de métricas
        self.cola_metricas = queue.Queue()
        self.verificar_cola_metricas()

        self.actualizar_calendario()

    def verificar_cola_metricas(self):
        """Monitorea la cola de métricas."""
        try:
            while True:
                metricas = self.cola_metricas.get_nowait()
                self.lbl_num_atletas.configure(text=str(metricas["atletas_activos"]))
                self.lbl_num_forms.configure(text=str(metricas["formularios_pendientes"]))
        except queue.Empty:
            pass
        finally:
            self.after(150, self.verificar_cola_metricas)

    def mostrar_ayuda(self):
        from tkinter import messagebox
        msg = ("Bienvenido al Dashboard.\n\n"
               "- Atletas Activos: Muestra el total de clientes vigentes.\n"
               "- Formularios Pendientes: Te avisa cuántos atletas deben rellenar su reporte.\n"
               "- Calendario: Gestiona tus llamadas y ve fechas de pago.\n"
               "  - Azul: Llamadas programadas.\n"
               "  - Verde: Renovaciones/Pagos.\n"
               "  - Naranja: Ambos eventos el mismo día.\n"
               "Haz clic en un día para añadir o editar llamadas.")
        messagebox.showinfo("Ayuda: Dashboard", msg)

    def actualizar_dashboard(self):
        """Refresca métricas y calendario lanzando la consulta en un hilo secundario."""
        threading.Thread(target=self._cargar_metricas, daemon=True).start()
        # Forzar invalidación de caché de calendario para que se recarguen los datos
        self._cache_cal = None
        self.actualizar_calendario()

    def _cargar_metricas(self):
        """Consulta métricas en segundo plano y actualiza los labels en el hilo principal."""
        with SessionLocal() as session:
            metricas = DashboardService(session).obtener_metricas_dashboard()
        self.cola_metricas.put(metricas)

    def actualizar_calendario(self):
        """Reconstruye el grid del calendario de forma síncrona con un swap atómico.
        Las consultas SQLite de un mes son instantáneas; threading solo añadía complejidad."""
        # Capturar scroll antes de cualquier cambio en la UI
        scroll_y = self._parent_canvas.yview()[0] if hasattr(self, "_parent_canvas") else 0.0

        meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                 "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
        self.lbl_mes_anio.configure(text=f"{meses[self.current_month-1]} {self.current_year}")

        # Consultar datos del mes en un solo paso optimizado
        with SessionLocal() as session:
            ds = DashboardService(session)
            datos_mes = ds.obtener_datos_calendario(self.current_year, self.current_month)

        self._construir_botones_calendario(datos_mes, scroll_y)

    def _construir_botones_calendario(self, datos_mes: dict, scroll_y: float = 0.0):
        """Sustituye los botones del calendario de forma atómica."""
        self._cache_cal_datos = datos_mes

        # 1. Ocultar el grid mientras se hace la sustitución
        self.frame_grid_calendario.pack_forget()

        # 2. Destruir botones del mes anterior
        for btn in self.dias_botones:
            btn.destroy()
        self.dias_botones.clear()

        # 3. Construir todos los botones del mes nuevo (el grid no es visible aún)
        cal = calendar.monthcalendar(self.current_year, self.current_month)

        for row, semana in enumerate(cal):
            for col, dia in enumerate(semana):
                if dia != 0:
                    info_dia = datos_mes.get(dia, {"llamadas": [], "renovaciones": []})
                    llamadas = info_dia["llamadas"]
                    renovaciones = info_dia["renovaciones"]

                    texto_boton = str(dia)
                    color_fondo = ("gray80", "gray25")
                    color_hover = ("gray70", "gray35")

                    if llamadas or renovaciones:
                        nombres = [ll["nombre"] for ll in llamadas]
                        nombres += [f"💸 {n}" for n in renovaciones]
                        texto_boton += "\n" + "\n".join(nombres)

                        tiene_llamada = bool(llamadas)
                        tiene_pago    = bool(renovaciones)
                        
                        if tiene_pago and not tiene_llamada:
                            color_fondo, color_hover = ("#2e8c4a", "#1b5e20"), ("#3ba359", "#2e7d32")
                        elif tiene_llamada and not tiene_pago:
                            color_fondo, color_hover = ("#4a90e2", "#2b5c8f"), ("#357abd", "#1d4066")
                        else:
                            color_fondo, color_hover = ("#a06917", "#8c5607"), ("#b87f28", "#ab6c14")

                    btn_dia = ctk.CTkButton(
                        self.frame_grid_calendario,
                        text=texto_boton,
                        fg_color=color_fondo,
                        text_color=("black", "white"),
                        hover_color=color_hover,
                        height=60,
                        command=lambda d=dia, l_dia=llamadas: self.abrir_dialogo_llamada(d, l_dia)
                    )
                    btn_dia.grid(row=row + 1, column=col, padx=2, pady=2, sticky="nsew")
                    self.dias_botones.append(btn_dia)

        # 4. Mostrar el grid completo de una sola vez
        self.frame_grid_calendario.pack(fill="both", expand=True, padx=20, pady=20)

        # 5. Restaurar posición de scroll tras volver a mostrar el frame
        if scroll_y > 0.0 and hasattr(self, "_parent_canvas"):
            def _restaurar_scroll():
                self.update_idletasks()
                self._parent_canvas.yview_moveto(scroll_y)
            self.after(30, _restaurar_scroll)

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
        
    def abrir_dialogo_llamada(self, dia, llamadas_del_dia):
        fecha_llamada = datetime(self.current_year, self.current_month, dia).date()

        if llamadas_del_dia:
            # Abrir el diálogo avanzado si hay llamadas
            DialogoGestionLlamadas(self, dia, fecha_llamada, llamadas_del_dia)
            return

        # Comportamiento si no hay llamadas
        dialog = ctk.CTkInputDialog(text=f"Agendar la llamada para el {dia}/{self.current_month}/{self.current_year}:", title="Nueva Llamada")
        llamada = dialog.get_input()
        if llamada:
            with SessionLocal() as session:
                ds = DashboardService(session)
                if ds.agregar_llamada(llamada, fecha_llamada):
                    app_logger.info(f"Llamada guardada en BBDD (y meses siguientes): '{llamada}' el {dia}/{self.current_month}/{self.current_year}")
            
            # Refrescar el calendario para que se muestre la nueva llamada
            self.actualizar_calendario()# ==========================================
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
