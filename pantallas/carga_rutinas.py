import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
from datetime import datetime
from bbdd.database import SessionLocal
from logica.atletas_service import AtletasService
from logica.rutinas_service import RutinasService
from utils.logger import app_logger

class CargaRutinas(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        # Estado local
        self.archivos_seleccionados = []
        self.ejercicios_procesados = []
        self.resultados_por_imagen = [] # [{archivo, prefijo, ejercicios}]
        
        # Título
        self.lbl_titulo = ctk.CTkLabel(self, text="Digitalizador de Rutinas Pro", font=ctk.CTkFont(size=28, weight="bold"))
        self.lbl_titulo.grid(row=0, column=0, pady=(20, 10), padx=30, sticky="w")
        
        self.lbl_subtitulo = ctk.CTkLabel(self, text="Sube fotos de tus libretas y la IA extraerá los datos automáticamente.", font=ctk.CTkFont(size=16))
        self.lbl_subtitulo.grid(row=1, column=0, pady=(0, 20), padx=30, sticky="w")

        # --- SECCIÓN 1: SELECCIÓN DE ATLETA Y ARCHIVO ---
        self.frame_controles = ctk.CTkFrame(self)
        self.frame_controles.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        self.frame_controles.grid_columnconfigure((0, 1), weight=1)

        # Selección de Atleta
        self.lbl_atleta = ctk.CTkLabel(self.frame_controles, text="1. Selecciona el Atleta:", font=ctk.CTkFont(weight="bold"))
        self.lbl_atleta.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.combo_atletas = ctk.CTkComboBox(self.frame_controles, values=["Cargando atletas..."], width=300)
        self.combo_atletas.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Cargar atletas de la BBDD
        self.cargar_atletas()

        # Botón de Selección de Archivo
        self.lbl_file = ctk.CTkLabel(self.frame_controles, text="2. Carga las Imágenes (JPG/PNG):", font=ctk.CTkFont(weight="bold"))
        self.lbl_file.grid(row=0, column=1, padx=20, pady=(15, 5), sticky="w")
        
        self.btn_select_file = ctk.CTkButton(self.frame_controles, text="📁 Seleccionar Imágenes", 
                                             command=self.seleccionar_archivos,
                                             fg_color="#1f6aa5", hover_color="#144870")
        self.btn_select_file.grid(row=1, column=1, padx=20, pady=(0, 15), sticky="w")
        
        self.lbl_status_file = ctk.CTkLabel(self.frame_controles, text="Ningún archivo seleccionado", text_color="gray")
        self.lbl_status_file.grid(row=2, column=1, padx=20, pady=(0, 15), sticky="w")
        
        self.btn_help = ctk.CTkButton(self.frame_controles, text="?", width=30, height=30, corner_radius=15,
                                      fg_color="gray", hover_color="gray50", command=self.mostrar_ayuda)
        self.btn_help.grid(row=0, column=2, padx=20, pady=15, sticky="e")

        # --- SECCIÓN 2: ACCIÓN DE PROCESADO ---
        self.btn_procesar = ctk.CTkButton(self, text="⚡ PROCESAR CON IA", font=ctk.CTkFont(size=18, weight="bold"),
                                          height=50, command=self.iniciar_procesamiento,
                                          state="disabled", fg_color="#2e8c4a", hover_color="#1b5e20")
        self.btn_procesar.grid(row=3, column=0, padx=30, pady=20, sticky="ew")

        # --- SECCIÓN 3: RESULTADOS Y PREVISUALIZACIÓN ---
        self.frame_resultados = ctk.CTkFrame(self)
        self.frame_resultados.grid(row=4, column=0, padx=30, pady=10, sticky="nsew")
        self.frame_resultados.grid_columnconfigure(0, weight=1)
        
        self.lbl_res_titulo = ctk.CTkLabel(self.frame_resultados, text="Vista Previa de Ejercicios Detectados", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_res_titulo.pack(pady=10)
        
        self.txt_preview = ctk.CTkTextbox(self.frame_resultados, height=350, font=ctk.CTkFont(family="Consolas", size=13))
        self.txt_preview.pack(fill="both", expand=True, padx=20, pady=10)
        self.txt_preview.insert("0.0", "Los resultados aparecerán aquí tras el procesamiento...")
        self.txt_preview.configure(state="disabled")

        # --- SECCIÓN 4: GUARDAR Y EXPORTAR ---
        self.frame_acciones = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_acciones.grid(row=5, column=0, padx=30, pady=20, sticky="e")
        
        self.btn_exportar = ctk.CTkButton(self.frame_acciones, text="📊 Exportar a Excel", state="disabled", 
                                          command=self.exportar_excel, fg_color="#a06917", hover_color="#8c5607")
        self.btn_exportar.pack(side="left", padx=10)
        
        self.btn_guardar = ctk.CTkButton(self.frame_acciones, text="💾 Guardar en BBDD", state="disabled",
                                         command=self.confirmar_guardado)
        self.btn_guardar.pack(side="left", padx=10)

    def mostrar_ayuda(self):
        from tkinter import messagebox
        msg = ("Carga de Rutinas:\n\n"
               "- Selecciona un atleta y una o varias fotos.\n"
               "- Pulsa 'Procesar con IA'. Se usará Ollama (Local) para analizar cada página.\n"
               "- Cada foto se evalúa de forma independiente.\n"
               "- Revisa los resultados y guárdalos en la base de datos.")
        messagebox.showinfo("Ayuda: Carga de Rutinas", msg)

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

    def seleccionar_archivos(self):
        file_paths = filedialog.askopenfilenames(
            title="Seleccionar imágenes de rutina",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("Todos los archivos", "*.*")]
        )
        if file_paths:
            self.archivos_seleccionados = list(file_paths)
            cant = len(self.archivos_seleccionados)
            self.lbl_status_file.configure(text=f"{cant} archivos seleccionados", text_color="white")
            self.btn_procesar.configure(state="normal")

    def iniciar_procesamiento(self):
        atleta_str = self.combo_atletas.get()
        if "No hay atletas" in atleta_str or atleta_str == "Cargando atletas...":
            messagebox.showwarning("Atención", "Por favor, selecciona un atleta válido.")
            return
            
        atleta_id = int(atleta_str.split(" - ")[0])
        
        # Bloquear UI
        self.btn_procesar.configure(state="disabled", text="Analizando fotos...")
        self.txt_preview.configure(state="normal")
        self.txt_preview.delete("0.0", "end")
        self.txt_preview.insert("0.0", f"Iniciando el análisis de {len(self.archivos_seleccionados)} fotos...\nEstamos leyendo tu libreta, esto puede tardar un poco.\n")
        self.txt_preview.configure(state="disabled")
        
        # Lanzar en hilo para no congelar la UI
        threading.Thread(target=self.ejecutar_pipeline_multiple, args=(atleta_id,), daemon=True).start()

    def ejecutar_pipeline_multiple(self, atleta_id):
        try:
            self.resultados_por_imagen = []
            self.ejercicios_procesados = []
            
            with SessionLocal() as session:
                service = RutinasService(session)
                
                for i, path in enumerate(self.archivos_seleccionados, 1):
                    nombre_foto = os.path.basename(path)
                    self.actualizar_status_progreso(f"Leyendo foto {i} de {len(self.archivos_seleccionados)} ({nombre_foto})...")
                    
                    resultado = service.procesar_imagen_vlm_a_diccionario(path)
                    
                    if resultado.get("success"):
                        res_item = {
                            "archivo": nombre_foto,
                            "prefijo": resultado.get("prefijo", ""),
                            "ejercicios": resultado["data"]
                        }
                        self.resultados_por_imagen.append(res_item)
                        self.ejercicios_procesados.extend(resultado["data"])
                    else:
                        app_logger.error(f"Fallo en la foto {path}: {resultado.get('error')}")
                
                if not self.resultados_por_imagen:
                    self.finalizar_con_error("No se han podido detectar ejercicios. Prueba con una foto más clara.")
                    return
                
                # Mostrar en la previsualización consolidada
                self.mostrar_previsualizacion_multiple()
                
        except Exception as e:
            self.finalizar_con_error(f"Ha ocurrido un inconveniente: {str(e)}")

    def actualizar_status_progreso(self, msg):
        self.after(0, lambda: self.txt_preview.configure(state="normal"))
        self.after(0, lambda: self.txt_preview.insert("end", f"\n- {msg}"))
        self.after(0, lambda: self.txt_preview.see("end"))
        self.after(0, lambda: self.txt_preview.configure(state="disabled"))

    def finalizar_con_error(self, error):
        self.after(0, lambda: messagebox.showerror("Atención", error))
        self.after(0, lambda: self.btn_procesar.configure(state="normal", text="⚡ PROCESAR CON IA"))

    def mostrar_previsualizacion_multiple(self):
        self.after(0, lambda: self.txt_preview.configure(state="normal"))
        self.after(0, lambda: self.txt_preview.delete("0.0", "end"))
        
        previa = "RESUMEN DE DIGITALIZACIÓN MULTI-PÁGINA\n"
        previa += "="*40 + "\n\n"
        
        for item in self.resultados_por_imagen:
            previa += f"📄 ARCHIVO: {item['archivo']}\n"
            if item['prefijo']:
                previa += f"📍 CABECERA: {item['prefijo']}\n"
            previa += "-"*30 + "\n"
            
            for i, ej in enumerate(item['ejercicios'], 1):
                nombre = ej.get("nombre_ejercicio", "Desconocido")
                series = ej.get("series", "?")
                reps = ej.get("repeticiones", "?")
                detalle = ej.get("peso_objetivo", "?")
                previa += f"  {i}. {nombre} | {series} series | {reps} | {detalle}\n"
            previa += "\n"
            
        self.after(0, lambda: self.txt_preview.insert("0.0", previa))
        
        # Habilitar botones de acción
        self.after(0, lambda: self.btn_procesar.configure(state="normal", text="⚡ PROCESAR CON IA"))
        self.after(0, lambda: self.btn_guardar.configure(state="normal"))
        self.after(0, lambda: self.btn_exportar.configure(state="normal"))
        # No deshabilitamos para que el texto sea editable por el usuario
        
        # Habilitar botones de acción
        self.after(0, lambda: self.btn_procesar.configure(state="normal", text="⚡ PROCESAR CON IA"))
        self.after(0, lambda: self.btn_guardar.configure(state="normal"))
        self.after(0, lambda: self.btn_exportar.configure(state="normal"))

    def confirmar_guardado(self):
        atleta_str = self.combo_atletas.get()
        atleta_id = int(atleta_str.split(" - ")[0])
        nombre_atleta = atleta_str.split(" - ")[1]
        
        cant_rutinas = len(self.resultados_por_imagen)
        if messagebox.askyesno("Confirmar", f"¿Guardar {cant_rutinas} rutinas detectadas para {nombre_atleta}?"):
            try:
                exitos = 0
                with SessionLocal() as session:
                    repo = RutinasService(session).repo
                    
                    for item in self.resultados_por_imagen:
                        prefijo = item.get('prefijo', '')
                        archivo = item.get('archivo', '')
                        base_nombre = f"Rutina IA {datetime.now().strftime('%d/%m/%Y')}"
                        
                        # Nombre final combinando cabecera y fecha
                        if prefijo:
                            nombre_rutina = f"{prefijo} | {base_nombre} ({archivo})"
                        else:
                            nombre_rutina = f"{base_nombre} ({archivo})"
                            
                        if repo.guardar_rutina_completa(atleta_id, nombre_rutina, item['ejercicios']):
                            exitos += 1
                
                if exitos > 0:
                    messagebox.showinfo("Éxito", f"Se han guardado {exitos}/{cant_rutinas} rutinas correctamente.")
                    self.btn_guardar.configure(state="disabled")
                else:
                    messagebox.showerror("Error", "No se pudo guardar ninguna rutina.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def exportar_excel(self):
        output_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"Rutina_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        )
        if output_path:
            try:
                from logica.exportador import ExportadorExcel
                if ExportadorExcel.exportar_rutina(self.ejercicios_procesados, output_path):
                    messagebox.showinfo("Éxito", f"Excel generado en:\n{output_path}")
                else:
                    messagebox.showerror("Error", "No se pudo generar el Excel.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
