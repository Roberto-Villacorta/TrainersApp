from sqlalchemy.orm import Session
from bbdd.repository import DashboardRepository
from utils.logger import app_logger
import datetime
import calendar


def _add_months(sourcedate: datetime.date, months: int) -> datetime.date:
    """
    Suma un número entero de meses a una fecha, respetando los límites del
    calendario (por ejemplo, 31 de enero + 1 mes = 28/29 de febrero).
    """
    month = sourcedate.month - 1 + months
    year  = sourcedate.year + month // 12
    month = month % 12 + 1
    day   = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


class DashboardService:
    """
    Capa de servicio para el Dashboard.

    Actúa como intermediario entre la UI y el repositorio, aplicando la lógica
    de negocio necesaria antes de leer o escribir datos. Entre otras cosas,
    al añadir una llamada la replica automáticamente en los dos meses siguientes
    para que el entrenador no tenga que programarlas manualmente.
    """

    def __init__(self, session: Session):
        self.repository = DashboardRepository(session)

    def obtener_metricas_dashboard(self) -> dict:
        """
        Devuelve las métricas principales del Dashboard en un único dict:
        - ``atletas_activos``: total de atletas en estado 'activo'.
        - ``formularios_pendientes``: atletas activos sin formulario esta semana.

        En caso de error de base de datos, devuelve ambos valores a 0 y
        registra el error en el log.
        """
        try:
            return {
                "atletas_activos":       self.repository.count_atletas_activos(),
                "formularios_pendientes": self.repository.count_formularios_pendientes(),
            }
        except Exception as e:
            app_logger.error(f"Error al obtener métricas del dashboard: {e}")
            return {"atletas_activos": 0, "formularios_pendientes": 0}

    def obtener_atletas_activos(self) -> list:
        """Devuelve una lista de todos los atletas activos."""
        try:
            return self.repository.obtener_atletas_activos()
        except Exception as e:
            app_logger.error(f"Error al obtener atletas activos: {e}")
            return []

    def agregar_llamada(self, nombre: str, fecha: datetime.date) -> bool:
        """
        Programa una llamada en la fecha indicada y la repite automáticamente
        en los dos meses siguientes (ciclo trimestral).

        Devuelve True si la transacción fue correcta, False si hubo algún error.
        """
        try:
            self.repository.guardar_llamada(nombre, fecha)
            self.repository.guardar_llamada(nombre, _add_months(fecha, 1))
            self.repository.guardar_llamada(nombre, _add_months(fecha, 2))
            self.repository.session.commit()
            return True
        except Exception as e:
            self.repository.session.rollback()
            app_logger.error(f"Error al guardar llamada: {e}")
            return False

    def eliminar_llamadas(self, fecha: datetime.date) -> bool:
        """
        Elimina todas las llamadas programadas para una fecha concreta.
        Útil para cancelar un día completo de agenda de una vez.
        """
        try:
            self.repository.eliminar_llamadas_por_fecha(fecha)
            self.repository.session.commit()
            return True
        except Exception as e:
            self.repository.session.rollback()
            app_logger.error(f"Error al eliminar llamadas: {e}")
            return False

    def eliminar_llamada_por_id(self, llamada_id: int) -> bool:
        """Elimina una única llamada identificada por su ID."""
        try:
            self.repository.eliminar_llamada_por_id(llamada_id)
            self.repository.session.commit()
            return True
        except Exception as e:
            self.repository.session.rollback()
            app_logger.error(f"Error al eliminar llamada {llamada_id}: {e}")
            return False

    def actualizar_llamada(self, llamada_id: int, nuevo_nombre: str) -> bool:
        """Cambia el nombre de una llamada existente identificada por su ID."""
        try:
            self.repository.actualizar_llamada(llamada_id, nuevo_nombre)
            self.repository.session.commit()
            return True
        except Exception as e:
            self.repository.session.rollback()
            app_logger.error(f"Error al actualizar llamada {llamada_id}: {e}")
            return False

    def obtener_llamadas_mes(self, anio: int, mes: int) -> list:
        """Devuelve todas las llamadas programadas en el mes y año indicados."""
        try:
            return self.repository.obtener_llamadas_por_mes(anio, mes)
        except Exception as e:
            app_logger.error(f"Error al obtener llamadas: {e}")
            return []

    def obtener_suscripciones_mes(self, anio: int, mes: int) -> list:
        """
        Devuelve las suscripciones de atletas activos con fecha de renovación
        dentro del mes y año indicados.
        """
        try:
            return self.repository.obtener_suscripciones_por_mes(anio, mes)
        except Exception as e:
            app_logger.error(f"Error al obtener suscripciones: {e}")
            return []

    def obtener_datos_calendario(self, anio: int, mes: int) -> dict:
        """
        Optimización: Obtiene todas las llamadas y renovaciones del mes 
        en un solo objeto estructurado por día para acelerar el renderizado de la UI.
        """
        datos = {}
        try:
            # Podríamos optimizar esto más con una sola query compleja en el repo, 
            # pero por ahora consolidamos la lógica de negocio aquí.
            llamadas = self.obtener_llamadas_mes(anio, mes)
            suscripciones = self.obtener_suscripciones_mes(anio, mes)
            
            for ll in llamadas:
                dia = ll.fecha.day
                datos.setdefault(dia, {"llamadas": [], "renovaciones": []})
                datos[dia]["llamadas"].append({"id": ll.id, "nombre": ll.nombre})
                
            for s in suscripciones:
                dia = s.fecha_renovacion.day
                datos.setdefault(dia, {"llamadas": [], "renovaciones": []})
                datos[dia]["renovaciones"].append(s.atleta.nombre_completo)
                
            return datos
        except Exception as e:
            app_logger.error(f"Error consolidando datos del calendario: {e}")
            return {}
