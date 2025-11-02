"""
Repository para Recetas
=======================

PATRÓN: Repository Pattern
"""

from typing import List
from datetime import date, datetime
from models import Receta
from repositories.base_repository import BaseRepository


class RecetaRepository(BaseRepository[Receta]):
    """Repository para Recetas médicas."""

    def __init__(self):
        super().__init__(Receta)

    def generar_codigo_receta(self) -> str:
        """
        Genera código único para receta.

        PATRÓN: Template Method (hook personalizado)
        Formato: R-YYYYMMDD-NNNN
        """
        fecha_str = datetime.utcnow().strftime('%Y%m%d')

        # Contar recetas del día
        count = self.model_class.query.filter(
            Receta.codigo_receta.like(f'R-{fecha_str}-%')
        ).count()

        numero = str(count + 1).zfill(4)
        return f'R-{fecha_str}-{numero}'

    def find_by_paciente(self, paciente_id: int) -> List[Receta]:
        """Encuentra recetas de un paciente."""
        return self.model_class.query.filter_by(paciente_id=paciente_id)\
            .order_by(Receta.fecha.desc()).all()

    def find_by_medico(self, medico_id: int) -> List[Receta]:
        """Encuentra recetas emitidas por un médico."""
        return self.model_class.query.filter_by(medico_id=medico_id)\
            .order_by(Receta.fecha.desc()).all()

    def find_activas(self, paciente_id: int = None) -> List[Receta]:
        """
        Encuentra recetas activas (no vencidas).

        PATRÓN: Specification Pattern
        """
        query = self.model_class.query.filter_by(estado='activa')

        if paciente_id:
            query = query.filter_by(paciente_id=paciente_id)

        # Filtrar por validez
        hoy = date.today()
        query = query.filter(
            (Receta.valida_hasta.is_(None)) | (Receta.valida_hasta >= hoy)
        )

        return query.order_by(Receta.fecha.desc()).all()
