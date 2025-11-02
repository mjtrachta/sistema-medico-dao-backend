"""
Repository para HistoriaClinica
================================

PATRÓN: Repository Pattern
- Encapsula acceso a datos de historias clínicas
"""

from typing import List, Optional
from datetime import date
from models import HistoriaClinica
from repositories.base_repository import BaseRepository


class HistoriaClinicaRepository(BaseRepository[HistoriaClinica]):
    """
    Repository para Historias Clínicas.

    PATRÓN: Repository Pattern + Query Object Pattern
    """

    def __init__(self):
        super().__init__(HistoriaClinica)

    def find_by_paciente(self, paciente_id: int, limit: int = None) -> List[HistoriaClinica]:
        """
        Encuentra historias clínicas de un paciente.

        PATRÓN: Query Object Pattern
        """
        query = self.model_class.query.filter_by(paciente_id=paciente_id)\
            .order_by(HistoriaClinica.fecha_consulta.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    def find_by_medico(self, medico_id: int, fecha_inicio: date = None, fecha_fin: date = None) -> List[HistoriaClinica]:
        """
        Encuentra historias clínicas atendidas por un médico.

        PATRÓN: Query Object Pattern + Specification Pattern
        """
        query = self.model_class.query.filter_by(medico_id=medico_id)

        # Aplicar filtros de fecha si existen
        if fecha_inicio:
            query = query.filter(HistoriaClinica.fecha_consulta >= fecha_inicio)
        if fecha_fin:
            query = query.filter(HistoriaClinica.fecha_consulta <= fecha_fin)

        return query.order_by(HistoriaClinica.fecha_consulta.desc()).all()

    def find_by_turno(self, turno_id: int) -> Optional[HistoriaClinica]:
        """Encuentra historia clínica asociada a un turno."""
        return self.model_class.query.filter_by(turno_id=turno_id).first()

    def exists_for_turno(self, turno_id: int) -> bool:
        """
        Verifica si ya existe historia clínica para un turno.

        PATRÓN: Specification Pattern
        """
        return self.model_class.query.filter_by(turno_id=turno_id).count() > 0
