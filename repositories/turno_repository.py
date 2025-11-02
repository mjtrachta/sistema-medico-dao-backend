"""
PATRÓN: Repository Pattern + Specification Pattern
==================================================

Este repositorio implementa:
1. Repository para acceso a turnos
2. Specification para validaciones complejas de horarios
3. Query Objects para búsquedas específicas

JUSTIFICACIÓN DE PATRONES:
-------------------------
- Repository: Abstrae queries complejas de disponibilidad
- Specification: Reglas de negocio reutilizables (ej: turno válido)
- Query Object: Búsquedas nombradas y tipadas
"""

from typing import List, Optional
from datetime import date, time, datetime, timedelta
from models import Turno, Medico, HorarioMedico
from repositories.base_repository import BaseRepository
from sqlalchemy import and_, or_, func


class TurnoRepository(BaseRepository[Turno]):
    """
    Repositorio específico para gestión de turnos.

    Responsabilidades:
    - CRUD de turnos
    - Validación de disponibilidad de horarios
    - Detección de superposición de turnos
    - Queries de reportes
    """

    def __init__(self):
        super().__init__(Turno)

    # ==========================================
    # QUERIES DE BÚSQUEDA
    # ==========================================

    def find_by_codigo(self, codigo_turno: str) -> Optional[Turno]:
        """
        Busca turno por código único.

        Query Object Pattern: Query nombrada
        """
        return self.find_one({'codigo_turno': codigo_turno})

    def find_by_paciente(self, paciente_id: int,
                        desde: date = None,
                        hasta: date = None,
                        estados: List[str] = None) -> List[Turno]:
        """
        Busca turnos de un paciente con filtros opcionales.

        Args:
            paciente_id: ID del paciente
            desde: Fecha desde (opcional)
            hasta: Fecha hasta (opcional)
            estados: Lista de estados a filtrar (opcional)

        Returns:
            Lista de turnos ordenados por fecha/hora
        """
        from models.database import db

        query = db.session.query(Turno).filter(
            Turno.paciente_id == paciente_id
        )

        if desde:
            query = query.filter(Turno.fecha >= desde)

        if hasta:
            query = query.filter(Turno.fecha <= hasta)

        if estados:
            query = query.filter(Turno.estado.in_(estados))

        return query.order_by(Turno.fecha.desc(), Turno.hora.desc()).all()

    def find_by_medico(self, medico_id: int,
                      desde: date = None,
                      hasta: date = None,
                      estados: List[str] = None) -> List[Turno]:
        """
        Busca turnos de un médico con filtros opcionales.

        Similar a find_by_paciente pero para médicos.
        Útil para ver agenda del médico.
        """
        from models.database import db

        query = db.session.query(Turno).filter(
            Turno.medico_id == medico_id
        )

        if desde:
            query = query.filter(Turno.fecha >= desde)

        if hasta:
            query = query.filter(Turno.fecha <= hasta)

        if estados:
            query = query.filter(Turno.estado.in_(estados))

        return query.order_by(Turno.fecha.asc(), Turno.hora.asc()).all()

    def find_by_fecha(self, fecha: date,
                     medico_id: int = None,
                     ubicacion_id: int = None) -> List[Turno]:
        """
        Busca todos los turnos de una fecha específica.

        Útil para:
        - Ver agenda del día
        - Planificación de recursos
        """
        from models.database import db

        query = db.session.query(Turno).filter(Turno.fecha == fecha)

        if medico_id:
            query = query.filter(Turno.medico_id == medico_id)

        if ubicacion_id:
            query = query.filter(Turno.ubicacion_id == ubicacion_id)

        return query.order_by(Turno.hora.asc()).all()

    # ==========================================
    # VALIDACIONES DE DISPONIBILIDAD
    # ==========================================
    # PATRÓN: Specification Pattern
    # Cada método encapsula una regla de negocio compleja

    def verificar_disponibilidad_medico(self, medico_id: int,
                                       fecha: date,
                                       hora: time,
                                       duracion_min: int,
                                       excluir_turno_id: int = None) -> bool:
        """
        Verifica si un médico está disponible en fecha/hora específica.

        SPECIFICATION PATTERN: Regla de negocio encapsulada
        Verifica:
        1. El médico tiene horario de atención ese día
        2. La hora está dentro del horario de atención
        3. No hay superposición con otros turnos

        Args:
            medico_id: ID del médico
            fecha: Fecha del turno
            hora: Hora del turno
            duracion_min: Duración en minutos
            excluir_turno_id: ID de turno a excluir (para actualizaciones)

        Returns:
            True si está disponible, False si no
        """
        # 1. Verificar horario de atención
        if not self._tiene_horario_atencion(medico_id, fecha, hora, duracion_min):
            return False

        # 2. Verificar superposición con otros turnos
        if self._existe_superposicion(medico_id, fecha, hora, duracion_min, excluir_turno_id):
            return False

        return True

    def _tiene_horario_atencion(self, medico_id: int, fecha: date,
                                hora: time, duracion_min: int) -> bool:
        """
        Verifica si el médico tiene horario de atención.

        SPECIFICATION: Regla de negocio - horario válido
        """
        from models.database import db

        # Obtener día de la semana
        dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        dia_semana = dias_semana[fecha.weekday()]

        # Calcular hora de fin del turno
        hora_datetime = datetime.combine(fecha, hora)
        hora_fin_datetime = hora_datetime + timedelta(minutes=duracion_min)
        hora_fin = hora_fin_datetime.time()

        # Buscar horario que cubra el turno
        horario = db.session.query(HorarioMedico).filter(
            HorarioMedico.medico_id == medico_id,
            HorarioMedico.dia_semana == dia_semana,
            HorarioMedico.hora_inicio <= hora,
            HorarioMedico.hora_fin >= hora_fin,
            HorarioMedico.activo == True
        ).first()

        return horario is not None

    def _existe_superposicion(self, medico_id: int, fecha: date,
                             hora: time, duracion_min: int,
                             excluir_turno_id: int = None) -> bool:
        """
        Detecta si hay superposición con otros turnos.

        SPECIFICATION: Regla de negocio - no superposición

        Algoritmo de detección de superposición:
        Dos turnos se superponen si:
        - turno1.inicio < turno2.fin AND turno1.fin > turno2.inicio

        Esta es una validación CRÍTICA del sistema.
        """
        from models.database import db

        # Calcular inicio y fin del turno a validar
        hora_inicio = hora
        hora_datetime = datetime.combine(fecha, hora)
        hora_fin_datetime = hora_datetime + timedelta(minutes=duracion_min)
        hora_fin = hora_fin_datetime.time()

        # Buscar turnos del mismo médico en la misma fecha
        # que NO estén cancelados
        query = db.session.query(Turno).filter(
            Turno.medico_id == medico_id,
            Turno.fecha == fecha,
            Turno.estado.in_(['pendiente', 'confirmado', 'completado'])
        )

        if excluir_turno_id:
            query = query.filter(Turno.id != excluir_turno_id)

        turnos_existentes = query.all()

        # Verificar superposición con cada turno
        for turno in turnos_existentes:
            turno_hora_fin_dt = datetime.combine(fecha, turno.hora) + \
                               timedelta(minutes=turno.duracion_min)
            turno_hora_fin = turno_hora_fin_dt.time()

            # Algoritmo de detección de superposición
            if hora_inicio < turno_hora_fin and hora_fin > turno.hora:
                return True  # Hay superposición

        return False

    def get_horarios_disponibles(self, medico_id: int, fecha: date,
                                 duracion_min: int = 30) -> List[time]:
        """
        Genera lista de horarios disponibles para un médico en una fecha.

        PATRÓN: Factory Method (genera objetos time)

        Algoritmo:
        1. Obtener horario de atención del médico ese día
        2. Generar slots de tiempo según duración
        3. Filtrar slots que estén ocupados
        4. Retornar slots disponibles

        Args:
            medico_id: ID del médico
            fecha: Fecha a consultar
            duracion_min: Duración de cada slot

        Returns:
            Lista de horarios (time) disponibles
        """
        from models.database import db

        # 1. Obtener horario de atención
        dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        dia_semana = dias_semana[fecha.weekday()]

        horarios_atencion = db.session.query(HorarioMedico).filter(
            HorarioMedico.medico_id == medico_id,
            HorarioMedico.dia_semana == dia_semana,
            HorarioMedico.activo == True
        ).all()

        if not horarios_atencion:
            return []

        # 2. Generar slots para cada bloque horario
        slots_disponibles = []

        for horario in horarios_atencion:
            # Convertir a datetime para facilitar cálculos
            slot_actual = datetime.combine(fecha, horario.hora_inicio)
            hora_fin = datetime.combine(fecha, horario.hora_fin)

            # Generar slots cada duracion_min minutos
            while slot_actual + timedelta(minutes=duracion_min) <= hora_fin:
                hora_slot = slot_actual.time()

                # 3. Verificar si el slot está disponible
                if self.verificar_disponibilidad_medico(
                    medico_id, fecha, hora_slot, duracion_min
                ):
                    slots_disponibles.append(hora_slot)

                # Avanzar al siguiente slot
                slot_actual += timedelta(minutes=duracion_min)

        return slots_disponibles

    # ==========================================
    # ESTADÍSTICAS Y REPORTES
    # ==========================================

    def get_turnos_por_estado(self, fecha_desde: date,
                              fecha_hasta: date) -> dict:
        """
        Obtiene cantidad de turnos agrupados por estado.

        Útil para reportes y dashboards.
        """
        from models.database import db

        resultados = db.session.query(
            Turno.estado,
            func.count(Turno.id).label('cantidad')
        ).filter(
            Turno.fecha >= fecha_desde,
            Turno.fecha <= fecha_hasta
        ).group_by(
            Turno.estado
        ).all()

        return {r.estado: r.cantidad for r in resultados}

    def get_turnos_por_especialidad(self, fecha_desde: date,
                                    fecha_hasta: date) -> dict:
        """
        Obtiene cantidad de turnos agrupados por especialidad.

        Requiere JOIN con médicos y especialidades.
        """
        from models.database import db
        from models import Especialidad

        resultados = db.session.query(
            Especialidad.nombre,
            func.count(Turno.id).label('cantidad')
        ).join(
            Medico, Turno.medico_id == Medico.id
        ).join(
            Especialidad, Medico.especialidad_id == Especialidad.id
        ).filter(
            Turno.fecha >= fecha_desde,
            Turno.fecha <= fecha_hasta
        ).group_by(
            Especialidad.nombre
        ).all()

        return {r.nombre: r.cantidad for r in resultados}

    def get_tasa_ausentismo(self, fecha_desde: date,
                           fecha_hasta: date) -> float:
        """
        Calcula tasa de ausentismo (% de turnos con estado 'ausente').

        Importante para métricas del sistema.

        Returns:
            Porcentaje de ausentismo (0.0 a 100.0)
        """
        from models.database import db

        total = db.session.query(func.count(Turno.id)).filter(
            Turno.fecha >= fecha_desde,
            Turno.fecha <= fecha_hasta,
            Turno.estado.in_(['completado', 'ausente'])
        ).scalar() or 0

        if total == 0:
            return 0.0

        ausentes = db.session.query(func.count(Turno.id)).filter(
            Turno.fecha >= fecha_desde,
            Turno.fecha <= fecha_hasta,
            Turno.estado == 'ausente'
        ).scalar() or 0

        return (ausentes / total) * 100

    # ==========================================
    # HOOKS (TEMPLATE METHOD)
    # ==========================================

    def _before_create(self, turno: Turno):
        """
        Validaciones antes de crear un turno.

        TEMPLATE METHOD: Hook sobrescrito
        """
        # Validar disponibilidad
        if not self.verificar_disponibilidad_medico(
            turno.medico_id,
            turno.fecha,
            turno.hora,
            turno.duracion_min
        ):
            raise ValueError("El horario no está disponible")

        # Generar código de turno si no existe
        if not turno.codigo_turno:
            turno.codigo_turno = self._generar_codigo_turno(turno.fecha)

    def _generar_codigo_turno(self, fecha: date) -> str:
        """
        Genera código único de turno.

        Formato: T-YYYYMMDD-NNNN
        """
        from models.database import db

        prefijo = f"T-{fecha.strftime('%Y%m%d')}"

        ultimo = db.session.query(Turno).filter(
            Turno.codigo_turno.like(f"{prefijo}%")
        ).order_by(Turno.codigo_turno.desc()).first()

        if ultimo:
            ultimo_numero = int(ultimo.codigo_turno.split('-')[-1])
            nuevo_numero = ultimo_numero + 1
        else:
            nuevo_numero = 1

        return f"{prefijo}-{nuevo_numero:04d}"
