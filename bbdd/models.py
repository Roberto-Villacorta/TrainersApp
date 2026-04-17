from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Atleta(Base):
    __tablename__ = "atletas"

    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    telefono = Column(String)
    fecha_alta = Column(Date, default=datetime.date.today)
    estado = Column(String, default="activo") # "activo" o "inactivo"
    objetivos = Column(Text)
    notas_entrenador = Column(Text)

    # Relaciones: Un atleta tiene muchas rutinas, formularios, etc.
    metricas = relationship("MetricaCorporal", back_populates="atleta", cascade="all, delete-orphan")
    formularios = relationship("FormularioSemanal", back_populates="atleta", cascade="all, delete-orphan")
    rutinas = relationship("Rutina", back_populates="atleta", cascade="all, delete-orphan")
    archivos = relationship("ArchivoSubido", back_populates="atleta", cascade="all, delete-orphan")

class MetricaCorporal(Base):
    __tablename__ = "metricas_corporales"

    id = Column(Integer, primary_key=True, index=True)
    atleta_id = Column(Integer, ForeignKey("atletas.id"))
    fecha_medicion = Column(Date, default=datetime.date.today)
    peso_kg = Column(Float)
    porcentaje_grasa = Column(Float)
    foto_progreso_ruta = Column(String)

    atleta = relationship("Atleta", back_populates="metricas")

class FormularioSemanal(Base):
    __tablename__ = "formularios_semanales"

    id = Column(Integer, primary_key=True, index=True) [cite: 8]
    atleta_id = Column(Integer, ForeignKey("atletas.id")) [cite: 9]
    fecha_registro = Column(Date, default=datetime.date.today) [cite: 10]
    
    # 1. Satisfacción
    satisfaccion_general = Column(Integer)  # 1-5 [cite: 11]
    comentario_satisfaccion = Column(Text) [cite: 12]
    
    # 2. Adherencia
    adherencia_plan = Column(String)  # baja/media/alta [cite: 14]
    lleva_mejor = Column(Text) [cite: 15]
    cuesta_mas = Column(Text) [cite: 16]
    
    # 3. Cambios en el plan
    modificaciones_plan = Column(Boolean) [cite: 18]
    que_quitaria = Column(Text) [cite: 19]
    que_anadiria = Column(Text) [cite: 20]
    
    # 4. Saciedad
    nivel_saciedad = Column(String) # hambre / normal / demasiada comida [cite: 22]
    comentario_saciedad = Column(Text) [cite: 23]
    
    # 5 y 6. Picoteos y Consumo
    hay_picoteos = Column(Boolean) [cite: 25]
    frecuencia_picoteos = Column(String) # nunca / a veces / frecuente [cite: 27]
    fruta_consumo = Column(Integer) [cite: 28]
    verdura_consumo = Column(Integer) [cite: 29]
    pescado_blanco_consumo = Column(Integer) [cite: 30]
    pescado_azul_consumo = Column(Integer) [cite: 31]
    
    # 7. Fin de semana
    sigue_plan_fin_semana = Column(Boolean) [cite: 33]
    eventos_fin_semana = Column(Boolean) [cite: 34]
    consume_alcohol = Column(Boolean) [cite: 35]
    cantidad_alcohol = Column(String) [cite: 36]
    
    # 8. Nutrición entreno
    pre_entreno = Column(Text) [cite: 38]
    intra_entreno = Column(Text) [cite: 39]
    post_entreno = Column(Text) [cite: 40]
    
    # 9. Mejora y Alertas/Tendencias
    mejora_entrenamiento = Column(Integer) # 1-5 [cite: 42]
    comentario_mejora = Column(Text) [cite: 42]
    alerta_fatiga = Column(Integer) [cite: 96]
    alerta_dolor = Column(Integer) [cite: 98]
    alerta_sueno = Column(Integer) [cite: 99]
    alerta_estres = Column(Integer) [cite: 101]
    alerta_rendimiento = Column(Integer) [cite: 102]

    atleta = relationship("Atleta", back_populates="formularios")

class Rutina(Base):
    __tablename__ = "rutinas"

    id = Column(Integer, primary_key=True, index=True)
    atleta_id = Column(Integer, ForeignKey("atletas.id"))
    nombre_rutina = Column(String)
    fecha_asignacion = Column(Date, default=datetime.date.today)
    activa = Column(Boolean, default=True)

    atleta = relationship("Atleta", back_populates="rutinas")
    ejercicios = relationship("EjercicioRutina", back_populates="rutina", cascade="all, delete-orphan")

class EjercicioRutina(Base):
    __tablename__ = "ejercicios_rutina"

    id = Column(Integer, primary_key=True, index=True)
    rutina_id = Column(Integer, ForeignKey("rutinas.id"))
    dia_sesion = Column(String)
    nombre_ejercicio = Column(String)
    series = Column(String)
    repeticiones = Column(String)
    peso_objetivo = Column(String)
    tiempo_descanso = Column(String)

    rutina = relationship("Rutina", back_populates="ejercicios")

class ArchivoSubido(Base):
    __tablename__ = "archivos_subidos"

    id = Column(Integer, primary_key=True, index=True)
    atleta_id = Column(Integer, ForeignKey("atletas.id"))
    nombre_archivo = Column(String)
    tipo = Column(String) # rutina_imagen, pdf, etc.
    ruta_local = Column(String)
    fecha_subida = Column(DateTime, default=datetime.datetime.now)

    atleta = relationship("Atleta", back_populates="archivos")