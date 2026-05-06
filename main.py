import customtkinter as ctk
import sys
from bbdd.crear_tablas import iniciar_base_datos
from pantallas.dashboard import Dashboard
from pantallas.listado_atletas import ListadoAtletas
from pantallas.carga_rutinas import CargaRutinas
from pantallas.ficha_atleta import FichaAtleta
from utils.dialogo_calendario import DialogoSeleccionarFecha
from pantallas.sesion_manual import SesionManual


class MainApp(ctk.CTk):
    """
    Ventana raíz de la aplicación TrainersApp.

    Gestiona la navegación entre pantallas (Dashboard, Atletas, Archivos, Ficha)
    mediante un sistema de pila único donde sólo una pantalla es visible en cada
    momento. Todas las pantallas se instancian al arrancar para evitar latencia
    al cambiar de vista.
    """

    def __init__(self):
        super().__init__()

        self.title("Aplicación para Entrenadores")
        self.geometry("1024x768")

        # Inicializar la base de datos SQLite al arrancar.
        # Si no existe, crear_tablas la genera automáticamente.
        iniciar_base_datos()

        # ── Cabecera de navegación ────────────────────────────────────────────
        self.frame_cabecera = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.frame_cabecera.pack(side="top", fill="x")

        self.btn_dashboard = ctk.CTkButton(
            self.frame_cabecera, text="Inicio",
            fg_color="transparent", text_color=("black", "white"),
            command=lambda: self.mostrar_pantalla("dashboard")
        )
        self.btn_dashboard.pack(side="left", padx=10, pady=10)

        self.btn_atletas = ctk.CTkButton(
            self.frame_cabecera, text="Atletas",
            fg_color="transparent", text_color=("black", "white"),
            command=lambda: self.mostrar_pantalla("atletas")
        )
        self.btn_atletas.pack(side="left", padx=10, pady=10)

        self.btn_manual = ctk.CTkButton(
            self.frame_cabecera, text="Añadir Entrenamiento",
            fg_color="transparent", text_color=("black", "white"),
            command=lambda: self.mostrar_pantalla("manual")
        )
        self.btn_manual.pack(side="left", padx=10, pady=10)

        self.btn_archivos = ctk.CTkButton(
            self.frame_cabecera, text="Escanear Libreta (IA)",
            fg_color="transparent", text_color=("black", "white"),
            command=lambda: self.mostrar_pantalla("archivos")
        )
        self.btn_archivos.pack(side="left", padx=10, pady=10)

        # ── Contenedor principal ──────────────────────────────────────────────
        # Frame transparente donde se muestran las pantallas dinámicamente.
        self.contenedor_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.contenedor_principal.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # Registro de todas las pantallas. Se instancian una sola vez aquí
        # y se ocultan/muestran mediante pack_forget / pack.
        self.pantallas = {}
        self.pantallas["dashboard"]    = Dashboard(self.contenedor_principal)
        self.pantallas["atletas"]      = ListadoAtletas(self.contenedor_principal, fg_color="transparent")
        self.pantallas["manual"]       = SesionManual(self.contenedor_principal, fg_color="transparent")
        self.pantallas["archivos"]     = CargaRutinas(self.contenedor_principal, fg_color="transparent")
        self.pantallas["ficha_atleta"] = FichaAtleta(self.contenedor_principal, master_app=self, fg_color="transparent")

        # Arrancar siempre en el Dashboard
        self.pantalla_actual = "dashboard"
        self.mostrar_pantalla("dashboard")
        
        # Verificar pagos al iniciar (Heurística: Prevención de errores / Visibilidad del estado)
        self.after(2000, self.verificar_pagos)

    def verificar_pagos(self):
        """Revisa si hay atletas con suscripciones vencidas y pregunta al usuario."""
        try:
            from bbdd.database import SessionLocal
            from logica.atletas_service import AtletasService
            from tkinter import messagebox
            import datetime
            
            session = SessionLocal()
            service = AtletasService(session)
            vencidas = service.obtener_suscripciones_vencidas()
            
            def procesar_siguiente(index):
                if index >= len(vencidas):
                    session.close()
                    # Al finalizar todo, refrescar dashboard
                    if self.pantalla_actual == "dashboard":
                        self.pantallas["dashboard"].actualizar_dashboard()
                    return
                
                sub = vencidas[index]
                atleta = sub.atleta
                pregunta = f"¿El atleta {atleta.nombre_completo} ha pagado la renovación?\n\n(Fecha límite era: {sub.fecha_renovacion.strftime('%d/%m/%Y')})"
                
                if messagebox.askyesno("Cobro de Suscripción", pregunta):
                    # Si ha pagado, preguntamos DESDE QUÉ FECHA empieza este nuevo periodo
                    def al_seleccionar_fecha(fecha_pago):
                        # Actualizamos la fecha de renovación a 3 meses de la fecha de pago elegida
                        nueva_fecha = fecha_pago + datetime.timedelta(days=90)
                        sub.fecha_renovacion = nueva_fecha
                        session.commit()
                        messagebox.showinfo("Pago Registrado", f"Suscripción de {atleta.nombre_completo} renovada hasta {nueva_fecha.strftime('%d/%m/%Y')}.")
                        procesar_siguiente(index + 1)
                    
                    # Lanzar calendario
                    DialogoSeleccionarFecha(self, al_seleccionar_fecha, fecha_inicial=sub.fecha_renovacion)
                else:
                    # Si no ha pagado, desactivar
                    service.cambiar_estado(atleta.id, "inactivo")
                    messagebox.showwarning("Atleta Desactivado", f"El atleta {atleta.nombre_completo} ha sido marcado como INACTIVO por falta de pago.")
                    procesar_siguiente(index + 1)

            procesar_siguiente(0)
                
        except Exception as e:
            print(f"Error verificando pagos: {e}")

        # Scroll global con la rueda del ratón: se delega al canvas interno
        # de la pantalla activa sin importar sobre qué widget esté el cursor.
        self.bind_all("<Button-4>", self._on_mousewheel)   # Linux scroll-up
        self.bind_all("<Button-5>", self._on_mousewheel)   # Linux scroll-down
        self.bind_all("<MouseWheel>", self._on_mousewheel) # Windows / macOS

        # Aseguramos que al cerrar la ventana se liberen todos los recursos
        # y el proceso de Python termine completamente (sin hilos huérfanos).
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Cierra la ventana y termina el proceso por completo."""
        self.quit()
        self.destroy()
        sys.exit(0)

    def _on_mousewheel(self, event):
        """
        Intercepta el evento de rueda del ratón a nivel global y lo redirige
        al canvas interno de la pantalla activa.
        """
        # Si el evento viene de un diálogo (Toplevel), no hacemos scroll en la pantalla principal
        try:
            if event.widget.winfo_toplevel() != self:
                return
        except:
            return

        if hasattr(self, "pantalla_actual") and self.pantalla_actual in self.pantallas:
            pantalla = self.pantallas[self.pantalla_actual]
            if hasattr(pantalla, "_parent_canvas"):
                delta = 0
                if sys.platform in ("darwin", "apple"):
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
        """
        Realiza un desplazamiento animado del canvas dividiendo el movimiento
        total en ``pasos`` pequeños llamados con ``after()``, lo que produce
        un efecto de inercia suave en lugar de un salto brusco.

        Cada «clic» de rueda desplaza 100 px repartidos en 15 pasos de 10 ms.
        """
        if delta == 0:
            return

        bbox = canvas.bbox("all")
        if not bbox:
            return
        altura_total = bbox[3] - bbox[1]
        if altura_total == 0:
            return

        pixeles_por_scroll = 100 * delta
        fraccion_total     = pixeles_por_scroll / altura_total
        pasos              = 15
        fraccion_por_paso  = fraccion_total / pasos

        def animar(paso):
            if paso < pasos:
                pos_actual = canvas.yview()[0]
                nuevo_y = max(0.0, min(1.0, pos_actual + fraccion_por_paso))
                canvas.yview_moveto(nuevo_y)
                self.after(10, animar, paso + 1)

        animar(0)

    def mostrar_ficha_atleta(self, id_atleta):
        """
        Carga los datos del atleta indicado en la ficha y navega a esa pantalla.
        Llamado desde ListadoAtletas al hacer clic en una tarjeta.
        """
        self.pantallas["ficha_atleta"].cargar_atleta(id_atleta)
        self.mostrar_pantalla("ficha_atleta")

    def ir_a_entrenamiento_manual(self, id_atleta):
        """Navega a la pantalla de sesión manual y pre-selecciona al atleta."""
        self.mostrar_pantalla("manual")
        if hasattr(self.pantallas["manual"], "seleccionar_atleta"):
            self.pantallas["manual"].seleccionar_atleta(id_atleta)

    def mostrar_pantalla(self, nombre_pantalla):
        """
        Cambia la pantalla visible y refresca sus datos antes de mostrarla.

        El refresco previo garantiza que el contenido esté siempre actualizado
        sin necesidad de escuchar eventos de cambio entre módulos. La pantalla
        ``ficha_atleta`` solo se recarga si ya tiene un atleta asignado.
        """
        # Refrescar los datos de la pantalla de destino antes de mostrarla
        if nombre_pantalla == "atletas":
            if hasattr(self.pantallas["atletas"], "renderizar_lista"):
                self.pantallas["atletas"].renderizar_lista()

        elif nombre_pantalla == "dashboard":
            if hasattr(self.pantallas["dashboard"], "actualizar_dashboard"):
                self.pantallas["dashboard"].actualizar_dashboard()

        elif nombre_pantalla == "archivos":
            # Sincronizar el combo de atletas con los datos actuales de la BBDD
            if hasattr(self.pantallas["archivos"], "cargar_atletas"):
                self.pantallas["archivos"].cargar_atletas()

        elif nombre_pantalla == "manual":
            # Sincronizar el combo de atletas con los datos actuales de la BBDD
            if hasattr(self.pantallas["manual"], "cargar_atletas"):
                self.pantallas["manual"].cargar_atletas()

        elif nombre_pantalla == "ficha_atleta":
            # Si ya hay un atleta activo, refrescar por si se guardó un formulario
            # nuevo o se modificaron sus datos desde otro módulo
            atleta_id = getattr(self.pantallas["ficha_atleta"], "id_atleta_actual", None)
            if atleta_id and hasattr(self.pantallas["ficha_atleta"], "cargar_atleta"):
                self.pantallas["ficha_atleta"].cargar_atleta(atleta_id)

        self.pantalla_actual = nombre_pantalla

        # Ocultar todas las pantallas y mostrar solo la seleccionada
        for pantalla in self.pantallas.values():
            pantalla.pack_forget()

        # Resaltar el botón de navegación correspondiente a la pantalla activa
        botones = {
            "dashboard": self.btn_dashboard,
            "atletas":   self.btn_atletas,
            "manual":    self.btn_manual,
            "archivos":  self.btn_archivos,
        }
        for name, btn in botones.items():
            btn.configure(fg_color=("gray75", "gray25") if name == nombre_pantalla else "transparent")

        self.pantallas[nombre_pantalla].pack(fill="both", expand=True)


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = MainApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        # Ctrl+C en terminal: cierre limpio sin traceback
        pass
