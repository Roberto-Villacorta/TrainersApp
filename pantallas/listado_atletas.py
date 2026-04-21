import customtkinter as ctk
import io
from PIL import Image, ImageDraw, ImageFont
from bbdd.database import SessionLocal
from logica.atletas_service import AtletasService
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
        
        # Frame Listado (Scrollable)
        self.frame_lista = ctk.CTkScrollableFrame(self)
        self.frame_lista.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Render inicial
        self.imagenes_cargadas = {}
        self.renderizar_lista()

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

    def crear_avatar_por_defecto(self, nombre):
        img = Image.new('RGB', (80, 80), color=(100, 100, 150))
        d = ImageDraw.Draw(img)
        letra = nombre[0].upper() if nombre else "?"
        # Como no tenemos una fuente cargada fácilmente accesible en todos los sistemas, usamos la default y ajustamos:
        # Nota: Idealmente se usaría ImageFont.truetype()
        d.text((30, 25), letra, fill=(255, 255, 255))
        return img

    def renderizar_lista(self):
        # Limpiar
        for widget in self.frame_lista.winfo_children():
            widget.destroy()
        
        with SessionLocal() as session:
            service = AtletasService(session)
            estado_req = "inactivo" if self.viendo_inactivos else "activo"
            atletas = service.obtener_atletas(estado=estado_req)
            
        if not atletas:
            msg = "No hay atletas inactivos." if self.viendo_inactivos else "No hay atletas activos. ¡Registra tú primer cliente!"
            ctk.CTkLabel(self.frame_lista, text=msg, font=ctk.CTkFont(size=16)).pack(pady=40)
            return
            
        for atleta in atletas:
            card = ctk.CTkFrame(self.frame_lista, cursor="hand2")
            card.pack(fill="x", pady=5, padx=5)
            
            # Hacer que hacer click en la tarjeta o sus hijos abra la ficha
            # Hay que vincular a los hijos también
            for event_target in [card]: # lo asociaremos a target y a cada hijo abajo
                pass
                
            # Avatar
            img = None
            if atleta.foto_perfil:
                try:
                    img = Image.open(io.BytesIO(atleta.foto_perfil))
                    img = img.resize((60, 60))
                except:
                    img = self.crear_avatar_por_defecto(atleta.nombre_completo)
            else:
                img = self.crear_avatar_por_defecto(atleta.nombre_completo)
                
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(60, 60))
            # Guardamos referencia para evitar GC
            self.imagenes_cargadas[atleta.id] = ctk_img
            
            lbl_img = ctk.CTkLabel(card, image=ctk_img, text="")
            lbl_img.pack(side="left", padx=15, pady=10)
            
            # Datos
            frame_nombres = ctk.CTkFrame(card, fg_color="transparent")
            frame_nombres.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            lbl_nombre = ctk.CTkLabel(frame_nombres, text=atleta.nombre_completo, font=ctk.CTkFont(size=18, weight="bold"))
            lbl_nombre.pack(anchor="w")
            
            str_fecha = atleta.fecha_comienzo.strftime('%d/%m/%Y') if atleta.fecha_comienzo else "Sin asignar"
            lbl_fecha = ctk.CTkLabel(frame_nombres, text=f"Comienzo del proceso: {str_fecha}", text_color="gray")
            lbl_fecha.pack(anchor="w")
            
            # Switch de reactivacion cuando es inactivo
            if self.viendo_inactivos:
                var_switch = ctk.IntVar(value=0)
                switch = ctk.CTkSwitch(card, text="Reactivar", variable=var_switch, 
                                       command=lambda id_atl=atleta.id: self.alternar_estado_atleta(id_atl, "activo"))
                switch.pack(side="right", padx=20)
            
            # Bind de clic
            def abrir_ficha(evento, id_atleta=atleta.id):
                app = self.winfo_toplevel()
                if hasattr(app, "mostrar_ficha_atleta"):
                    app.mostrar_ficha_atleta(id_atleta)
                    
            card.bind("<Button-1>", abrir_ficha)
            lbl_img.bind("<Button-1>", abrir_ficha)
            frame_nombres.bind("<Button-1>", abrir_ficha)
            lbl_nombre.bind("<Button-1>", abrir_ficha)
            lbl_fecha.bind("<Button-1>", abrir_ficha)
