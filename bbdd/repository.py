from sqlalchemy.orm import Session
from sqlalchemy import extract
from bbdd.models import Atleta, FormularioSemanal, Llamada, Suscripcion
import datetime


class DashboardRepository:
    """
    Repositorio de datos para el Dashboard.

    Agrupa todas las consultas a la base de datos que alimentan las métricas
    y el calendario del Dashboard: recuento de atletas, formularios pendientes,
    llamadas programadas y suscripciones por mes.
    """

    def __init__(self, session: Session):
        self.session = session

    def count_atletas_activos(self) -> int:
        """Devuelve el número de atletas con estado 'activo'."""
        return self.session.query(Atleta).filter(Atleta.estado == "activo").count()

    def count_formularios_pendientes(self) -> int:
        """
        Devuelve el número de atletas activos que aún no han enviado
        su formulario semanal desde el último domingo.

        La lógica considera como «semana en curso» el periodo que va desde
        el domingo inmediatamente anterior hasta hoy. Un atleta cuenta como
        pendiente si no tiene ningún formulario registrado en ese intervalo.
        """
        hoy = datetime.date.today()
        # weekday() devuelve 0=Lunes … 6=Domingo.
        # Si hoy es domingo (6), dias_desde_domingo = 0 (el corte es hoy mismo).
        dias_desde_domingo = hoy.weekday() + 1 if hoy.weekday() != 6 else 0
        ultimo_domingo = hoy - datetime.timedelta(days=dias_desde_domingo)

        # IDs de atletas que ya han enviado al menos un formulario esta semana
        atletas_con_formulario = self.session.query(FormularioSemanal.atleta_id).filter(
            FormularioSemanal.fecha_registro >= ultimo_domingo
        ).scalar_subquery()

        # Atletas activos que NO están en la lista anterior → pendientes
        return self.session.query(Atleta).filter(
            Atleta.estado == "activo",
            ~Atleta.id.in_(atletas_con_formulario)
        ).count()

    def guardar_llamada(self, nombre: str, fecha: datetime.date) -> Llamada:
        """
        Crea un registro de llamada en la sesión (sin hacer commit).
        El commit debe llamarse externamente para poder agrupar varias
        llamadas en una sola transacción.
        """
        nueva_llamada = Llamada(nombre=nombre, fecha=fecha)
        self.session.add(nueva_llamada)
        return nueva_llamada

    def obtener_llamadas_por_mes(self, anio: int, mes: int) -> list[Llamada]:
        """Devuelve todas las llamadas programadas en el mes y año indicados."""
        return self.session.query(Llamada).filter(
            extract('year', Llamada.fecha) == anio,
            extract('month', Llamada.fecha) == mes
        ).all()

    def obtener_suscripciones_por_mes(self, anio: int, mes: int) -> list[Suscripcion]:
        """
        Devuelve las suscripciones de atletas activos cuya fecha de renovación
        cae dentro del mes y año indicados.
        """
        return self.session.query(Suscripcion).join(Atleta).filter(
            extract('year', Suscripcion.fecha_renovacion) == anio,
            extract('month', Suscripcion.fecha_renovacion) == mes,
            Atleta.estado == "activo"
        ).all()

    def eliminar_llamadas_por_fecha(self, fecha: datetime.date):
        """Elimina todas las llamadas programadas para una fecha concreta."""
        self.session.query(Llamada).filter(Llamada.fecha == fecha).delete()

    def eliminar_llamada_por_id(self, llamada_id: int):
        """Elimina una llamada específica por su clave primaria."""
        self.session.query(Llamada).filter(Llamada.id == llamada_id).delete()

    def actualizar_llamada(self, llamada_id: int, nuevo_nombre: str) -> Llamada:
        """
        Cambia el nombre de una llamada existente.
        Devuelve el objeto actualizado o None si no se encontró.
        """
        llamada = self.session.query(Llamada).filter(Llamada.id == llamada_id).first()
        if llamada:
            llamada.nombre = nuevo_nombre
        return llamada


class RoutineRepository:
    """
    Repositorio para la gestión de rutinas de entrenamiento.

    Centraliza la escritura de rutinas y sus ejercicios en la base de datos,
    garantizando que ambas operaciones se realicen dentro de una única
    transacción atómica.
    """

    def __init__(self, session: Session):
        self.session = session

    def guardar_rutina_completa(self, atleta_id: int, nombre_rutina: str, ejercicios_data: list) -> bool:
        """
        Persiste una rutina junto con todos sus ejercicios en una sola transacción.

        Primero crea la cabecera (Rutina) y hace flush para obtener su ID.
        Después inserta cada EjercicioRutina vinculado. Si cualquier paso
        falla, se hace rollback y se devuelve False.

        Args:
            atleta_id: ID del atleta propietario de la rutina.
            nombre_rutina: Nombre descriptivo (normalmente incluye fecha y hora).
            ejercicios_data: Lista de dicts con las claves 'nombre_ejercicio',
                             'series', 'repeticiones', 'peso_objetivo' y
                             'tiempo_descanso', tal como las devuelve el parser.

        Returns:
            True si la transacción tuvo éxito, False en caso contrario.
        """
        try:
            from bbdd.models import Rutina, EjercicioRutina

            nueva_rutina = Rutina(
                atleta_id=atleta_id,
                nombre_rutina=nombre_rutina,
                fecha_asignacion=datetime.date.today(),
                activa=True
            )
            self.session.add(nueva_rutina)
            # flush para obtener nueva_rutina.id antes del commit
            self.session.flush()

            for ej in ejercicios_data:
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
