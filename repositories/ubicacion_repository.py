"""
Repository para Ubicacion
===========================

PATRÓN: Repository Pattern
"""

from typing import List, Optional
from models import Ubicacion
from repositories.base_repository import BaseRepository


class UbicacionRepository(BaseRepository[Ubicacion]):
    """
    Repository para Ubicaciones/Sedes.

    Gestiona las sedes donde atienden los médicos.
    """

    def __init__(self):
        super().__init__(Ubicacion)

    def find_all_active(self) -> List[Ubicacion]:
        """
        Encuentra todas las ubicaciones activas.

        Returns:
            Lista de ubicaciones activas ordenadas por nombre
        """
        return self.model_class.query.filter_by(activo=True)\
            .order_by(Ubicacion.nombre).all()

    def find_by_nombre(self, nombre: str) -> Optional[Ubicacion]:
        """
        Busca una ubicación por nombre exacto.

        Args:
            nombre: Nombre de la ubicación

        Returns:
            Ubicación encontrada o None
        """
        return self.model_class.query.filter_by(nombre=nombre).first()

    def search_by_nombre(self, termino: str) -> List[Ubicacion]:
        """
        Busca ubicaciones por nombre (búsqueda parcial).

        Args:
            termino: Término de búsqueda

        Returns:
            Lista de ubicaciones que coinciden
        """
        return self.model_class.query.filter(
            Ubicacion.nombre.ilike(f'%{termino}%'),
            Ubicacion.activo == True
        ).order_by(Ubicacion.nombre).all()

    def search_by_ciudad(self, ciudad: str) -> List[Ubicacion]:
        """
        Busca ubicaciones por ciudad.

        Args:
            ciudad: Nombre de la ciudad

        Returns:
            Lista de ubicaciones en esa ciudad
        """
        return self.model_class.query.filter(
            Ubicacion.ciudad.ilike(f'%{ciudad}%'),
            Ubicacion.activo == True
        ).order_by(Ubicacion.nombre).all()

    def existe_nombre(self, nombre: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verifica si ya existe una ubicación con ese nombre.

        Args:
            nombre: Nombre a verificar
            excluir_id: ID a excluir (para edición)

        Returns:
            True si existe, False si no
        """
        query = self.model_class.query.filter_by(nombre=nombre, activo=True)

        if excluir_id:
            query = query.filter(Ubicacion.id != excluir_id)

        return query.count() > 0
