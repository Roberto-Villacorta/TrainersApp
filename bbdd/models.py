from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text, LargeBinary
from sqlalchemy.orm import relationship
from bbdd.database import Base
import datetime

class Atleta(Base):
    __tablename__ = "atletas"

    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    telefono = Column(String)
    fecha_alta = Column(Date, default=datetime.date.today)
    fecha_comienzo = Column(Date, nullable=True)
    estado = Column(String, default="activo") # "activo" o "inactivo"
    objetivos = Column(Text)
    notas_entrenador = Column(Text)
    foto_perfil = Column(LargeBinary, nullable=True)

    # Relaciones: Un atleta tiene muchas rutinas, formularios, etc.
    metricas = relationship("MetricaCorporal", back_populates="atleta", cascade="all, delete-orphan")
    formularios = relationship("FormularioSemanal", back_populates="atleta", cascade="all, delete-orphan")
    rutinas = relationship("Rutina", back_populates="atleta", cascade="all, delete-orphan")
    archivos = relationship("ArchivoSubido", back_populates="atleta", cascade="all, delete-orphan")
    suscripciones = relationship("Suscripcion", back_populates="atleta", cascade="all, delete-orphan")

class MetricaCorporal(Base):
    __tablename__ = "metricas_corporales"

    id = Column(Integer, primary_key=True, index=True)
    atleta_id = Column(Integer, ForeignKey("atletas.id"))
    fecha_medicion = Column(Date, default=datetime.date.today)
    peso_kg = Column(Float)
    porcentaje_grasa = Column(Float)

    atleta = relationship("Atleta", back_populates="metricas")

class FormularioSemanal(Base):
    __tablename__ = "formularios_semanales"

    id = Column(Integer, primary_key=True, index=True)
    atleta_id = Column(Integer, ForeignKey("atletas.id"))
    fecha_registro = Column(Date, default=datetime.date.today)
    
    # 1. Satisfacción
    satisfaccion_general = Column(Integer)  # 1-5
    comentario_satisfaccion = Column(Text)
    
    # 2. Adherencia
    adherencia_plan = Column(String)  # baja/media/alta
    lleva_mejor = Column(Text)
    cuesta_mas = Column(Text)
    
    # 3. Cambios en el plan
    modificaciones_plan = Column(Boolean)
    que_quitaria = Column(Text)
    que_anadiria = Column(Text)
    
    # 4. Saciedad
    nivel_saciedad = Column(String) # hambre / normal / demasiada comida
    comentario_saciedad = Column(Text)
    
    # 5 y 6. Picoteos y Consumo
    hay_picoteos = Column(Boolean)
    frecuencia_picoteos = Column(String) # nunca / a veces / frecuente
    fruta_consumo = Column(Integer)
    verdura_consumo = Column(Integer)
    pescado_blanco_consumo = Column(Integer)
    pescado_azul_consumo = Column(Integer)
    
    # 7. Fin de semana
    sigue_plan_fin_semana = Column(Boolean)
    eventos_fin_semana = Column(Boolean)
    consume_alcohol = Column(Boolean)
    cantidad_alcohol = Column(String)
    
    # 8. Nutrición entreno
    pre_entreno = Column(Text)
    intra_entreno = Column(Text)
    post_entreno = Column(Text)
    
    # 9. Mejora y Alertas/Tendencias
    mejora_entrenamiento = Column(Integer) # 1-5
    comentario_mejora = Column(Text)
    alerta_fatiga = Column(Integer)
    alerta_dolor = Column(Integer)
    alerta_sueno = Column(Integer)
    alerta_estres = Column(Integer)
    alerta_rendimiento = Column(Integer)

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

class Llamada(Base):
    __tablename__ = "llamadas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    fecha = Column(Date, nullable=False)

class Suscripcion(Base):
    __tablename__ = "suscripciones"

    id = Column(Integer, primary_key=True, index=True)
    atleta_id = Column(Integer, ForeignKey("atletas.id"))
    fecha_renovacion = Column(Date, nullable=False)
    estado = Column(String, default="pendiente") # "pendiente", "pagado", etc.

    atleta = relationship("Atleta", back_populates="suscripciones")