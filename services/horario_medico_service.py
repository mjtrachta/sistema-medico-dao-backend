"""
Servicio de Horarios de Médicos
=================================

PATRÓN: Service Layer Pattern
"""

from typing import List, Optional
from datetime import time
from models import HorarioMedico
from repositories.horario_medico_repository import HorarioMedicoRepository


class HorarioMedicoService:
    """
    Servicio para gestionar horarios de médicos.

    Incluye validaciones de negocio:
    - No superposición de horarios del mismo médico
    - Validación de rangos horarios
    """

    def __init__(self, repository=None):
        self.repository = repository or HorarioMedicoRepository()

    def crear_horario(
        self,
        medico_id: int,
        ubicacion_id: int,
        dia_semana: str,
        hora_inicio: time,
        hora_fin: time
    ) -> HorarioMedico:
        """
        Crea un nuevo horario para un médico.

        VALIDACIONES:
        1. hora_fin debe ser mayor que hora_inicio
        2. No debe haber superposición con otros horarios del médico

        Args:
            medico_id: ID del médico
            ubicacion_id: ID de la ubicación/sede
            dia_semana: Día de la semana (lunes, martes, miércoles, jueves, viernes, sábado, domingo)
            hora_inicio: Hora de inicio
            hora_fin: Hora de fin

        Returns:
            HorarioMedico creado

        Raises:
            ValueError: Si las validaciones fallan
        """
        # Validar día de semana
        dias_validos = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
        if dia_semana.lower() not in dias_validos:
            raise ValueError(f"Día de semana inválido. Debe ser uno de: {', '.join(dias_validos)}")

        # Validar que hora_fin > hora_inicio
        if hora_fin <= hora_inicio:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")

        # Validar superposición
        if self.repository.check_superposicion(medico_id, dia_semana.lower(), hora_inicio, hora_fin):
            horarios_conflicto = self.repository.get_horarios_superpuestos(
                medico_id, dia_semana.lower(), hora_inicio, hora_fin
            )
            conflictos = [
                f"{h.dia_semana} {h.hora_inicio.strftime('%H:%M')}-{h.hora_fin.strftime('%H:%M')} en {h.ubicacion.nombre if h.ubicacion else 'sin ubicación'}"
                for h in horarios_conflicto
            ]
            raise ValueError(
                f"El médico ya tiene horarios en ese rango de tiempo. Conflictos: {'; '.join(conflictos)}"
            )

        # Crear horario
        horario = HorarioMedico(
            medico_id=medico_id,
            ubicacion_id=ubicacion_id,
            dia_semana=dia_semana.lower(),
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            activo=True
        )

        return self.repository.create(horario)

    def actualizar_horario(
        self,
        horario_id: int,
        dia_semana: Optional[str] = None,
        hora_inicio: Optional[time] = None,
        hora_fin: Optional[time] = None,
        ubicacion_id: Optional[int] = None
    ) -> HorarioMedico:
        """
        Actualiza un horario existente.

        Aplica las mismas validaciones que crear_horario.

        Args:
            horario_id: ID del horario a actualizar
            dia_semana: Nuevo día (opcional)
            hora_inicio: Nueva hora inicio (opcional)
            hora_fin: Nueva hora fin (opcional)
            ubicacion_id: Nueva ubicación (opcional)

        Returns:
            HorarioMedico actualizado

        Raises:
            ValueError: Si las validaciones fallan
        """
        horario = self.repository.find_by_id(horario_id)
        if not horario:
            raise ValueError(f"Horario {horario_id} no encontrado")

        # Usar valores actuales si no se proporcionan nuevos
        nuevo_dia = dia_semana.lower() if dia_semana else horario.dia_semana
        nueva_hora_inicio = hora_inicio if hora_inicio else horario.hora_inicio
        nueva_hora_fin = hora_fin if hora_fin else horario.hora_fin

        # Validar que hora_fin > hora_inicio
        if nueva_hora_fin <= nueva_hora_inicio:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")

        # Validar superposición (excluyendo el horario actual)
        if self.repository.check_superposicion(
            horario.medico_id,
            nuevo_dia,
            nueva_hora_inicio,
            nueva_hora_fin,
            excluir_id=horario_id
        ):
            raise ValueError("El horario se superpone con otros horarios existentes del médico")

        # Actualizar campos
        if dia_semana:
            horario.dia_semana = nuevo_dia
        if hora_inicio:
            horario.hora_inicio = hora_inicio
        if hora_fin:
            horario.hora_fin = hora_fin
        if ubicacion_id:
            horario.ubicacion_id = ubicacion_id

        return self.repository.update(horario)

    def obtener_horarios_medico(self, medico_id: int, solo_activos: bool = True) -> List[HorarioMedico]:
        """Obtiene todos los horarios de un médico."""
        return self.repository.find_by_medico(medico_id, solo_activos)

    def obtener_horarios_ubicacion(self, ubicacion_id: int, solo_activos: bool = True) -> List[HorarioMedico]:
        """Obtiene todos los horarios de una ubicación."""
        return self.repository.find_by_ubicacion(ubicacion_id, solo_activos)

    def obtener_por_id(self, horario_id: int) -> HorarioMedico:
        """Obtiene un horario por ID."""
        horario = self.repository.find_by_id(horario_id)
        if not horario:
            raise ValueError(f"Horario {horario_id} no encontrado")
        return horario

    def desactivar_horario(self, horario_id: int) -> HorarioMedico:
        """
        Desactiva un horario (soft delete).

        Args:
            horario_id: ID del horario

        Returns:
            Horario desactivado
        """
        horario = self.repository.find_by_id(horario_id)
        if not horario:
            raise ValueError(f"Horario {horario_id} no encontrado")

        horario.activo = False
        return self.repository.update(horario)

    def desactivar_todos_medico(self, medico_id: int) -> int:
        """
        Desactiva todos los horarios de un médico.

        Se usa cuando se da de baja al médico.

        Args:
            medico_id: ID del médico

        Returns:
            Cantidad de horarios desactivados
        """
        return self.repository.desactivar_horarios_medico(medico_id)
