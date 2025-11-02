"""
Repository para HorarioMedico
===============================

PATRÓN: Repository Pattern
"""

from typing import List, Optional
from datetime import time
from models import HorarioMedico
from repositories.base_repository import BaseRepository
from models.database import db
from sqlalchemy import and_, or_


class HorarioMedicoRepository(BaseRepository[HorarioMedico]):
    """
    Repository para Horarios de Médicos.

    Incluye validaciones para evitar superposición de horarios.
    """

    def __init__(self):
        super().__init__(HorarioMedico)

    def find_by_medico(self, medico_id: int, solo_activos: bool = True) -> List[HorarioMedico]:
        """
        Encuentra todos los horarios de un médico.

        Args:
            medico_id: ID del médico
            solo_activos: Si True, solo retorna horarios activos

        Returns:
            Lista de horarios del médico
        """
        query = self.model_class.query.filter_by(medico_id=medico_id)

        if solo_activos:
            query = query.filter_by(activo=True)

        return query.order_by(
            HorarioMedico.dia_semana,
            HorarioMedico.hora_inicio
        ).all()

    def find_by_ubicacion(self, ubicacion_id: int, solo_activos: bool = True) -> List[HorarioMedico]:
        """
        Encuentra todos los horarios en una ubicación.

        Args:
            ubicacion_id: ID de la ubicación
            solo_activos: Si True, solo retorna horarios activos

        Returns:
            Lista de horarios en la ubicación
        """
        query = self.model_class.query.filter_by(ubicacion_id=ubicacion_id)

        if solo_activos:
            query = query.filter_by(activo=True)

        return query.order_by(
            HorarioMedico.dia_semana,
            HorarioMedico.hora_inicio
        ).all()

    def find_by_medico_ubicacion_dia(
        self,
        medico_id: int,
        ubicacion_id: int,
        dia_semana: str,
        solo_activos: bool = True
    ) -> List[HorarioMedico]:
        """
        Encuentra horarios de un médico en una ubicación y día específicos.

        Args:
            medico_id: ID del médico
            ubicacion_id: ID de la ubicación
            dia_semana: Día de la semana (lunes, martes, etc.)
            solo_activos: Si True, solo retorna horarios activos

        Returns:
            Lista de horarios que cumplen los criterios
        """
        query = self.model_class.query.filter_by(
            medico_id=medico_id,
            ubicacion_id=ubicacion_id,
            dia_semana=dia_semana
        )

        if solo_activos:
            query = query.filter_by(activo=True)

        return query.order_by(HorarioMedico.hora_inicio).all()

    def check_superposicion(
        self,
        medico_id: int,
        dia_semana: str,
        hora_inicio: time,
        hora_fin: time,
        excluir_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si un horario se superpone con horarios existentes del médico.

        VALIDACIÓN CRÍTICA: Un médico no puede estar en dos lugares al mismo tiempo.

        Args:
            medico_id: ID del médico
            dia_semana: Día de la semana
            hora_inicio: Hora de inicio del nuevo horario
            hora_fin: Hora de fin del nuevo horario
            excluir_id: ID de horario a excluir (para edición)

        Returns:
            True si hay superposición, False si no hay conflicto
        """
        query = self.model_class.query.filter(
            HorarioMedico.medico_id == medico_id,
            HorarioMedico.dia_semana == dia_semana,
            HorarioMedico.activo == True,
            # Verificar superposición de rangos de tiempo
            or_(
                # El nuevo horario empieza durante un horario existente
                and_(
                    HorarioMedico.hora_inicio <= hora_inicio,
                    HorarioMedico.hora_fin > hora_inicio
                ),
                # El nuevo horario termina durante un horario existente
                and_(
                    HorarioMedico.hora_inicio < hora_fin,
                    HorarioMedico.hora_fin >= hora_fin
                ),
                # El nuevo horario engloba completamente un horario existente
                and_(
                    HorarioMedico.hora_inicio >= hora_inicio,
                    HorarioMedico.hora_fin <= hora_fin
                )
            )
        )

        # Excluir el horario actual si estamos editando
        if excluir_id:
            query = query.filter(HorarioMedico.id != excluir_id)

        return query.count() > 0

    def get_horarios_superpuestos(
        self,
        medico_id: int,
        dia_semana: str,
        hora_inicio: time,
        hora_fin: time,
        excluir_id: Optional[int] = None
    ) -> List[HorarioMedico]:
        """
        Obtiene los horarios que se superponen con el rango especificado.

        Útil para mostrar al usuario qué horarios están en conflicto.

        Args:
            medico_id: ID del médico
            dia_semana: Día de la semana
            hora_inicio: Hora de inicio
            hora_fin: Hora de fin
            excluir_id: ID de horario a excluir

        Returns:
            Lista de horarios en conflicto
        """
        query = self.model_class.query.filter(
            HorarioMedico.medico_id == medico_id,
            HorarioMedico.dia_semana == dia_semana,
            HorarioMedico.activo == True,
            or_(
                and_(
                    HorarioMedico.hora_inicio <= hora_inicio,
                    HorarioMedico.hora_fin > hora_inicio
                ),
                and_(
                    HorarioMedico.hora_inicio < hora_fin,
                    HorarioMedico.hora_fin >= hora_fin
                ),
                and_(
                    HorarioMedico.hora_inicio >= hora_inicio,
                    HorarioMedico.hora_fin <= hora_fin
                )
            )
        )

        if excluir_id:
            query = query.filter(HorarioMedico.id != excluir_id)

        return query.all()

    def desactivar_horarios_medico(self, medico_id: int) -> int:
        """
        Desactiva todos los horarios de un médico.

        Se usa cuando se da de baja al médico.

        Args:
            medico_id: ID del médico

        Returns:
            Cantidad de horarios desactivados
        """
        count = self.model_class.query.filter_by(
            medico_id=medico_id,
            activo=True
        ).update({'activo': False})

        db.session.commit()
        return count
