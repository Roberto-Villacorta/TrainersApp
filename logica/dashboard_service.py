from sqlalchemy.orm import Session
from bbdd.repository import DashboardRepository
import datetime

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
            print(f"Error al obtener métricas del dashboard: {e}")
            return {
                "atletas_activos": 0,
                "formularios_pendientes": 0
            }

    def agregar_llamada(self, nombre: str, fecha: datetime.date):
        """Guarda una nueva llamada y aplica el commit en la BBDD."""
        try:
            self.repository.guardar_llamada(nombre, fecha)
            self.repository.session.commit()
            return True
        except Exception as e:
            self.repository.session.rollback()
            print(f"Error al guardar llamada: {e}")
            return False

    def obtener_llamadas_mes(self, anio: int, mes: int) -> list:
        """Obtiene todas las llamadas programadas para un mes y año concretos."""
        try:
            return self.repository.obtener_llamadas_por_mes(anio, mes)
        except Exception as e:
            print(f"Error al obtener llamadas: {e}")
            return []
