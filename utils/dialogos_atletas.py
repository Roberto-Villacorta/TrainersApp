import customtkinter as ctk
from tkinter import filedialog, messagebox
import io
from PIL import Image
from bbdd.database import SessionLocal
from logica.atletas_service import AtletasService
from utils.dialogo_calendario import DialogoSeleccionarFecha
from datetime import datetime

class DialogoRegistrarAtleta(ctk.CTkToplevel):
    def __init__(self, master, al_completar_callback):
        super().__init__(master)
        self.title("Registrar Nuevo Atleta")
        self.geometry("450x650")
        self.al_completar_callback = al_completar_callback
        self.foto_bytes = None
        self.fecha_comienzo_seleccionada = None
        
        self.transient(master.winfo_toplevel())
        self.after(100, self.grab_set)
        
        self.lbl_title = ctk.CTkLabel(self, text="Registro de Atleta", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(pady=15)
        
        # Frame desplazable para el formulario
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Campos
        self.entry_nombre = ctk.CTkEntry(self.scroll, placeholder_text="Nombre Completo (Obligatorio)")
        self.entry_nombre.pack(fill="x", pady=5)
        
        self.entry_email = ctk.CTkEntry(self.scroll, placeholder_text="Correo Electrónico (Opcional)")
        self.entry_email.pack(fill="x", pady=5)
        
        self.entry_telefono = ctk.CTkEntry(self.scroll, placeholder_text="Teléfono de contacto (Opcional)")
        self.entry_telefono.pack(fill="x", pady=5)
        
        # Fecha de Comienzo
        self.frame_fecha = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.frame_fecha.pack(fill="x", pady=10)
        self.lbl_fecha = ctk.CTkLabel(self.frame_fecha, text="Sin fecha de inicio (Usará la de alta)")
        self.lbl_fecha.pack(side="left")
        self.btn_fecha = ctk.CTkButton(self.frame_fecha, text="🗓️ Elegir en Calendario", width=140, command=self.pedir_fecha)
        self.btn_fecha.pack(side="right")
        
        # Foto
        self.btn_subir_foto = ctk.CTkButton(self.scroll, text="Seleccionar Foto de Perfil (Opcional)", command=self.seleccionar_foto)
        self.btn_subir_foto.pack(fill="x", pady=10)
        
        self.lbl_foto_status = ctk.CTkLabel(self.scroll, text="Ninguna foto seleccionada")
        self.lbl_foto_status.pack()
        
        self.lbl_obj = ctk.CTkLabel(self.scroll, text="Objetivos de tu atleta:", anchor="w")
        self.lbl_obj.pack(fill="x", pady=(10, 0))
        self.text_objetivos = ctk.CTkTextbox(self.scroll, height=80)
        self.text_objetivos.pack(fill="x", pady=5)
        
        self.lbl_notas = ctk.CTkLabel(self.scroll, text="Notas del Entrenador:", anchor="w")
        self.lbl_notas.pack(fill="x", pady=(10, 0))
        self.text_notas = ctk.CTkTextbox(self.scroll, height=80)
        self.text_notas.pack(fill="x", pady=5)
        
        self.btn_guardar = ctk.CTkButton(self, text="Registrar", command=self.guardar)
        self.btn_guardar.pack(pady=15)

    def seleccionar_foto(self):
        ruta_archivo = filedialog.askopenfilename(
            filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")]
        )
        if ruta_archivo:
            try:
                with open(ruta_archivo, "rb") as f:
                    self.foto_bytes = f.read()
                self.lbl_foto_status.configure(text="Foto seleccionada correctamente ✅")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer la imagen: {e}")
                self.foto_bytes = None

    def pedir_fecha(self):
        def on_fecha_seleccionada(f):
            self.fecha_comienzo_seleccionada = f
            self.lbl_fecha.configure(text=f"Inicio: {f.strftime('%d/%m/%Y')}")
            
        DialogoSeleccionarFecha(self, on_fecha_seleccionada)

    def guardar(self):
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio")
            return
            
        with SessionLocal() as session:
            service = AtletasService(session)
            service.registrar_atleta(
                nombre_completo=nombre,
                fecha_comienzo=self.fecha_comienzo_seleccionada,
                foto_perfil=self.foto_bytes,
                email=self.entry_email.get().strip() or None,
                telefono=self.entry_telefono.get().strip() or None,
                objetivos=self.text_objetivos.get("1.0", "end-1c").strip() or None,
                notas=self.text_notas.get("1.0", "end-1c").strip() or None
            )
            
        self.al_completar_callback()
        self.destroy()

class DialogoActualizarAtleta(ctk.CTkToplevel):
    def __init__(self, master, atletas_activos, al_completar_callback):
        super().__init__(master)
        self.title("Actualizar Atleta")
        self.geometry("450x650")
        self.al_completar_callback = al_completar_callback
        self.atletas = {a.nombre_completo: a for a in atletas_activos}
        self.atleta_seleccionado_id = None
        self.foto_bytes = None
        self.fecha_comienzo_seleccionada = None

        self.transient(master.winfo_toplevel())
        self.after(100, self.grab_set)
        
        self.lbl_title = ctk.CTkLabel(self, text="Actualizar Información", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(pady=15)
        
        self.combo_atletas = ctk.CTkComboBox(self, values=list(self.atletas.keys()), command=self.cargar_datos_atleta)
        self.combo_atletas.pack(fill="x", padx=20, pady=10)
        
        # Frame desplazable
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Campos
        self.entry_nombre = ctk.CTkEntry(self.scroll, placeholder_text="Nombre Completo")
        self.entry_nombre.pack(fill="x", pady=5)
        
        self.entry_email = ctk.CTkEntry(self.scroll, placeholder_text="Correo Electrónico")
        self.entry_email.pack(fill="x", pady=5)
        
        self.entry_telefono = ctk.CTkEntry(self.scroll, placeholder_text="Teléfono")
        self.entry_telefono.pack(fill="x", pady=5)
        
        # Fecha de Comienzo
        self.frame_fecha = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.frame_fecha.pack(fill="x", pady=10)
        self.lbl_fecha = ctk.CTkLabel(self.frame_fecha, text="")
        self.lbl_fecha.pack(side="left")
        self.btn_fecha = ctk.CTkButton(self.frame_fecha, text="🗓️ Cambiar Comienzo", width=140, command=self.pedir_fecha)
        self.btn_fecha.pack(side="right")
        
        self.btn_subir_foto = ctk.CTkButton(self.scroll, text="Cambiar Foto de Perfil", command=self.seleccionar_foto)
        self.btn_subir_foto.pack(fill="x", pady=10)
        
        self.lbl_foto_status = ctk.CTkLabel(self.scroll, text="Ninguna foto nueva seleccionada")
        self.lbl_foto_status.pack()
        
        self.lbl_obj = ctk.CTkLabel(self.scroll, text="Objetivos:", anchor="w")
        self.lbl_obj.pack(fill="x", pady=(10, 0))
        self.text_objetivos = ctk.CTkTextbox(self.scroll, height=80)
        self.text_objetivos.pack(fill="x", pady=5)
        
        self.lbl_notas = ctk.CTkLabel(self.scroll, text="Notas del Entrenador:", anchor="w")
        self.lbl_notas.pack(fill="x", pady=(10, 0))
        self.text_notas = ctk.CTkTextbox(self.scroll, height=80)
        self.text_notas.pack(fill="x", pady=5)
        
        self.btn_guardar = ctk.CTkButton(self, text="Actualizar", command=self.guardar)
        self.btn_guardar.pack(pady=15)
        
        if self.atletas:
            self.combo_atletas.set(list(self.atletas.keys())[0])
            self.cargar_datos_atleta(self.combo_atletas.get())
        else:
            self.combo_atletas.set("No hay atletas")

    def cargar_datos_atleta(self, valor):
        atleta = self.atletas.get(valor)
        if not atleta: return
        self.atleta_seleccionado_id = atleta.id
        
        self.entry_nombre.delete(0, "end")
        self.entry_nombre.insert(0, atleta.nombre_completo or "")
        
        self.entry_email.delete(0, "end")
        self.entry_email.insert(0, atleta.email or "")
        
        self.entry_telefono.delete(0, "end")
        self.entry_telefono.insert(0, atleta.telefono or "")
        
        self.text_objetivos.delete("1.0", "end")
        self.text_objetivos.insert("1.0", atleta.objetivos or "")
        
        self.text_notas.delete("1.0", "end")
        self.text_notas.insert("1.0", atleta.notas_entrenador or "")
        
        self.fecha_comienzo_seleccionada = atleta.fecha_comienzo
        str_fecha = self.fecha_comienzo_seleccionada.strftime('%d/%m/%Y') if self.fecha_comienzo_seleccionada else "Sin fecha asignada"
        self.lbl_fecha.configure(text=f"Inicio: {str_fecha}")
        
        self.foto_bytes = None
        self.lbl_foto_status.configure(text="Manteniendo foto anterior...")

    def pedir_fecha(self):
        def on_fecha_seleccionada(f):
            self.fecha_comienzo_seleccionada = f
            self.lbl_fecha.configure(text=f"Nueva fecha inicio: {f.strftime('%d/%m/%Y')}")
            
        DialogoSeleccionarFecha(self, on_fecha_seleccionada, self.fecha_comienzo_seleccionada)

    def seleccionar_foto(self):
        ruta_archivo = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
        if ruta_archivo:
            try:
                with open(ruta_archivo, "rb") as f:
                    self.foto_bytes = f.read()
                self.lbl_foto_status.configure(text="Foto nueva adjuntada ✅")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer la imagen: {e}")
                self.foto_bytes = None

    def guardar(self):
        if not self.atleta_seleccionado_id: return
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio")
            return
            
        kwargs = {
            "nombre_completo": nombre,
            "email": self.entry_email.get().strip() or None,
            "telefono": self.entry_telefono.get().strip() or None,
            "objetivos": self.text_objetivos.get("1.0", "end-1c").strip() or None,
            "notas_entrenador": self.text_notas.get("1.0", "end-1c").strip() or None,
            "fecha_comienzo": self.fecha_comienzo_seleccionada
        }
        
        if self.foto_bytes is not None:
            kwargs["foto_perfil"] = self.foto_bytes
            
        with SessionLocal() as session:
            service = AtletasService(session)
            service.actualizar_atleta(self.atleta_seleccionado_id, **kwargs)
            
        self.al_completar_callback()
        self.destroy()

class DialogoBorrarAtleta(ctk.CTkToplevel):
    def __init__(self, master, atletas_activos, al_completar_callback):
        super().__init__(master)
        self.title("Borrar/Inactivar Atleta")
        self.geometry("300x200")
        self.al_completar_callback = al_completar_callback
        self.atletas = {a.nombre_completo: a for a in atletas_activos}
        
        self.transient(master.winfo_toplevel())
        self.after(100, self.grab_set)
        
        self.lbl_title = ctk.CTkLabel(self, text="Dar de baja", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(pady=15)
        
        self.combo_atletas = ctk.CTkComboBox(self, values=list(self.atletas.keys()))
        self.combo_atletas.pack(fill="x", padx=20, pady=10)
        
        if self.atletas:
            self.combo_atletas.set(list(self.atletas.keys())[0])
            
        self.btn_borrar = ctk.CTkButton(self, text="Borrar (Inactivar)", command=self.borrar, fg_color="#c25757", hover_color="#a14242")
        self.btn_borrar.pack(pady=15)

    def borrar(self):
        nombre = self.combo_atletas.get()
        atleta = self.atletas.get(nombre)
        if not atleta: return
        
        if messagebox.askyesno("Confirmar", f"¿Seguro que deseas inactivar a {nombre}?"):
            with SessionLocal() as session:
                service = AtletasService(session)
                service.cambiar_estado(atleta.id, "inactivo")
            self.al_completar_callback()
            self.destroy()
