"""
Servicio de Historia Clínica
=============================

PATRÓN: Service Layer Pattern
- Orquesta creación de historias clínicas
- Valida reglas de negocio
"""

from typing import Optional
from datetime import date
from models import HistoriaClinica, Turno
from repositories.historia_clinica_repository import HistoriaClinicaRepository
from repositories.turno_repository import TurnoRepository


class HistoriaClinicaService:
    """
    Servicio para gestionar historias clínicas.

    PATRÓN: Service Layer + Dependency Injection
    """

    def __init__(self, historia_repository=None, turno_repository=None):
        """
        Constructor con Dependency Injection.

        PATRÓN: Dependency Injection
        - Permite inyectar repositories (facilita testing)
        """
        self.historia_repository = historia_repository or HistoriaClinicaRepository()
        self.turno_repository = turno_repository or TurnoRepository()

    def crear_desde_turno(
        self,
        turno_id: int,
        diagnostico: str,
        tratamiento: str = None,
        observaciones: str = None
    ) -> HistoriaClinica:
        """
        Crea historia clínica a partir de un turno completado.

        VALIDACIONES (Specification Pattern):
        1. Turno debe existir
        2. Turno debe estar en estado 'completado'
        3. No debe existir HC previa para ese turno

        Args:
            turno_id: ID del turno
            diagnostico: Diagnóstico médico
            tratamiento: Tratamiento prescrito
            observaciones: Observaciones adicionales

        Returns:
            HistoriaClinica creada

        Raises:
            ValueError: Si validaciones fallan
        """
        # Validar que turno existe
        turno = self.turno_repository.find_by_id(turno_id)
        if not turno:
            raise ValueError(f"Turno {turno_id} no encontrado")

        # Validar estado del turno - debe estar confirmado o completado
        if turno.estado not in ['confirmado', 'completado']:
            raise ValueError(f"Turno debe estar en estado 'confirmado' o 'completado'. Estado actual: {turno.estado}")

        # Validar que no exista HC previa
        if self.historia_repository.exists_for_turno(turno_id):
            raise ValueError(f"Ya existe historia clínica para el turno {turno_id}")

        # Crear historia clínica
        historia = HistoriaClinica(
            turno_id=turno_id,
            paciente_id=turno.paciente_id,
            medico_id=turno.medico_id,
            fecha_consulta=turno.fecha,
            motivo_consulta=turno.motivo_consulta,
            diagnostico=diagnostico,
            tratamiento=tratamiento,
            observaciones=observaciones
        )

        # Guardar historia clínica
        historia_creada = self.historia_repository.create(historia)

        # Marcar turno como completado si estaba confirmado
        if turno.estado == 'confirmado':
            turno.estado = 'completado'
            self.turno_repository.update(turno)

        return historia_creada

    def obtener_historial_paciente(self, paciente_id: int, limit: int = 10) -> list:
        """
        Obtiene historial completo de un paciente.

        PATRÓN: Facade Pattern
        - Simplifica obtención de historial
        """
        return self.historia_repository.find_by_paciente(paciente_id, limit)

    def actualizar(
        self,
        historia_id: int,
        diagnostico: str = None,
        tratamiento: str = None,
        observaciones: str = None
    ) -> HistoriaClinica:
        """
        Actualiza una historia clínica existente.

        Args:
            historia_id: ID de la historia clínica
            diagnostico: Nuevo diagnóstico (opcional)
            tratamiento: Nuevo tratamiento (opcional)
            observaciones: Nuevas observaciones (opcional)

        Returns:
            HistoriaClinica actualizada

        Raises:
            ValueError: Si historia no existe
        """
        historia = self.historia_repository.find_by_id(historia_id)
        if not historia:
            raise ValueError(f"Historia clínica {historia_id} no encontrada")

        # Actualizar campos si se proveen
        if diagnostico is not None:
            historia.diagnostico = diagnostico
        if tratamiento is not None:
            historia.tratamiento = tratamiento
        if observaciones is not None:
            historia.observaciones = observaciones

        return self.historia_repository.update(historia)

    def obtener_historias_medico(self, medico_id: int, limit: int = 100) -> list:
        """
        Obtiene historias clínicas atendidas por un médico.

        Args:
            medico_id: ID del médico
            limit: Límite de resultados

        Returns:
            Lista de historias clínicas del médico
        """
        historias = self.historia_repository.find_by_medico(medico_id)
        # Aplicar limit manualmente ya que find_by_medico no lo acepta
        return historias[:limit] if limit else historias

    def obtener_todas(self, limit: int = 100) -> list:
        """
        Obtiene todas las historias clínicas (admin).

        Args:
            limit: Límite de resultados

        Returns:
            Lista de todas las historias clínicas
        """
        return self.historia_repository.find_all(limit=limit, order_by='-fecha_consulta')

    def get_by_id(self, historia_id: int) -> HistoriaClinica:
        """
        Obtiene una historia clínica por ID.

        Args:
            historia_id: ID de la historia clínica

        Returns:
            HistoriaClinica encontrada

        Raises:
            ValueError: Si historia no existe
        """
        historia = self.historia_repository.find_by_id(historia_id)
        if not historia:
            raise ValueError(f"Historia clínica {historia_id} no encontrada")
        return historia
