from bbdd.models import Atleta, Suscripcion
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

class AtletasService:
    def __init__(self, session: Session):
        self.session = session

    def obtener_atletas(self, estado=None):
        query = self.session.query(Atleta)
        if estado:
            query = query.filter(Atleta.estado == estado)
        return query.all()

    def obtener_atleta_por_id(self, atleta_id):
        return self.session.query(Atleta).filter(Atleta.id == atleta_id).first()

    def registrar_atleta(self, nombre_completo, fecha_comienzo=None, foto_perfil=None, email=None, telefono=None, objetivos=None, notas=None):
        hoy = datetime.today().date()
        if not fecha_comienzo:
            fecha_comienzo = hoy
            
        nuevo_atleta = Atleta(
            nombre_completo=nombre_completo,
            fecha_comienzo=fecha_comienzo,
            foto_perfil=foto_perfil,
            email=email,
            telefono=telefono,
            objetivos=objetivos,
            notas_entrenador=notas,
            estado="activo",
            fecha_alta=hoy
        )
        self.session.add(nuevo_atleta)
        self.session.flush() 
        
        # Suscripción inicial a 3 meses (90 días)
        fecha_renovacion = fecha_comienzo + timedelta(days=90)
        nueva_sub = Suscripcion(
            atleta_id=nuevo_atleta.id,
            fecha_renovacion=fecha_renovacion,
            estado="pendiente"
        )
        self.session.add(nueva_sub)
            
        self.session.commit()
        self.session.refresh(nuevo_atleta)
        return nuevo_atleta

    def actualizar_atleta(self, atleta_id, **kwargs):
        atleta = self.obtener_atleta_por_id(atleta_id)
        if not atleta:
            return False
        
        fecha_comienzo_antigua = atleta.fecha_comienzo
        
        for key, value in kwargs.items():
            if hasattr(atleta, key):
                setattr(atleta, key, value)
                
        # Si la fecha de comienzo se modificó, sobreescribir la suscripción
        if "fecha_comienzo" in kwargs and kwargs["fecha_comienzo"] != fecha_comienzo_antigua and kwargs["fecha_comienzo"] is not None:
            self.session.query(Suscripcion).filter(
                Suscripcion.atleta_id == atleta_id
            ).delete()
            
            fecha_renovacion = kwargs["fecha_comienzo"] + timedelta(days=90)
            nueva_sub = Suscripcion(
                atleta_id=atleta.id,
                fecha_renovacion=fecha_renovacion,
                estado="pendiente"
            )
            self.session.add(nueva_sub)
                
        self.session.commit()
        return True

    def cambiar_estado(self, atleta_id, nuevo_estado="inactivo"):
        atleta = self.obtener_atleta_por_id(atleta_id)
        if atleta:
            atleta.estado = nuevo_estado
            if nuevo_estado == "activo":
                # Al reactivar, se pone la renovación a 3 meses de hoy
                hoy = datetime.today().date()
                self.session.query(Suscripcion).filter(Suscripcion.atleta_id == atleta_id).delete()
                nueva_sub = Suscripcion(
                    atleta_id=atleta_id,
                    fecha_renovacion=hoy + timedelta(days=90),
                    estado="pendiente"
                )
                self.session.add(nueva_sub)
            self.session.commit()
            return True
        return False

    def obtener_suscripciones_vencidas(self):
        hoy = datetime.today().date()
        return self.session.query(Suscripcion).join(Atleta).filter(
            Suscripcion.fecha_renovacion <= hoy,
            Atleta.estado == "activo"
        ).all()

    def registrar_pago(self, suscripcion_id):
        sub = self.session.query(Suscripcion).filter(Suscripcion.id == suscripcion_id).first()
        if sub:
            # Marcamos como pagada la actual y creamos la siguiente a 3 meses de la fecha de renovacion pactada
            # o de hoy? El usuario dice "3 meses después".
            nueva_fecha = sub.fecha_renovacion + timedelta(days=90)
            sub.fecha_renovacion = nueva_fecha
            self.session.commit()
            return True
        return False
