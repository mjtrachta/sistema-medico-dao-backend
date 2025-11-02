"""
Servicio de Recetas Electrónicas
=================================

PATRÓN: Service Layer
"""

from typing import List, Dict
from datetime import date, timedelta
from models import Receta, ItemReceta
from models.database import db
from repositories.receta_repository import RecetaRepository


class RecetaService:
    """
    Servicio para gestionar recetas electrónicas.

    PATRÓN: Service Layer + Dependency Injection
    """

    def __init__(self, receta_repository=None):
        self.receta_repository = receta_repository or RecetaRepository()

    def crear_receta(
        self,
        paciente_id: int,
        medico_id: int,
        items: List[Dict],
        historia_clinica_id: int = None,
        dias_validez: int = 30
    ) -> Receta:
        """
        Crea una receta electrónica con sus ítems.

        PATRÓN: Service Layer
        - Orquesta creación de receta e ítems
        - Transaction handling

        Args:
            paciente_id: ID del paciente
            medico_id: ID del médico
            items: Lista de medicamentos [{'medicamento_id', 'nombre', 'dosis', 'frecuencia', 'cantidad', 'duracion_dias', 'instrucciones'}]
            historia_clinica_id: ID de historia clínica asociada (opcional)
            dias_validez: Días de validez de la receta

        Returns:
            Receta creada con ítems

        Raises:
            ValueError: Si validaciones fallan
        """
        if not items:
            raise ValueError("La receta debe tener al menos un medicamento")

        # Generar código único
        codigo = self.receta_repository.generar_codigo_receta()

        # Calcular fecha de vencimiento
        valida_hasta = date.today() + timedelta(days=dias_validez)

        # Crear receta
        receta = Receta(
            codigo_receta=codigo,
            paciente_id=paciente_id,
            medico_id=medico_id,
            historia_clinica_id=historia_clinica_id,
            fecha=date.today(),
            estado='activa',
            valida_hasta=valida_hasta
        )

        # Agregar items
        for item_data in items:
            item = ItemReceta(
                medicamento_id=item_data.get('medicamento_id'),
                nombre_medicamento=item_data['nombre_medicamento'],
                dosis=item_data.get('dosis'),
                frecuencia=item_data.get('frecuencia'),
                cantidad=item_data.get('cantidad'),
                duracion_dias=item_data.get('duracion_dias'),
                instrucciones=item_data.get('instrucciones')
            )
            receta.items.append(item)

        return self.receta_repository.create(receta)

    def cancelar_receta(self, receta_id: int, motivo: str = None) -> Receta:
        """
        Cancela una receta.

        PATRÓN: Business Logic encapsulation
        """
        receta = self.receta_repository.find_by_id(receta_id)
        if not receta:
            raise ValueError(f"Receta {receta_id} no encontrada")

        if receta.estado == 'cancelada':
            raise ValueError("La receta ya está cancelada")

        receta.estado = 'cancelada'
        return self.receta_repository.update(receta)

    def obtener_recetas_paciente(self, paciente_id: int, solo_activas: bool = False) -> List[Receta]:
        """Obtiene recetas de un paciente."""
        if solo_activas:
            return self.receta_repository.find_activas(paciente_id)
        return self.receta_repository.find_by_paciente(paciente_id)

    def obtener_recetas_medico(self, medico_id: int) -> List[Receta]:
        """Obtiene recetas emitidas por un médico."""
        return self.receta_repository.find_by_medico(medico_id)

    def obtener_todas(self, limit: int = 100) -> List[Receta]:
        """Obtiene todas las recetas (admin)."""
        return self.receta_repository.find_all(limit=limit)

    def get_by_id(self, receta_id: int) -> Receta:
        """Obtiene una receta por ID."""
        receta = self.receta_repository.find_by_id(receta_id)
        if not receta:
            raise ValueError(f"Receta {receta_id} no encontrada")
        return receta
