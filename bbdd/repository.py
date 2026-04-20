from sqlalchemy.orm import Session
from sqlalchemy import extract
from bbdd.models import Atleta, FormularioSemanal, Llamada
import datetime

class DashboardRepository:
    def __init__(self, session: Session):
        self.session = session

    def count_atletas_activos(self) -> int:
        """Cuenta el número de atletas con estado 'activo'."""
        return self.session.query(Atleta).filter(Atleta.estado == "activo").count()

    def count_formularios_pendientes(self) -> int:
        """
        Cuenta los formularios pendientes.
        Por ahora, cuenta todos los formularios registrados en la base de datos.
        """
        return self.session.query(FormularioSemanal).count()

    def guardar_llamada(self, nombre: str, fecha: datetime.date) -> Llamada:
        nueva_llamada = Llamada(nombre=nombre, fecha=fecha)
        self.session.add(nueva_llamada)
        return nueva_llamada

    def obtener_llamadas_por_mes(self, anio: int, mes: int) -> list[Llamada]:
        return self.session.query(Llamada).filter(
            extract('year', Llamada.fecha) == anio,
            extract('month', Llamada.fecha) == mes
        ).all()

    def eliminar_llamadas_por_fecha(self, fecha: datetime.date):
        self.session.query(Llamada).filter(Llamada.fecha == fecha).delete()

    def eliminar_llamada_por_id(self, llamada_id: int):
        self.session.query(Llamada).filter(Llamada.id == llamada_id).delete()

    def actualizar_llamada(self, llamada_id: int, nuevo_nombre: str) -> Llamada:
        llamada = self.session.query(Llamada).filter(Llamada.id == llamada_id).first()
        if llamada:
            llamada.nombre = nuevo_nombre
        return llamada
