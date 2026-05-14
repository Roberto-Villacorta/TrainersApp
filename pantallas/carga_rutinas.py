import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
import queue
from datetime import datetime
from bbdd.database import SessionLocal
from logica.atletas_service import AtletasService
from logica.rutinas_service import RutinasService
from logica.vlm_service import VLMService
from utils.logger import app_logger
from utils.dialogos_ayuda import DialogoAyuda

class CargaRutinas(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        # Estado local
        self.archivos_seleccionados = []
        self.ejercicios_procesados = []
        self.resultados_por_imagen = [] # [{archivo, prefijo, ejercicios}]
        
        # Cola para actualizaciones de UI seguras
        self.cola_ui = queue.Queue()
        self.verificar_cola_ui()
        
        self.lbl_titulo = ctk.CTkLabel(self, text="Escanear Libreta de Entrenamiento", font=ctk.CTkFont(size=28, weight="bold"))
        self.lbl_titulo.grid(row=0, column=0, pady=(20, 10), padx=30, sticky="w")
        
        self.lbl_subtitulo = ctk.CTkLabel(self, text="Sube fotos de la libreta de tu atleta y el programa leerá los datos.", font=ctk.CTkFont(size=16))
        self.lbl_subtitulo.grid(row=1, column=0, pady=(0, 20), padx=30, sticky="w")
        
        # Verificación de GPU (Nielsen: Error Prevention)
        self.gpu_disponible = VLMService.is_gpu_available()
        if not self.gpu_disponible:
            self.lbl_no_gpu = ctk.CTkLabel(self, text="⚠️ FUNCIÓN DESACTIVADA: Se requiere una tarjeta gráfica NVIDIA (GPU) para usar la IA.", 
                                          text_color="#c25757", font=ctk.CTkFont(weight="bold"))
            self.lbl_no_gpu.grid(row=2, column=0, pady=5, padx=30, sticky="w")

        # --- SECCIÓN 1: SELECCIÓN DE ATLETA Y ARCHIVO ---
        self.frame_controles = ctk.CTkFrame(self)
        self.frame_controles.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        self.frame_controles.grid_columnconfigure((0, 1), weight=1)

        # Selección de Atleta
        self.lbl_atleta = ctk.CTkLabel(self.frame_controles, text="1. Selecciona al Atleta:", font=ctk.CTkFont(weight="bold"))
        self.lbl_atleta.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.combo_atletas = ctk.CTkComboBox(self.frame_controles, values=["Cargando atletas..."], width=300,
                                            fg_color="white", text_color="black", button_color="#3b8ed0", button_hover_color="#2c7bb6")
        self.combo_atletas.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Cargar atletas de la BBDD
        self.cargar_atletas()

        # Botón de Selección de Archivo
        self.lbl_file = ctk.CTkLabel(self.frame_controles, text="2. Carga las Imágenes (JPG/PNG):", font=ctk.CTkFont(weight="bold"))
        self.lbl_file.grid(row=0, column=1, padx=20, pady=(15, 5), sticky="w")
        
        self.btn_select_file = ctk.CTkButton(self.frame_controles, text="Seleccionar Imagenes", 
                                             command=self.seleccionar_archivos,
                                             fg_color="#1f6aa5", hover_color="#144870")
        self.btn_select_file.grid(row=1, column=1, padx=20, pady=(0, 15), sticky="w")
        
        self.lbl_status_file = ctk.CTkLabel(self.frame_controles, text="Ningun archivo seleccionado", text_color="gray")
        self.lbl_status_file.grid(row=2, column=1, padx=20, pady=(0, 15), sticky="w")
        
        self.btn_help = ctk.CTkButton(self.frame_controles, text="?", width=30, height=30, corner_radius=15,
                                      fg_color="gray", hover_color="gray50", command=self.mostrar_ayuda)
        self.btn_help.grid(row=0, column=2, padx=20, pady=15, sticky="e")

        # --- SECCIÓN 2: ACCIÓN DE PROCESADO ---
        self.btn_procesar = ctk.CTkButton(self, text="ANALIZAR FOTO", font=ctk.CTkFont(size=18, weight="bold"),
                                          height=50, command=self.iniciar_procesamiento,
                                          state="disabled" if not self.gpu_disponible else "disabled", 
                                          fg_color="#2e8c4a", hover_color="#1b5e20")
        self.btn_procesar.grid(row=3, column=0, padx=30, pady=20, sticky="ew")
        
        if not self.gpu_disponible:
            self.btn_procesar.configure(text="IA DESACTIVADA (SIN GPU)")

        # --- SECCIÓN 3: RESULTADOS Y PREVISUALIZACIÓN ---
        self.frame_resultados = ctk.CTkFrame(self)
        self.frame_resultados.grid(row=4, column=0, padx=30, pady=10, sticky="nsew")
        self.frame_resultados.grid_columnconfigure(0, weight=1)
        
        self.lbl_res_titulo = ctk.CTkLabel(self.frame_resultados, text="Vista Previa de Ejercicios Detectados", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_res_titulo.pack(pady=10)
        
        self.txt_preview = ctk.CTkTextbox(self.frame_resultados, height=350, font=ctk.CTkFont(family="Consolas", size=13))
        self.txt_preview.pack(fill="both", expand=True, padx=20, pady=10)
        self.txt_preview.insert("0.0", "Los resultados aparecerán aquí. Podrás corregirlos si falta algo.")
        self.txt_preview.configure(state="disabled")

        # --- SECCIÓN 4: GUARDAR Y EXPORTAR ---
        self.frame_acciones = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_acciones.grid(row=5, column=0, padx=30, pady=20, sticky="e")
        
        self.btn_exportar = ctk.CTkButton(self.frame_acciones, text="Guardar en Excel", state="disabled", 
                                          command=self.exportar_excel, fg_color="#a06917", hover_color="#8c5607")
        self.btn_exportar.pack(side="left", padx=10)
        
        self.btn_guardar = ctk.CTkButton(self.frame_acciones, text="Guardar en el Programa", state="disabled",
                                         command=self.confirmar_guardado)
        self.btn_guardar.pack(side="left", padx=10)

    def verificar_cola_ui(self):
        """Procesa tareas de UI pendientes enviadas desde hilos."""
        try:
            while True:
                tarea = self.cola_ui.get_nowait()
                if callable(tarea):
                    tarea()
        except queue.Empty:
            pass
        finally:
            self.after(100, self.verificar_cola_ui)

    def mostrar_ayuda(self):
        titulo = "Guía: Escanear fotos de la libreta"
        msg = (
            "Esta función permite que el programa lea por ti las fotos de los entrenamientos escritos a mano. Sigue estos pasos:\n\n"
            "1. ELIGE AL ATLETA: Selecciona el nombre del alumno al que pertenecen las fotos.\n\n"
            "2. SUBE LAS FOTOS: Pulsa el botón azul 'Seleccionar Imágenes' y elige las fotos de la libreta que tengas en tu ordenador.\n\n"
            "3. ANALIZAR: Pulsa el botón verde grande 'ANALIZAR FOTO'. El ordenador tardará unos segundos en 'leer' la letra.\n\n"
            "4. REVISA: Verás que aparece el texto en el cuadro de abajo. Asegúrate de que los nombres de los ejercicios y los pesos son correctos.\n\n"
            "5. GUARDA: Si todo está bien, pulsa 'Guardar en el Programa'.\n\n"
            "⚠️ IMPORTANTE: Esta función solo funciona en ordenadores muy potentes con tarjeta gráfica NVIDIA (GPU). Si el botón sale en gris, es porque tu ordenador no tiene la potencia necesaria para esta Inteligencia Artificial."
        )
        DialogoAyuda(self, titulo, msg)

    def cargar_atletas(self):
        try:
            actual = self.combo_atletas.get()
            with SessionLocal() as session:
                service = AtletasService(session)
                atletas = service.obtener_atletas(estado="activo")
                if atletas:
                    nombres = [f"{a.id} - {a.nombre_completo}" for a in atletas]
                    self.combo_atletas.configure(values=nombres)
                    # Mantener selección si sigue activa
                    if actual in nombres:
                        self.combo_atletas.set(actual)
                    else:
                        self.combo_atletas.set(nombres[0])
                else:
                    self.combo_atletas.configure(values=["No hay atletas activos"])
                    self.combo_atletas.set("No hay atletas activos")
        except Exception as e:
            app_logger.error(f"Error cargando atletas: {e}")

    def seleccionar_archivos(self):
        file_paths = filedialog.askopenfilenames(
            title="Seleccionar imagenes de rutina",
            filetypes=[("Imagenes", "*.png *.jpg *.jpeg"), ("Todos los archivos", "*.*")]
        )
        if file_paths:
            self.archivos_seleccionados = list(file_paths)
            cant = len(self.archivos_seleccionados)
            self.lbl_status_file.configure(text=f"{cant} archivos seleccionados", text_color="white")
            if self.gpu_disponible:
                self.btn_procesar.configure(state="normal")

    def iniciar_procesamiento(self):
        atleta_str = self.combo_atletas.get()
        if "No hay atletas" in atleta_str or atleta_str == "Cargando atletas...":
            messagebox.showwarning("Atencion", "Por favor, selecciona un atleta valido.")
            return
            
        atleta_id = int(atleta_str.split(" - ")[0])
        
        # Bloquear UI
        self.btn_procesar.configure(state="disabled", text="Analizando fotos...")
        self.txt_preview.configure(state="normal")
        self.txt_preview.delete("0.0", "end")
        self.txt_preview.insert("0.0", f"Leyendo las {len(self.archivos_seleccionados)} fotos...\nPor favor, espera un momento.\n")
        self.txt_preview.configure(state="disabled")
        
        # Lanzar en hilo para no congelar la UI
        threading.Thread(target=self.ejecutar_pipeline_multiple, args=(atleta_id,), daemon=True).start()

    def ejecutar_pipeline_multiple(self, atleta_id):
        try:
            self.resultados_por_imagen = []
            
            with SessionLocal() as session:
                service = RutinasService(session)
                
                for i, path in enumerate(self.archivos_seleccionados, 1):
                    nombre_foto = os.path.basename(path)
                    msg_prefix = f"[Imagen {i}/{len(self.archivos_seleccionados)}]"
                    
                    self.actualizar_status_progreso(f"\n{msg_prefix} Analizando: {nombre_foto}")
                    
                    # Callback local con prefijo
                    def callback_vlm(m):
                        self.actualizar_status_progreso(f"{msg_prefix} {m}")

                    resultado = service.procesar_imagen_vlm_secuencial(
                        path, 
                        progress_callback=callback_vlm
                    )
                    
                    if resultado.get("success"):
                        res_item = {
                            "archivo": nombre_foto,
                            "prefijo": resultado.get("prefijo", ""),
                            "ejercicios": resultado["data"]["ejercicios"]
                        }
                        self.resultados_por_imagen.append(res_item)
                    else:
                        error_msg = resultado.get('error', 'Error desconocido')
                        self.actualizar_status_progreso(f"{msg_prefix} Fallo: {error_msg}")
                
                if not self.resultados_por_imagen:
                    self.finalizar_con_error("No se han podido detectar ejercicios.")
                    return
                
                # Mostrar en la previsualización consolidada
                self.mostrar_previsualizacion_multiple()
                
        except Exception as e:
            self.finalizar_con_error(f"Inconveniente detectado: {str(e)}")

    def actualizar_status_progreso(self, msg):
        self.cola_ui.put(lambda: self.txt_preview.configure(state="normal"))
        self.cola_ui.put(lambda: self.txt_preview.insert("end", f"{msg}\n"))
        self.cola_ui.put(lambda: self.txt_preview.see("end"))
        self.cola_ui.put(lambda: self.txt_preview.configure(state="disabled"))

    def finalizar_con_error(self, error):
        self.cola_ui.put(lambda: messagebox.showerror("Atención", error))
        self.cola_ui.put(lambda: self.btn_procesar.configure(state="normal", text="ANALIZAR FOTO"))

    def mostrar_previsualizacion_multiple(self):
        self.cola_ui.put(lambda: self.txt_preview.configure(state="normal"))
        self.cola_ui.put(lambda: self.txt_preview.delete("0.0", "end"))
        
        previa = "RESUMEN DE LA LIBRETA\n"
        previa += "="*30 + "\n\n"
        
        for item in self.resultados_por_imagen:
            previa += f"ARCHIVO: {item['archivo']}\n"
            if item['prefijo']:
                previa += f"CABECERA: {item['prefijo']}\n"
            previa += "-"*20 + "\n"
            
            for i, ej in enumerate(item['ejercicios'], 1):
                nombre = ej.get("nombre_ejercicio", "Desconocido")
                series = ej.get("series", "?")
                reps = ej.get("repeticiones", "?")
                detalle = ej.get("peso_objetivo", "?")
                previa += f"  {i}. {nombre} | {series} series | {reps} | {detalle}\n"
            previa += "\n"
            
        self.cola_ui.put(lambda: self.txt_preview.insert("0.0", previa))
        
        # Habilitar botones de acción y PERMITIR EDICION
        self.cola_ui.put(lambda: self.txt_preview.configure(state="normal"))
        self.cola_ui.put(lambda: self.btn_procesar.configure(state="normal", text="VOLVER A ANALIZAR"))
        self.cola_ui.put(lambda: self.btn_guardar.configure(state="normal"))
        self.cola_ui.put(lambda: self.btn_exportar.configure(state="normal"))

    def parsear_texto_a_datos(self):
        """
        Orquesta la conversión del texto del CTkTextbox a una estructura de datos usable.
        """
        texto = self.txt_preview.get("1.0", "end")
        lineas = [l.strip() for l in texto.split("\n") if l.strip()]
        
        datos_finales = []
        bloque_actual = {"archivo": "Desconocido", "prefijo": "", "ejercicios": []}
        
        for line in lineas:
            if line.startswith("ARCHIVO:"):
                self._guardar_bloque_acumulado(datos_finales, bloque_actual)
                bloque_actual = {"archivo": line.replace("ARCHIVO:", "").strip(), "prefijo": "", "ejercicios": []}
            elif line.startswith("CABECERA:"):
                bloque_actual["prefijo"] = line.replace("CABECERA:", "").strip()
            elif "|" in line:
                ej = self._parsear_linea_ejercicio(line)
                if ej:
                    bloque_actual["ejercicios"].append(ej)
        
        self._guardar_bloque_acumulado(datos_finales, bloque_actual)
        return datos_finales

    def _guardar_bloque_acumulado(self, lista_datos, bloque):
        """Helper para guardar un bloque de ejercicios si contiene datos."""
        if bloque["ejercicios"]:
            lista_datos.append(bloque.copy())

    def _parsear_linea_ejercicio(self, line):
        """Parsea una única línea de ejercicio y devuelve un diccionario."""
        try:
            parts = line.split("|")
            # Extraer nombre quitando el número inicial "1. Press..."
            nombre_part = parts[0]
            nombre = nombre_part.split(".", 1)[1].strip() if "." in nombre_part else nombre_part.strip()
            
            return {
                "nombre_ejercicio": nombre,
                "series": parts[1].replace("series", "").strip() if len(parts) > 1 else "1",
                "repeticiones": parts[2].strip() if len(parts) > 2 else "",
                "peso_objetivo": parts[3].strip() if len(parts) > 3 else "",
                "tiempo_descanso": ""
            }
        except Exception as e:
            app_logger.warning(f"No se pudo parsear línea de ejercicio: {line}. Error: {e}")
            return None

    def confirmar_guardado(self):
        # 1. Obtener datos actualizados del texto (por si el usuario editó)
        self.resultados_por_imagen = self.parsear_texto_a_datos()
        
        if not self.resultados_por_imagen:
            messagebox.showwarning("Atención", "No hay datos válidos en el cuadro de texto para guardar.")
            return

        atleta_str = self.combo_atletas.get()
        atleta_id = int(atleta_str.split(" - ")[0])
        nombre_atleta = atleta_str.split(" - ")[1]
        
        if messagebox.askyesno("Confirmar", f"¿Guardar rutinas detectadas para {nombre_atleta}?"):
            try:
                exitos = 0
                with SessionLocal() as session:
                    repo = RutinasService(session).repo
                    for item in self.resultados_por_imagen:
                        nombre_rutina = f"{item['prefijo']} | Rutina IA ({item['archivo']})" if item['prefijo'] else f"Rutina IA ({item['archivo']})"
                        if repo.guardar_rutina_completa(atleta_id, nombre_rutina, item['ejercicios']):
                            exitos += 1
                
                if exitos > 0:
                    messagebox.showinfo("Éxito", f"Se han guardado {exitos} rutinas correctamente.")
                    self.btn_guardar.configure(state="disabled")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def exportar_excel(self):
        # 1. Obtener datos actualizados del texto
        datos_editados = self.parsear_texto_a_datos()
        
        # Aplanamos para el exportador
        ejercicios_totales = []
        for item in datos_editados:
            for ej in item['ejercicios']:
                # Añadir información del archivo/sesión a cada fila de excel
                ej['dia_sesion'] = item['prefijo'] or item['archivo']
                ejercicios_totales.append(ej)
        
        if not ejercicios_totales:
            messagebox.showwarning("Atención", "No hay datos para exportar.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"Rutina_IA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        if output_path:
            try:
                from logica.exportador import ExportadorExcel
                if ExportadorExcel.exportar_rutina(ejercicios_totales, output_path):
                    messagebox.showinfo("Éxito", f"Excel generado en:\n{output_path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
