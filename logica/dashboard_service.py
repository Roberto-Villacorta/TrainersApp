from sqlalchemy.orm import Session
from bbdd.repository import DashboardRepository
from utils.logger import app_logger
import datetime
import calendar

def _add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month // 12 + 1 if (month % 12 + 1) > 12 else month % 12 + 1 # safer modulo
    # A cleaner logic
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)

class DashboardService:
    def __init__(self, session: Session):
        self.repository = DashboardRepository(session)

    def obtener_metricas_dashboard(self) -> dict:
        """
        Obtiene las métricas principales para mostrar en el dashboard.
        """
        try:
            atletas_activos = self.repository.count_atletas_activos()
            formularios_pendientes = self.repository.count_formularios_pendientes()
            
            return {
                "atletas_activos": atletas_activos,
                "formularios_pendientes": formularios_pendientes
            }
        except Exception as e:
            # En caso de error, devolvemos valores por defecto o 0
            app_logger.error(f"Error al obtener métricas del dashboard: {e}")
            return {
                "atletas_activos": 0,
                "formularios_pendientes": 0
            }

    def agregar_llamada(self, nombre: str, fecha: datetime.date):
        """Guarda una nueva llamada para este mes y los dos siguientes y aplica el commit en la BBDD."""
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

    def eliminar_llamadas(self, fecha: datetime.date):
        """Elimina todas las llamadas programadas para una fecha dada."""
        try:
            self.repository.eliminar_llamadas_por_fecha(fecha)
            self.repository.session.commit()
            return True
        except Exception as e:
            self.repository.session.rollback()
            app_logger.error(f"Error al eliminar llamadas: {e}")
            return False

    def eliminar_llamada_por_id(self, llamada_id: int):
        """Elimina una llamada específica por su ID."""
        try:
            self.repository.eliminar_llamada_por_id(llamada_id)
            self.repository.session.commit()
            return True
        except Exception as e:
            self.repository.session.rollback()
            app_logger.error(f"Error al eliminar llamada {llamada_id}: {e}")
            return False

    def actualizar_llamada(self, llamada_id: int, nuevo_nombre: str):
        """Actualiza el nombre de una llamada específica por su ID."""
        try:
            self.repository.actualizar_llamada(llamada_id, nuevo_nombre)
            self.repository.session.commit()
            return True
        except Exception as e:
            self.repository.session.rollback()
            app_logger.error(f"Error al actualizar llamada {llamada_id}: {e}")
            return False

    def obtener_llamadas_mes(self, anio: int, mes: int) -> list:
        """Obtiene todas las llamadas programadas para un mes y año concretos."""
        try:
            return self.repository.obtener_llamadas_por_mes(anio, mes)
        except Exception as e:
            app_logger.error(f"Error al obtener llamadas: {e}")
            return []
