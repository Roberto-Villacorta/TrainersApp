from bbdd.models import Atleta
from sqlalchemy.orm import Session
from datetime import datetime

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

    def registrar_atleta(self, nombre_completo, foto_perfil=None, email=None, telefono=None, objetivos=None, notas=None):
        nuevo_atleta = Atleta(
            nombre_completo=nombre_completo,
            foto_perfil=foto_perfil,
            email=email,
            telefono=telefono,
            objetivos=objetivos,
            notas_entrenador=notas,
            estado="activo",
            fecha_alta=datetime.today().date()
        )
        self.session.add(nuevo_atleta)
        self.session.commit()
        self.session.refresh(nuevo_atleta)
        return nuevo_atleta

    def actualizar_atleta(self, atleta_id, **kwargs):
        atleta = self.obtener_atleta_por_id(atleta_id)
        if not atleta:
            return False
        
        for key, value in kwargs.items():
            if hasattr(atleta, key):
                setattr(atleta, key, value)
                
        self.session.commit()
        return True

    def cambiar_estado(self, atleta_id, nuevo_estado="inactivo"):
        atleta = self.obtener_atleta_por_id(atleta_id)
        if atleta:
            atleta.estado = nuevo_estado
            self.session.commit()
            return True
        return False
