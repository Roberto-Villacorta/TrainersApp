import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime
from bbdd.database import SessionLocal
from logica.atletas_service import AtletasService
from logica.rutinas_service import RutinasService
from logica.exportador import ExportadorExcel
from logica.exercise_data import EJERCICIOS_POR_MUSCULO
from utils.logger import app_logger

class SesionManual(ctk.CTkScrollableFrame):
    """
    Pantalla para añadir entrenamientos de forma manual pero cómoda.
    Permite al entrenador introducir ejercicios, series y repeticiones sin usar IA.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        # Título amigable
        self.lbl_titulo = ctk.CTkLabel(self, text="Añadir entrenamiento de tú atleta", font=ctk.CTkFont(size=28, weight="bold"))
        self.lbl_titulo.grid(row=0, column=0, pady=(20, 10), padx=30, sticky="w")
        
        self.lbl_subtitulo = ctk.CTkLabel(self, text="Añade que ha hecho tú atleta en esta sesión.", font=ctk.CTkFont(size=16))
        self.lbl_subtitulo.grid(row=1, column=0, pady=(0, 20), padx=30, sticky="w")
        
        # Botón de ayuda (Heurística: Ayuda y documentación)
        self.btn_help = ctk.CTkButton(self, text="?", width=30, height=30, corner_radius=15,
                                      fg_color="gray", hover_color="gray50", command=self.mostrar_ayuda)
        self.btn_help.place(relx=0.97, rely=0.03, anchor="ne")

        # --- SECCIÓN 1: SELECCIÓN DE ATLETA ---
        self.frame_atleta = ctk.CTkFrame(self)
        self.frame_atleta.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        
        self.lbl_atleta = ctk.CTkLabel(self.frame_atleta, text="Selecciona al Atleta:", font=ctk.CTkFont(weight="bold"))
        self.lbl_atleta.pack(side="left", padx=20, pady=15)
        
        self.combo_atletas = ctk.CTkComboBox(self.frame_atleta, values=["Cargando atletas..."], width=300)
        self.combo_atletas.pack(side="left", padx=10, pady=15)
        
        self.cargar_atletas()

        # --- SECCIÓN 2: DATOS DE LA SESIÓN (Meso, Sem, Sesión) ---
        self.frame_info_sesion = ctk.CTkFrame(self)
        self.frame_info_sesion.grid(row=3, column=0, padx=30, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.frame_info_sesion, text="Mesociclo:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(20, 5), pady=15)
        self.entry_mesociclo = ctk.CTkEntry(self.frame_info_sesion, width=60, placeholder_text="Ej: 1")
        self.entry_mesociclo.pack(side="left", padx=5, pady=15)
        
        ctk.CTkLabel(self.frame_info_sesion, text="Semana:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(15, 5), pady=15)
        self.entry_semana = ctk.CTkEntry(self.frame_info_sesion, width=60, placeholder_text="Ej: 2")
        self.entry_semana.pack(side="left", padx=5, pady=15)
        
        ctk.CTkLabel(self.frame_info_sesion, text="Sesión:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(15, 5), pady=15)
        self.entry_sesion = ctk.CTkEntry(self.frame_info_sesion, width=60, placeholder_text="Ej: 1")
        self.entry_sesion.pack(side="left", padx=5, pady=15)

        # --- SECCIÓN 3: LISTA DE EJERCICIOS ---
        self.lbl_ejercicios = ctk.CTkLabel(self, text="Lista de Ejercicios:", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_ejercicios.grid(row=4, column=0, pady=(20, 5), padx=30, sticky="w")
        
        self.frame_lista_ejercicios = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_lista_ejercicios.grid(row=5, column=0, padx=30, pady=5, sticky="nsew")
        
        self.filas_ejercicios = []
        
        # Añadir la primera fila por defecto
        self.añadir_fila_ejercicio()

        self.btn_añadir_fila = ctk.CTkButton(self, text="+ Añadir otro ejercicio", command=self.añadir_fila_ejercicio, fg_color="#1f6aa5", hover_color="#144870")
        self.btn_añadir_fila.grid(row=6, column=0, padx=30, pady=10, sticky="w")

        # --- SECCIÓN 4: ACCIONES FINALES ---
        self.frame_acciones = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_acciones.grid(row=7, column=0, padx=30, pady=30, sticky="e")
        
        self.btn_exportar = ctk.CTkButton(self.frame_acciones, text="Guardar en Excel", 
                                          command=self.exportar_excel, fg_color="#a06917", hover_color="#8c5607")
        self.btn_exportar.pack(side="left", padx=10)
        
        self.btn_guardar = ctk.CTkButton(self.frame_acciones, text="Guardar en el Programa", 
                                         command=self.confirmar_guardado, fg_color="#2e8c4a", hover_color="#1b5e20")
        self.btn_guardar.pack(side="left", padx=10)

    def cargar_atletas(self):
        try:
            with SessionLocal() as session:
                service = AtletasService(session)
                atletas = service.obtener_atletas(estado="activo")
                if atletas:
                    nombres = [f"{a.id} - {a.nombre_completo}" for a in atletas]
                    self.combo_atletas.configure(values=nombres)
                    self.combo_atletas.set(nombres[0])
                else:
                    self.combo_atletas.configure(values=["No hay atletas activos"])
        except Exception as e:
            app_logger.error(f"Error cargando atletas: {e}")

    def seleccionar_atleta(self, id_atleta):
        """Pre-selecciona un atleta en el combo basándose en su ID."""
        # Asegurarse de que los valores están cargados
        self.cargar_atletas()
        
        valores = self.combo_atletas.cget("values")
        for val in valores:
            if val.startswith(f"{id_atleta} - "):
                self.combo_atletas.set(val)
                break

    def mostrar_ayuda(self):
        msg = ("Guía de Carga Manual:\n\n"
               "- Datos Sesión: Introduce el número de Mesociclo, Semana y Sesión.\n"
               "- Ejercicios: Elige el músculo para filtrar o escribe un nombre personalizado.\n"
               "- Series Dinámicas: Pulsa '+ Serie' para añadir un nuevo set (reps/peso/descanso).\n"
               "- Eliminar Serie: Pulsa la 'x' gris al final de una serie si te equivocas.\n"
               "- Cardio: Si eliges 'Cardio', solo tendrás que poner el tiempo (ej: 20 min).\n"
               "- Guardar: Puedes guardar en la base de datos o generar un Excel.")
        messagebox.showinfo("Ayuda: Carga Manual", msg)

    def añadir_fila_ejercicio(self):
        fila_container = ctk.CTkFrame(self.frame_lista_ejercicios)
        fila_container.pack(fill="x", pady=10, padx=5)
        
        # Fila de control (Músculo, Ejercicio, Botones)
        fila_control = ctk.CTkFrame(fila_container, fg_color="transparent")
        fila_control.pack(fill="x", pady=5, padx=5)
        
        musculos = list(EJERCICIOS_POR_MUSCULO.keys())
        
        combo_musculo = ctk.CTkComboBox(fila_control, values=musculos, width=140, 
                                        command=lambda v: self.actualizar_ejercicios_fila(v, combo_ejercicio, container_series, series_list, cabecera_series))
        combo_musculo.pack(side="left", padx=5)
        
        combo_ejercicio = ctk.CTkComboBox(fila_control, values=["Escribe o elige..."], width=250)
        combo_ejercicio.pack(side="left", padx=5)
        
        btn_mas_serie = ctk.CTkButton(fila_control, text="+ Serie", width=80, fg_color="#2e8c4a", hover_color="#1b5e20",
                                      command=lambda: self.añadir_serie_a_ejercicio(container_series, series_list, es_cardio=(combo_musculo.get()=="Cardio")))
        btn_mas_serie.pack(side="left", padx=10)
        
        btn_borrar_ej = ctk.CTkButton(fila_control, text="Eliminar Ejercicio", width=120, fg_color="#c25757", hover_color="#a14242",
                                      command=lambda: self.borrar_fila(fila_container, data_dict))
        btn_borrar_ej.pack(side="right", padx=5)

        # Contenedor de series
        container_series = ctk.CTkFrame(fila_container, fg_color="transparent")
        container_series.pack(fill="x", pady=5, padx=30)
        
        # Cabecera de series
        cabecera_series = ctk.CTkFrame(container_series, fg_color="transparent")
        cabecera_series.pack(fill="x")
        self.dibujar_cabecera_series(cabecera_series, es_cardio=False)

        series_list = []
        
        # Añadir la primera serie por defecto
        self.añadir_serie_a_ejercicio(container_series, series_list, es_cardio=False)
        
        data_dict = {
            "container": fila_container,
            "musculo": combo_musculo,
            "ejercicio": combo_ejercicio,
            "series_list": series_list,
            "container_series": container_series,
            "cabecera_series": cabecera_series
        }
        self.filas_ejercicios.append(data_dict)

    def dibujar_cabecera_series(self, frame, es_cardio):
        for w in frame.winfo_children(): w.destroy()
        if es_cardio:
            ctk.CTkLabel(frame, text="Tiempo", width=120, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=5)
        else:
            ctk.CTkLabel(frame, text="Reps", width=60, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=5)
            ctk.CTkLabel(frame, text="Peso", width=80, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=5)
            ctk.CTkLabel(frame, text="Descanso", width=80, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=5)

    def añadir_serie_a_ejercicio(self, container, series_list, es_cardio=False):
        f_serie = ctk.CTkFrame(container, fg_color="transparent")
        f_serie.pack(fill="x", pady=2)
        
        serie_data = {"frame": f_serie}
        
        if es_cardio:
            ent_tiempo = ctk.CTkEntry(f_serie, width=120, placeholder_text="20 min")
            ent_tiempo.pack(side="left", padx=5)
            serie_data.update({"tiempo": ent_tiempo, "reps": None, "peso": None, "desc": None})
        else:
            ent_reps = ctk.CTkEntry(f_serie, width=60, placeholder_text="10")
            ent_reps.pack(side="left", padx=5)
            ent_peso = ctk.CTkEntry(f_serie, width=80, placeholder_text="80kg")
            ent_peso.pack(side="left", padx=5)
            ent_desc = ctk.CTkEntry(f_serie, width=80, placeholder_text="90s")
            ent_desc.pack(side="left", padx=5)
            serie_data.update({"reps": ent_reps, "peso": ent_peso, "desc": ent_desc, "tiempo": None})
        
        btn_del = ctk.CTkButton(f_serie, text="x", width=25, height=25, fg_color="#c25757", hover_color="#a14242",
                                command=lambda: self.borrar_serie(f_serie, series_list, serie_data))
        btn_del.pack(side="left", padx=5)
        
        series_list.append(serie_data)

    def borrar_serie(self, frame, series_list, serie_data):
        if len(series_list) > 1:
            frame.destroy()
            series_list.remove(serie_data)
        else:
            messagebox.showwarning("Atención", "Debe haber al menos una serie por ejercicio.")

    def actualizar_ejercicios_fila(self, musculo, combo_ejercicio, container_series, series_list, cabecera_series):
        # Actualizar lista de ejercicios
        ejercicios = EJERCICIOS_POR_MUSCULO.get(musculo, [])
        combo_ejercicio.configure(values=ejercicios)
        if ejercicios:
            combo_ejercicio.set(ejercicios[0])
            
        # Cambiar modo de series si es Cardio
        es_cardio = (musculo == "Cardio")
        self.dibujar_cabecera_series(cabecera_series, es_cardio)
        
        # Limpiar series actuales y añadir una nueva del tipo correcto
        for s in series_list[:]:
            s["frame"].destroy()
        series_list.clear()
        self.añadir_serie_a_ejercicio(container_series, series_list, es_cardio)

    def borrar_fila(self, container, data_dict):
        container.destroy()
        if data_dict in self.filas_ejercicios:
            self.filas_ejercicios.remove(data_dict)

    def recolectar_datos(self):
        ejercicios_finales = []
        for fila in self.filas_ejercicios:
            nombre = fila["ejercicio"].get().strip()
            if nombre and nombre != "Escribe o elige...":
                reps_vals = []
                peso_vals = []
                desc_vals = []
                for s in fila["series_list"]:
                    if s.get("tiempo"):
                        reps_vals.append(s["tiempo"].get().strip() or "0")
                        peso_vals.append("")
                        desc_vals.append("")
                    else:
                        reps_vals.append(s["reps"].get().strip() or "0")
                        peso_vals.append(s["peso"].get().strip() or "0")
                        desc_vals.append(s["desc"].get().strip() or "0")
                
                ejercicios_finales.append({
                    "nombre_ejercicio": nombre,
                    "series": str(len(fila["series_list"])),
                    "repeticiones": ", ".join(reps_vals),
                    "peso_objetivo": ", ".join(peso_vals),
                    "tiempo_descanso": ", ".join(desc_vals)
                })
        return ejercicios_finales

    def confirmar_guardado(self):
        ejercicios = self.recolectar_datos()
        if not ejercicios:
            messagebox.showwarning("Atención", "Configura al menos un ejercicio.")
            return
            
        atleta_str = self.combo_atletas.get()
        if "No hay" in atleta_str or "Cargando" in atleta_str:
            messagebox.showwarning("Atención", "Selecciona un atleta válido.")
            return
            
        atleta_id = int(atleta_str.split(" - ")[0])
        
        meso = self.entry_mesociclo.get().strip()
        sem = self.entry_semana.get().strip()
        ses = self.entry_sesion.get().strip()
        nombre_sesion = f"Meso {meso} - Semana {sem} - Sesión {ses}"
        
        if messagebox.askyesno("Confirmar", f"¿Guardar entrenamiento para {atleta_str.split(' - ')[1]}?"):
            try:
                with SessionLocal() as session:
                    service = RutinasService(session)
                    if service.repo.guardar_rutina_completa(atleta_id, nombre_sesion, ejercicios):
                        messagebox.showinfo("¡Hecho!", "Entrenamiento guardado.")
                        self.limpiar_formulario()
                    else:
                        messagebox.showerror("Error", "No se pudo guardar.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def exportar_excel(self):
        ejercicios = self.recolectar_datos()
        if not ejercicios:
            messagebox.showwarning("Atención", "Configura al menos un ejercicio.")
            return
            
        output_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Documento Excel", "*.xlsx")],
            initialfile=f"Entrenamiento_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
        
        if output_path:
            try:
                if ExportadorExcel.exportar_rutina(ejercicios, output_path):
                    messagebox.showinfo("¡Hecho!", f"Excel creado en:\n{output_path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def limpiar_formulario(self):
        self.entry_mesociclo.delete(0, 'end')
        self.entry_semana.delete(0, 'end')
        self.entry_sesion.delete(0, 'end')
        # Limpiar filas y dejar solo una
        for fila in self.filas_ejercicios[:]:
            self.borrar_fila(fila["container"], fila)
        self.añadir_fila_ejercicio()
