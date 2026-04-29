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
        self.archivo_seleccionado = None
        self.ejercicios_procesados = []
        
        # Título
        self.lbl_titulo = ctk.CTkLabel(self, text="Procesamiento de Rutinas por IA", font=ctk.CTkFont(size=28, weight="bold"))
        self.lbl_titulo.grid(row=0, column=0, pady=(20, 10), padx=30, sticky="w")
        
        self.lbl_subtitulo = ctk.CTkLabel(self, text="Sube una foto de tu rutina y deja que la IA haga el trabajo sucio.", font=ctk.CTkFont(size=16))
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
        self.lbl_file = ctk.CTkLabel(self.frame_controles, text="2. Carga la Imagen (JPG/PNG):", font=ctk.CTkFont(weight="bold"))
        self.lbl_file.grid(row=0, column=1, padx=20, pady=(15, 5), sticky="w")
        
        self.btn_select_file = ctk.CTkButton(self.frame_controles, text="📁 Seleccionar Imagen", 
                                             command=self.seleccionar_archivo,
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
        
        self.txt_preview = ctk.CTkTextbox(self.frame_resultados, height=250, font=ctk.CTkFont(family="Consolas", size=13))
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
               "- Selecciona un atleta y una imagen de su rutina.\n"
               "- Pulsa 'Procesar con IA' para extraer los ejercicios automáticamente.\n"
               "- Revisa y edita el texto detectado si es necesario.\n"
               "- Exporta a Excel o guárdalo en la base de datos.")
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

    def seleccionar_archivo(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar imagen de rutina",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.archivo_seleccionado = file_path
            nombre_base = os.path.basename(file_path)
            self.lbl_status_file.configure(text=f"Archivo: {nombre_base}", text_color="white")
            self.btn_procesar.configure(state="normal")

    def iniciar_procesamiento(self):
        atleta_str = self.combo_atletas.get()
        if "No hay atletas" in atleta_str or atleta_str == "Cargando atletas...":
            messagebox.showwarning("Atención", "Por favor, selecciona un atleta válido.")
            return
            
        atleta_id = int(atleta_str.split(" - ")[0])
        
        # Bloquear UI
        self.btn_procesar.configure(state="disabled", text="Procesando...")
        self.txt_preview.configure(state="normal")
        self.txt_preview.delete("0.0", "end")
        self.txt_preview.insert("0.0", "Extrayendo texto con OCR y analizando con IA...\nPor favor, espera.")
        self.txt_preview.configure(state="disabled")
        
        # Lanzar en hilo para no congelar la UI
        threading.Thread(target=self.ejecutar_pipeline, args=(atleta_id,), daemon=True).start()

    def ejecutar_pipeline(self, atleta_id):
        try:
            with SessionLocal() as session:
                service = RutinasService(session)
                # Solo procesamos (no guardamos automáticamente en este paso para que el usuario revise)
                # pero para cumplir con el pedido del usuario de "montar la pipeline de leer la imagen pasarle ese texto a la IA",
                # lo haremos aquí.
                
                from logica.procesador_ocr import OCRProcessor
                texto_ocr = OCRProcessor.extract_text(self.archivo_seleccionado)
                
                if not texto_ocr:
                    self.finalizar_con_error("No se pudo extraer texto de la imagen.")
                    return
                
                from logica.ia_service import GlinerService
                ia = GlinerService()
                resultados = ia.procesar_texto_rutina(texto_ocr)
                
                if not resultados:
                    self.finalizar_con_error("La IA no detectó ejercicios.")
                    return
                
                self.ejercicios_procesados = resultados
                self.mostrar_previsualizacion(texto_ocr, resultados)
                
        except Exception as e:
            self.finalizar_con_error(f"Error crítico: {str(e)}")

    def finalizar_con_error(self, error):
        self.after(0, lambda: messagebox.showerror("Error", error))
        self.after(0, lambda: self.btn_procesar.configure(state="normal", text="⚡ PROCESAR CON IA"))

    def mostrar_previsualizacion(self, texto_ocr, resultados):
        self.after(0, lambda: self.txt_preview.configure(state="normal"))
        self.after(0, lambda: self.txt_preview.delete("0.0", "end"))
        
        previa = f"TEXTO EXTRAÍDO (OCR):\n{'-'*30}\n{texto_ocr}\n\n"
        previa += f"EJERCICIOS DETECTADOS POR IA:\n{'-'*30}\n"
        
        for i, ej in enumerate(resultados, 1):
            nombre = ej.get("nombre_ejercicio") or ej.get("texto") or "Desconocido"
            series = ej.get("series", "?")
            reps = ej.get("repeticiones", "?")
            peso = ej.get("peso_objetivo") or ej.get("peso_kg", "?")
            previa += f"{i}. {nombre} | {series} x {reps} | {peso}kg\n"
            
        self.after(0, lambda: self.txt_preview.insert("0.0", previa))
        # No deshabilitamos para que el texto sea editable por el usuario
        
        # Habilitar botones de acción
        self.after(0, lambda: self.btn_procesar.configure(state="normal", text="⚡ PROCESAR CON IA"))
        self.after(0, lambda: self.btn_guardar.configure(state="normal"))
        self.after(0, lambda: self.btn_exportar.configure(state="normal"))

    def confirmar_guardado(self):
        atleta_str = self.combo_atletas.get()
        atleta_id = int(atleta_str.split(" - ")[0])
        nombre_atleta = atleta_str.split(" - ")[1]
        
        if messagebox.askyesno("Confirmar", f"¿Guardar esta rutina para {nombre_atleta}?"):
            try:
                with SessionLocal() as session:
                    repo = RutinasService(session).repo
                    nombre_rutina = f"Rutina IA {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                    if repo.guardar_rutina_completa(atleta_id, nombre_rutina, self.ejercicios_procesados):
                        messagebox.showinfo("Éxito", "Rutina guardada correctamente en la BBDD.")
                        self.btn_guardar.configure(state="disabled")
                    else:
                        messagebox.showerror("Error", "No se pudo guardar la rutina.")
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
