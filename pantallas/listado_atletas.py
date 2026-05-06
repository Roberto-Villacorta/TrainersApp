import customtkinter as ctk
import io
import hashlib
import threading
import queue
from PIL import Image, ImageDraw
from bbdd.database import SessionLocal
from logica.atletas_service import AtletasService
from logica.media_service import MediaService
from utils.dialogos_atletas import DialogoRegistrarAtleta, DialogoActualizarAtleta, DialogoBorrarAtleta

class ListadoAtletas(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Frame Superior (Botones)
        self.frame_botones = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botones.pack(side="top", fill="x", pady=(10, 20), padx=20)
        
        self.btn_registrar = ctk.CTkButton(self.frame_botones, text="+ Registrar Atleta", command=self.abrir_registro)
        self.btn_registrar.pack(side="left", padx=(0, 10))
        
        self.btn_actualizar = ctk.CTkButton(self.frame_botones, text="Actualizar Atleta", command=self.abrir_actualizar)
        self.btn_actualizar.pack(side="left", padx=10)
        
        self.btn_borrar = ctk.CTkButton(self.frame_botones, text="Borrar Atleta", fg_color="#c25757", hover_color="#a14242", command=self.abrir_borrar)
        self.btn_borrar.pack(side="left", padx=10)
        
        self.viendo_inactivos = False
        self.btn_toggle_inactivos = ctk.CTkButton(self.frame_botones, text="Ver Inactivos", fg_color="gray", hover_color="gray50", command=self.toggle_inactivos)
        self.btn_toggle_inactivos.pack(side="left", padx=10)
        
        self.btn_help = ctk.CTkButton(self.frame_botones, text="?", width=30, height=30, corner_radius=15,
                                      fg_color="gray", hover_color="gray50", command=self.mostrar_ayuda)
        self.btn_help.pack(side="right", padx=10)
        
        # Frame Listado (Scrollable)
        self.frame_lista = ctk.CTkScrollableFrame(self)
        self.frame_lista.pack(fill="both", expand=True, padx=20, pady=10)

        # Cola para comunicación segura entre hilos
        self.cola_datos = queue.Queue()
        self.verificar_cola()

        self.renderizar_lista()

    def verificar_cola(self):
        """Monitorea la cola para actualizar la UI desde el hilo principal."""
        try:
            while True:
                datos = self.cola_datos.get_nowait()
                self._construir_tarjetas(datos)
        except queue.Empty:
            pass
        finally:
            # Seguir monitoreando (cada 100ms)
            self.after(100, self.verificar_cola)

    def mostrar_ayuda(self):
        from tkinter import messagebox
        msg = ("Gestión de Atletas:\n\n"
               "- Registrar Atleta: Añade un nuevo cliente al sistema.\n"
               "- Actualizar/Borrar: Modifica o elimina datos de atletas existentes.\n"
               "- Ver Inactivos: Alterna entre clientes activos y los que ya no están en el programa.\n"
               "- Ver Ficha: Haz clic sobre cualquier tarjeta de atleta para abrir su perfil detallado.")
        messagebox.showinfo("Ayuda: Listado de Atletas", msg)

    def obtener_atletas_activos(self):
        with SessionLocal() as session:
            service = AtletasService(session)
            return service.obtener_atletas(estado="activo")
            
    def alternar_estado_atleta(self, id_atleta, estado_nuevo):
        with SessionLocal() as session:
            service = AtletasService(session)
            service.cambiar_estado(id_atleta, estado_nuevo)
        self.renderizar_lista()
            
    def toggle_inactivos(self):
        self.viendo_inactivos = not self.viendo_inactivos
        if self.viendo_inactivos:
            self.btn_toggle_inactivos.configure(text="Ver Activos", fg_color="#4a90e2")
        else:
            self.btn_toggle_inactivos.configure(text="Ver Inactivos", fg_color="gray")
        self.renderizar_lista()

    def abrir_registro(self):
        DialogoRegistrarAtleta(self, al_completar_callback=self.renderizar_lista)

    def abrir_actualizar(self):
        atletas = self.obtener_atletas_activos()
        DialogoActualizarAtleta(self, atletas, al_completar_callback=self.renderizar_lista)

    def abrir_borrar(self):
        atletas = self.obtener_atletas_activos()
        DialogoBorrarAtleta(self, atletas, al_completar_callback=self.renderizar_lista)


    def renderizar_lista(self):
        """Consulta la BBDD en hilo secundario y construye las tarjetas en el hilo principal."""
        # Limpiar inmediatamente para dar feedback visual
        for widget in self.frame_lista.winfo_children():
            widget.destroy()
        threading.Thread(target=self._cargar_atletas_en_hilo, daemon=True).start()

    def _cargar_atletas_en_hilo(self):
        """Ejecuta la consulta SQL en segundo plano y devuelve los datos al hilo principal."""
        with SessionLocal() as session:
            service = AtletasService(session)
            estado_req = "inactivo" if self.viendo_inactivos else "activo"
            atletas = service.obtener_atletas(estado=estado_req)
            # Extraemos solo los datos necesarios dentro de la sesión para no arrastrar objetos SQLAlchemy
            datos = [
                {
                    "id": a.id,
                    "nombre": a.nombre_completo,
                    "fecha_comienzo": a.fecha_comienzo,
                    "foto_perfil": a.foto_perfil,
                }
                for a in atletas
            ]
        # Enviamos los datos a la cola para que el hilo principal los procese
        self.cola_datos.put(datos)

    def _construir_tarjetas(self, datos: list):
        """Construye las tarjetas en el hilo principal usando los datos recibidos del hilo secundario."""
        # Limpiar por si algo se añadió mientras esperábamos el hilo
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        if not datos:
            msg = "No hay atletas inactivos." if self.viendo_inactivos else "No hay atletas activos. ¡Registra tu primer cliente!"
            ctk.CTkLabel(self.frame_lista, text=msg, font=ctk.CTkFont(size=16)).pack(pady=40)
            return

        for atleta in datos:
            card = ctk.CTkFrame(self.frame_lista, cursor="hand2")
            card.pack(fill="x", pady=5, padx=5)

            ctk_img = MediaService.obtener_avatar_atleta(atleta["id"], atleta["foto_perfil"], atleta["nombre"])

            lbl_img = ctk.CTkLabel(card, image=ctk_img, text="")
            lbl_img.pack(side="left", padx=15, pady=10)

            frame_nombres = ctk.CTkFrame(card, fg_color="transparent")
            frame_nombres.pack(side="left", fill="both", expand=True, padx=10, pady=10)

            lbl_nombre = ctk.CTkLabel(frame_nombres, text=atleta["nombre"], font=ctk.CTkFont(size=18, weight="bold"))
            lbl_nombre.pack(anchor="w")

            str_fecha = atleta["fecha_comienzo"].strftime('%d/%m/%Y') if atleta["fecha_comienzo"] else "Sin asignar"
            lbl_fecha = ctk.CTkLabel(frame_nombres, text=f"Comienzo del proceso: {str_fecha}", text_color="gray")
            lbl_fecha.pack(anchor="w")

            if self.viendo_inactivos:
                var_switch = ctk.IntVar(value=0)
                switch = ctk.CTkSwitch(
                    card, text="Reactivar", variable=var_switch,
                    command=lambda id_atl=atleta["id"]: self.alternar_estado_atleta(id_atl, "activo")
                )
                switch.pack(side="right", padx=20)

            def abrir_ficha(evento, id_atleta=atleta["id"]):
                app = self.winfo_toplevel()
                if hasattr(app, "mostrar_ficha_atleta"):
                    app.mostrar_ficha_atleta(id_atleta)

            for widget in (card, lbl_img, frame_nombres, lbl_nombre, lbl_fecha):
                widget.bind("<Button-1>", abrir_ficha)
