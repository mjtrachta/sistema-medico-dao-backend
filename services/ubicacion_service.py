"""
Servicio de Ubicaciones
========================

PATRÓN: Service Layer Pattern
"""

from typing import List, Optional
from models import Ubicacion
from repositories.ubicacion_repository import UbicacionRepository


class UbicacionService:
    """
    Servicio para gestionar ubicaciones/sedes.

    Incluye validaciones de negocio:
    - No duplicación de nombres de ubicaciones
    - Validación de datos requeridos
    """

    def __init__(self, repository=None):
        self.repository = repository or UbicacionRepository()

    def crear_ubicacion(
        self,
        nombre: str,
        direccion: str,
        ciudad: str,
        telefono: Optional[str] = None
    ) -> Ubicacion:
        """
        Crea una nueva ubicación/sede.

        VALIDACIONES:
        1. Nombre no debe estar vacío
        2. Nombre no debe estar duplicado
        3. Dirección y ciudad son requeridas

        Args:
            nombre: Nombre de la ubicación
            direccion: Dirección física
            ciudad: Ciudad donde se encuentra
            telefono: Teléfono de contacto (opcional)

        Returns:
            Ubicacion creada

        Raises:
            ValueError: Si las validaciones fallan
        """
        # Validar campos requeridos
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la ubicación es requerido")

        if not direccion or not direccion.strip():
            raise ValueError("La dirección es requerida")

        if not ciudad or not ciudad.strip():
            raise ValueError("La ciudad es requerida")

        # Validar nombre único
        if self.repository.existe_nombre(nombre.strip()):
            raise ValueError(f"Ya existe una ubicación con el nombre '{nombre}'")

        # Crear ubicación
        ubicacion = Ubicacion(
            nombre=nombre.strip(),
            direccion=direccion.strip(),
            ciudad=ciudad.strip(),
            telefono=telefono.strip() if telefono else None,
            activo=True
        )

        return self.repository.create(ubicacion)

    def actualizar_ubicacion(
        self,
        ubicacion_id: int,
        nombre: Optional[str] = None,
        direccion: Optional[str] = None,
        ciudad: Optional[str] = None,
        telefono: Optional[str] = None
    ) -> Ubicacion:
        """
        Actualiza una ubicación existente.

        Aplica las mismas validaciones que crear_ubicacion.

        Args:
            ubicacion_id: ID de la ubicación a actualizar
            nombre: Nuevo nombre (opcional)
            direccion: Nueva dirección (opcional)
            ciudad: Nueva ciudad (opcional)
            telefono: Nuevo teléfono (opcional)

        Returns:
            Ubicacion actualizada

        Raises:
            ValueError: Si las validaciones fallan
        """
        ubicacion = self.repository.find_by_id(ubicacion_id)
        if not ubicacion:
            raise ValueError(f"Ubicación {ubicacion_id} no encontrada")

        # Validar nombre único si se está cambiando
        if nombre and nombre.strip() != ubicacion.nombre:
            if self.repository.existe_nombre(nombre.strip(), excluir_id=ubicacion_id):
                raise ValueError(f"Ya existe una ubicación con el nombre '{nombre}'")
            ubicacion.nombre = nombre.strip()

        if direccion:
            ubicacion.direccion = direccion.strip()

        if ciudad:
            ubicacion.ciudad = ciudad.strip()

        if telefono is not None:  # Permitir vacío para borrar teléfono
            ubicacion.telefono = telefono.strip() if telefono else None

        return self.repository.update(ubicacion)

    def obtener_todas_activas(self) -> List[Ubicacion]:
        """Obtiene todas las ubicaciones activas ordenadas por nombre."""
        return self.repository.find_all_active()

    def obtener_por_id(self, ubicacion_id: int) -> Ubicacion:
        """
        Obtiene una ubicación por ID.

        Args:
            ubicacion_id: ID de la ubicación

        Returns:
            Ubicacion encontrada

        Raises:
            ValueError: Si ubicación no existe
        """
        ubicacion = self.repository.find_by_id(ubicacion_id)
        if not ubicacion:
            raise ValueError(f"Ubicación {ubicacion_id} no encontrada")
        return ubicacion

    def buscar_por_nombre(self, termino: str) -> List[Ubicacion]:
        """
        Busca ubicaciones por nombre (búsqueda parcial).

        Args:
            termino: Término de búsqueda

        Returns:
            Lista de ubicaciones que coinciden
        """
        if not termino or not termino.strip():
            return self.obtener_todas_activas()
        return self.repository.search_by_nombre(termino.strip())

    def buscar_por_ciudad(self, ciudad: str) -> List[Ubicacion]:
        """
        Busca ubicaciones por ciudad.

        Args:
            ciudad: Nombre de la ciudad

        Returns:
            Lista de ubicaciones en esa ciudad
        """
        if not ciudad or not ciudad.strip():
            return []
        return self.repository.search_by_ciudad(ciudad.strip())

    def desactivar_ubicacion(self, ubicacion_id: int) -> Ubicacion:
        """
        Desactiva una ubicación (soft delete).

        IMPORTANTE: Los horarios asociados NO se desactivan automáticamente.
        El admin debe decidir qué hacer con los horarios existentes.

        Args:
            ubicacion_id: ID de la ubicación

        Returns:
            Ubicacion desactivada

        Raises:
            ValueError: Si ubicación no existe
        """
        ubicacion = self.repository.find_by_id(ubicacion_id)
        if not ubicacion:
            raise ValueError(f"Ubicación {ubicacion_id} no encontrada")

        ubicacion.activo = False
        return self.repository.update(ubicacion)

    def reactivar_ubicacion(self, ubicacion_id: int) -> Ubicacion:
        """
        Reactiva una ubicación previamente desactivada.

        Args:
            ubicacion_id: ID de la ubicación

        Returns:
            Ubicacion reactivada

        Raises:
            ValueError: Si ubicación no existe
        """
        ubicacion = self.repository.find_by_id(ubicacion_id)
        if not ubicacion:
            raise ValueError(f"Ubicación {ubicacion_id} no encontrada")

        ubicacion.activo = True
        return self.repository.update(ubicacion)
