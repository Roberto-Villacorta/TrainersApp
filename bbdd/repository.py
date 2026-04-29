from sqlalchemy.orm import Session
from sqlalchemy import extract
from bbdd.models import Atleta, FormularioSemanal, Llamada, Suscripcion
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
        Los atletas activos que no tengan guardado un formulario con la última fecha del último domingo 
        (o posterior) suman 1 a los formularios pendientes.
        """
        hoy = datetime.date.today()
        # weekday(): 0 es Lunes, 6 es Domingo.
        dias_desde_domingo = hoy.weekday() + 1 if hoy.weekday() != 6 else 0
        ultimo_domingo = hoy - datetime.timedelta(days=dias_desde_domingo)
        
        # Subconsulta para obtener los atletas que SÍ tienen formulario desde el último domingo
        atletas_con_formulario = self.session.query(FormularioSemanal.atleta_id).filter(
            FormularioSemanal.fecha_registro >= ultimo_domingo
        ).scalar_subquery()
        
        # Contar atletas activos que NO están en la subconsulta
        pendientes = self.session.query(Atleta).filter(
            Atleta.estado == "activo",
            ~Atleta.id.in_(atletas_con_formulario)
        ).count()
        
        return pendientes

    def guardar_llamada(self, nombre: str, fecha: datetime.date) -> Llamada:
        nueva_llamada = Llamada(nombre=nombre, fecha=fecha)
        self.session.add(nueva_llamada)
        return nueva_llamada

    def obtener_llamadas_por_mes(self, anio: int, mes: int) -> list[Llamada]:
        return self.session.query(Llamada).filter(
            extract('year', Llamada.fecha) == anio,
            extract('month', Llamada.fecha) == mes
        ).all()
        
    def obtener_suscripciones_por_mes(self, anio: int, mes: int) -> list[Suscripcion]:
        return self.session.query(Suscripcion).join(Atleta).filter(
            extract('year', Suscripcion.fecha_renovacion) == anio,
            extract('month', Suscripcion.fecha_renovacion) == mes,
            Atleta.estado == "activo"
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

class RoutineRepository:
    def __init__(self, session: Session):
        self.session = session

    def guardar_rutina_completa(self, atleta_id: int, nombre_rutina: str, ejercicios_data: list) -> bool:
        """
        Crea una rutina y todos sus ejercicios en una transacción.
        """
        try:
            from bbdd.models import Rutina, EjercicioRutina
            
            # 1. Crear la cabecera de la rutina
            nueva_rutina = Rutina(
                atleta_id=atleta_id,
                nombre_rutina=nombre_rutina,
                fecha_asignacion=datetime.date.today(),
                activa=True
            )
            self.session.add(nueva_rutina)
            self.session.flush() # Para obtener el id de la rutina
            
            # 2. Añadir los ejercicios
            for ej in ejercicios_data:
                # El mapeo depende de la salida del parser
                nuevo_ej = EjercicioRutina(
                    rutina_id=nueva_rutina.id,
                    nombre_ejercicio=ej.get("nombre_ejercicio", "Desconocido"),
                    series=str(ej.get("series", "")),
                    repeticiones=str(ej.get("repeticiones", "")),
                    peso_objetivo=str(ej.get("peso_objetivo", "")),
                    tiempo_descanso=str(ej.get("tiempo_descanso", ""))
                )
                self.session.add(nuevo_ej)
            
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error guardando rutina: {e}")
            return False
