import customtkinter as ctk
import io
import datetime
from PIL import Image, ImageDraw
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from bbdd.database import SessionLocal
from logica.atletas_service import AtletasService
from bbdd.models import FormularioSemanal
from logica.ia_form_service import IAFormService

class DialogoFormulario(ctk.CTkToplevel):
    def __init__(self, master_ficha, id_atleta):
        super().__init__(master_ficha)
        self.title("Añadir Formulario Semanal")
        self.geometry("600x700")
        self.id_atleta = id_atleta
        self.master_ficha = master_ficha
        
        self.transient(master_ficha.winfo_toplevel())
        self.after(100, self.grab_set)
        
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Q1
        ctk.CTkLabel(self.scroll, text="1. ¿Te sientes satisfecho/a con el proceso y los resultados? (1-5)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        self.q1_slider = ctk.CTkSlider(self.scroll, from_=1, to=5, number_of_steps=4)
        self.q1_slider.set(3)
        self.q1_slider.pack(fill="x", pady=5)
        self.q1_text = ctk.CTkTextbox(self.scroll, height=50)
        self.q1_text.pack(fill="x", pady=5)

        # Q2
        ctk.CTkLabel(self.scroll, text="2. ¿Has llevado bien seguir el plan? (Llevando mejor / Costando más)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        self.q2_mejor = ctk.CTkEntry(self.scroll, placeholder_text="Llevando mejor...")
        self.q2_mejor.pack(fill="x", pady=2)
        self.q2_peor = ctk.CTkEntry(self.scroll, placeholder_text="Costando más...")
        self.q2_peor.pack(fill="x", pady=2)

        # Q3
        ctk.CTkLabel(self.scroll, text="3. ¿Hay algo que modificarías? (Quitarías / Añadirías)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        self.q3_quitar = ctk.CTkEntry(self.scroll, placeholder_text="Quitaría...")
        self.q3_quitar.pack(fill="x", pady=2)
        self.q3_anadir = ctk.CTkEntry(self.scroll, placeholder_text="Añadiría...")
        self.q3_anadir.pack(fill="x", pady=2)

        # Q4
        ctk.CTkLabel(self.scroll, text="4. ¿Cómo te sientes de saciado/a?", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        self.q4_saciedad = ctk.CTkOptionMenu(self.scroll, values=["Hambre", "Normal", "Demasiada comida"])
        self.q4_saciedad.pack(fill="x", pady=5)
        self.q4_text = ctk.CTkEntry(self.scroll, placeholder_text="Comentarios saciedad...")
        self.q4_text.pack(fill="x", pady=2)

        # Q5
        ctk.CTkLabel(self.scroll, text="5. ¿Sueles tener picoteos fuera de las comidas establecidas?", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        self.q5_freq = ctk.CTkOptionMenu(self.scroll, values=["Nunca", "A veces", "Frecuente"])
        self.q5_freq.pack(fill="x", pady=5)

        # Q6
        ctk.CTkLabel(self.scroll, text="6. Consumo (Veces por semana): Fruta, Verdura, P. Blanco, P. Azul", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        f_g = ctk.CTkFrame(self.scroll, fg_color="transparent")
        f_g.pack(fill="x")
        self.q6_fruta = ctk.CTkEntry(f_g, placeholder_text="Fruta", width=80)
        self.q6_fruta.pack(side="left", padx=2)
        self.q6_verdura = ctk.CTkEntry(f_g, placeholder_text="Verdura", width=80)
        self.q6_verdura.pack(side="left", padx=2)
        self.q6_blanco = ctk.CTkEntry(f_g, placeholder_text="P. Blanco", width=80)
        self.q6_blanco.pack(side="left", padx=2)
        self.q6_azul = ctk.CTkEntry(f_g, placeholder_text="P. Azul", width=80)
        self.q6_azul.pack(side="left", padx=2)

        # Q7
        ctk.CTkLabel(self.scroll, text="7. Fin de semana y Alcohol", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        self.q7_finde = ctk.CTkCheckBox(self.scroll, text="¿Sigue plan el fin de semana?")
        self.q7_finde.pack(anchor="w", pady=2)
        self.q7_alcohol = ctk.CTkEntry(self.scroll, placeholder_text="Consumo de alcohol...")
        self.q7_alcohol.pack(fill="x", pady=2)

        # Q8
        ctk.CTkLabel(self.scroll, text="8. Nutrición: Pre, Intra, Post Entreno", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        self.q8_pre = ctk.CTkEntry(self.scroll, placeholder_text="Pre-entreno")
        self.q8_pre.pack(fill="x", pady=2)
        self.q8_intra = ctk.CTkEntry(self.scroll, placeholder_text="Intra-entreno")
        self.q8_intra.pack(fill="x", pady=2)
        self.q8_post = ctk.CTkEntry(self.scroll, placeholder_text="Post-entreno")
        self.q8_post.pack(fill="x", pady=2)

        # Q9
        ctk.CTkLabel(self.scroll, text="9. ¿Estás mejorando gracias a la alimentación? (1-5)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        self.q9_slider = ctk.CTkSlider(self.scroll, from_=1, to=5, number_of_steps=4)
        self.q9_slider.set(3)
        self.q9_slider.pack(fill="x", pady=5)
        self.q9_text = ctk.CTkEntry(self.scroll, placeholder_text="Comentarios mejora...")
        self.q9_text.pack(fill="x", pady=2)

        # Q10
        ctk.CTkLabel(self.scroll, text="10. ¿Alguna duda que quieres que resolvamos?", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        self.q10_text = ctk.CTkTextbox(self.scroll, height=50)
        self.q10_text.pack(fill="x", pady=5)
        
        self.btn_guardar = ctk.CTkButton(self, text="Guardar Formulario", command=self.guardar)
        self.btn_guardar.pack(pady=10)

    def guardar(self):
        try:
            with SessionLocal() as session:
                nuevo_form = FormularioSemanal(
                    atleta_id=self.id_atleta,
                    fecha_registro=datetime.date.today(),
                    satisfaccion_general=int(self.q1_slider.get()),
                    comentario_satisfaccion=self.q1_text.get("1.0", "end").strip(),
                    adherencia_plan="media",
                    lleva_mejor=self.q2_mejor.get(),
                    cuesta_mas=self.q2_peor.get(),
                    modificaciones_plan=bool(self.q3_quitar.get() or self.q3_anadir.get()),
                    que_quitaria=self.q3_quitar.get(),
                    que_anadiria=self.q3_anadir.get(),
                    nivel_saciedad=self.q4_saciedad.get(),
                    comentario_saciedad=self.q4_text.get(),
                    hay_picoteos=self.q5_freq.get() != "Nunca",
                    frecuencia_picoteos=self.q5_freq.get(),
                    fruta_consumo=int(self.q6_fruta.get() or 0),
                    verdura_consumo=int(self.q6_verdura.get() or 0),
                    pescado_blanco_consumo=int(self.q6_blanco.get() or 0),
                    pescado_azul_consumo=int(self.q6_azul.get() or 0),
                    sigue_plan_fin_semana=self.q7_finde.get() == 1,
                    eventos_fin_semana=False,
                    consume_alcohol=bool(self.q7_alcohol.get()),
                    cantidad_alcohol=self.q7_alcohol.get(),
                    pre_entreno=self.q8_pre.get(),
                    intra_entreno=self.q8_intra.get(),
                    post_entreno=self.q8_post.get(),
                    mejora_entrenamiento=int(self.q9_slider.get()),
                    comentario_mejora=self.q9_text.get(),
                    dudas=self.q10_text.get("1.0", "end").strip()
                )
                
                # Integrar IA para las alertas
                ia_service = IAFormService()
                respuestas_para_ia = {
                    "comentario_satisfaccion": nuevo_form.comentario_satisfaccion,
                    "lleva_mejor": nuevo_form.lleva_mejor,
                    "cuesta_mas": nuevo_form.cuesta_mas,
                    "comentario_saciedad": nuevo_form.comentario_saciedad,
                    "dudas": nuevo_form.dudas
                }
                resultado_ia = ia_service.analizar_formulario(respuestas_para_ia)
                alertas = resultado_ia["alertas"]
                nuevo_form.alerta_fatiga = alertas["alerta_fatiga"]
                nuevo_form.alerta_dolor = alertas["alerta_dolor"]
                nuevo_form.alerta_sueno = alertas["alerta_sueno"]
                nuevo_form.alerta_estres = alertas["alerta_estres"]
                nuevo_form.alerta_rendimiento = alertas["alerta_rendimiento"]
                
                self.master_ficha.ultimo_resumen_ia = resultado_ia["resumen"]
                
                session.add(nuevo_form)
                session.commit()
            
            messagebox.showinfo("Éxito", "Formulario guardado con éxito.")
            self.master_ficha.cargar_atleta(self.id_atleta)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando formulario: {e}")

class FichaAtleta(ctk.CTkFrame):
    def __init__(self, master, master_app, **kwargs):
        super().__init__(master, **kwargs)
        self.master_app = master_app
        self.id_atleta_actual = None
        self.imagen_cargada = None
        self.ultimo_resumen_ia = ""

        # Frame Superior (Botones y Cabecera)
        self.frame_cabecera = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_cabecera.pack(side="top", fill="x", pady=10, padx=20)
        
        self.btn_volver = ctk.CTkButton(self.frame_cabecera, text="← Volver a Atletas", width=140, fg_color="gray", hover_color="gray50", command=self.volver_al_listado)
        self.btn_volver.pack(side="left")
        
        self.btn_help = ctk.CTkButton(self.frame_cabecera, text="?", width=30, height=30, corner_radius=15,
                                      fg_color="gray", hover_color="gray50", command=self.mostrar_ayuda)
        self.btn_help.pack(side="right")
        
        # Frame Perfil
        self.frame_perfil = ctk.CTkFrame(self)
        self.frame_perfil.pack(fill="x", padx=20, pady=20)
        
        self.lbl_foto = ctk.CTkLabel(self.frame_perfil, text="")
        self.lbl_foto.pack(side="left", padx=20, pady=20)
        
        self.lbl_nombre = ctk.CTkLabel(self.frame_perfil, text="", font=ctk.CTkFont(size=28, weight="bold"))
        self.lbl_nombre.pack(side="left", padx=10, pady=20)
        
        # Botón para añadir formulario (Nuevo)
        self.btn_formulario = ctk.CTkButton(self.frame_perfil, text="📋 Añadir Formulario", width=160, 
                                            fg_color="#2e8c4a", hover_color="#1b5e20", command=self.abrir_formulario)
        self.btn_formulario.pack(side="right", padx=20, pady=20)
        
        # Frame Contenido Adicional (Gráficos y Resumen)
        self.frame_contenido = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frame_contenido.pack(fill="both", expand=True, padx=20, pady=10)

    def mostrar_ayuda(self):
        msg = ("Ficha del Atleta:\n\n"
               "- Información General: Consulta los datos básicos y la foto del cliente.\n"
               "- Formularios: Añade el reporte semanal. Contiene análisis automático por IA.\n"
               "- Gráficos: Compara el último reporte con el anterior.")
        messagebox.showinfo("Ayuda: Ficha de Atleta", msg)

    def crear_avatar_por_defecto(self, nombre):
        img = Image.new('RGB', (100, 100), color=(100, 100, 150))
        d = ImageDraw.Draw(img)
        letra = nombre[0].upper() if nombre else "?"
        d.text((40, 40), letra, fill=(255, 255, 255))
        return img

    def abrir_formulario(self):
        if self.id_atleta_actual:
            DialogoFormulario(self, self.id_atleta_actual)

    def renderizar_graficos(self):
        # Limpiar frame de contenido
        for widget in self.frame_contenido.winfo_children():
            widget.destroy()
            
        with SessionLocal() as session:
            formularios = session.query(FormularioSemanal).filter(
                FormularioSemanal.atleta_id == self.id_atleta_actual
            ).order_by(FormularioSemanal.fecha_registro.desc()).limit(2).all()
            
            # 1. Resumen IA
            if self.ultimo_resumen_ia:
                f_ia = ctk.CTkFrame(self.frame_contenido, fg_color="#1d4066")
                f_ia.pack(fill="x", pady=(0, 20))
                ctk.CTkLabel(f_ia, text="🤖 " + self.ultimo_resumen_ia, font=ctk.CTkFont(size=14, weight="bold"), text_color="white", wraplength=500).pack(pady=10, padx=10)
            elif formularios and formularios[0].dudas:
                # Si no acabamos de guardar pero hay dudas en el último
                f_ia = ctk.CTkFrame(self.frame_contenido, fg_color="#1d4066")
                f_ia.pack(fill="x", pady=(0, 20))
                ctk.CTkLabel(f_ia, text=f"🤖 Últimas dudas del atleta: {formularios[0].dudas}", font=ctk.CTkFont(size=14, italic=True), text_color="white", wraplength=500).pack(pady=10, padx=10)

            if not formularios:
                lbl = ctk.CTkLabel(self.frame_contenido, text="No hay formularios registrados para este atleta.", font=ctk.CTkFont(size=14, slant="italic"))
                lbl.pack(pady=40)
                return
                
            if len(formularios) == 1:
                lbl = ctk.CTkLabel(self.frame_contenido, text="Se necesita al menos otro formulario para ver la comparativa. ¡Buen comienzo!", font=ctk.CTkFont(size=14, slant="italic"))
                lbl.pack(pady=40)
                return
                
            form_actual = formularios[0]
            form_anterior = formularios[1]
            
            # Comparar y encontrar mejor/peor
            metricas = {
                "Satisfacción": (form_actual.satisfaccion_general, form_anterior.satisfaccion_general),
                "Mejora (Entreno)": (form_actual.mejora_entrenamiento, form_anterior.mejora_entrenamiento),
                "Fruta": (form_actual.fruta_consumo, form_anterior.fruta_consumo),
                "Verdura": (form_actual.verdura_consumo, form_anterior.verdura_consumo)
            }
            
            mejor_metrica = ""
            mejor_diff = -999
            peor_metrica = ""
            peor_diff = 999
            
            for nombre, (act, ant) in metricas.items():
                if act is None or ant is None: continue
                diff = act - ant
                if diff > mejor_diff:
                    mejor_diff = diff
                    mejor_metrica = nombre
                if diff < peor_diff:
                    peor_diff = diff
                    peor_metrica = nombre
                    
            # Resumen de cambios
            f_cambios = ctk.CTkFrame(self.frame_contenido, fg_color="transparent")
            f_cambios.pack(fill="x", pady=10)
            
            if mejor_metrica and mejor_diff > 0:
                ctk.CTkLabel(f_cambios, text=f"🌟 MEJOR CAMBIO: {mejor_metrica} (+{mejor_diff})", font=ctk.CTkFont(weight="bold"), text_color="#2e8c4a").pack(side="left", padx=20)
            if peor_metrica and peor_diff < 0:
                ctk.CTkLabel(f_cambios, text=f"⚠️ PEOR CAMBIO: {peor_metrica} ({peor_diff})", font=ctk.CTkFont(weight="bold"), text_color="#c25757").pack(side="right", padx=20)

            # Matplotlib Chart
            fig, ax = plt.subplots(figsize=(6, 4), facecolor='#2b2b2b')
            ax.set_facecolor('#2b2b2b')
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_edgecolor('white')

            etiquetas = list(metricas.keys())
            valores_act = [m[0] or 0 for m in metricas.values()]
            valores_ant = [m[1] or 0 for m in metricas.values()]
            
            x = range(len(etiquetas))
            width = 0.35
            
            ax.bar([i - width/2 for i in x], valores_ant, width, label='Anterior', color='#4a90e2')
            ax.bar([i + width/2 for i in x], valores_act, width, label='Actual', color='#2e8c4a')
            
            ax.set_ylabel('Valor', color='white')
            ax.set_title('Comparativa de Formularios', color='white')
            ax.set_xticks(x)
            ax.set_xticklabels(etiquetas, color='white')
            ax.legend()
            
            canvas = FigureCanvasTkAgg(fig, master=self.frame_contenido)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, pady=20)

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
            
        # Renderizamos los gráficos al final
        self.renderizar_graficos()
            
    def volver_al_listado(self):
        if hasattr(self.master_app, "mostrar_pantalla"):
            self.master_app.mostrar_pantalla("atletas")
