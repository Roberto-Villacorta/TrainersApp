import customtkinter as ctk
import io
from PIL import Image, ImageDraw
from bbdd.database import SessionLocal
from logica.atletas_service import AtletasService

class FichaAtleta(ctk.CTkFrame):
    def __init__(self, master, master_app, **kwargs):
        super().__init__(master, **kwargs)
        self.master_app = master_app
        self.id_atleta_actual = None
        self.imagen_cargada = None

        # Frame Superior (Botones y Cabecera)
        self.frame_cabecera = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_cabecera.pack(side="top", fill="x", pady=10, padx=20)
        
        self.btn_volver = ctk.CTkButton(self.frame_cabecera, text="← Volver a Atletas", width=140, fg_color="gray", hover_color="gray50", command=self.volver_al_listado)
        self.btn_volver.pack(side="left")
        
        # Frame Perfil
        self.frame_perfil = ctk.CTkFrame(self)
        self.frame_perfil.pack(fill="x", padx=20, pady=20)
        
        self.lbl_foto = ctk.CTkLabel(self.frame_perfil, text="")
        self.lbl_foto.pack(side="left", padx=20, pady=20)
        
        self.lbl_nombre = ctk.CTkLabel(self.frame_perfil, text="", font=ctk.CTkFont(size=28, weight="bold"))
        self.lbl_nombre.pack(side="left", padx=10, pady=20)
        
        # Frame Contenido Adicional (Placeholder por ahora)
        self.frame_contenido = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frame_contenido.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.lbl_info = ctk.CTkLabel(self.frame_contenido, text="Estructura base de la ficha.\nEl resto del diseño será integrado posteriormente.", font=ctk.CTkFont(size=14, slant="italic"))
        self.lbl_info.pack(expand=True, pady=40)

    def crear_avatar_por_defecto(self, nombre):
        img = Image.new('RGB', (100, 100), color=(100, 100, 150))
        d = ImageDraw.Draw(img)
        letra = nombre[0].upper() if nombre else "?"
        d.text((40, 40), letra, fill=(255, 255, 255))
        return img

    def cargar_atleta(self, id_atleta):
        self.id_atleta_actual = id_atleta
        with SessionLocal() as session:
            service = AtletasService(session)
            atleta = service.obtener_atleta_por_id(id_atleta)
            
            if not atleta:
                self.lbl_nombre.configure(text="Atleta no encontrado")
                return
                
            self.lbl_nombre.configure(text=atleta.nombre_completo)
            
            img = None
            if atleta.foto_perfil:
                try:
                    img = Image.open(io.BytesIO(atleta.foto_perfil))
                    img = img.resize((100, 100))
                except:
                    img = self.crear_avatar_por_defecto(atleta.nombre_completo)
            else:
                img = self.crear_avatar_por_defecto(atleta.nombre_completo)
                
            self.imagen_cargada = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
            self.lbl_foto.configure(image=self.imagen_cargada)
            
    def volver_al_listado(self):
        if hasattr(self.master_app, "mostrar_pantalla"):
            self.master_app.mostrar_pantalla("atletas")
