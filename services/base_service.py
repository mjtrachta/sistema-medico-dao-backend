"""
PATRÓN: Service Layer Pattern + Dependency Injection
===================================================

SERVICE LAYER PATTERN:
---------------------
Propósito: Encapsular la lógica de negocio, separándola de
           controllers y repositories.

Ubicación en arquitectura:
    Controller → Service → Repository → Database

Responsabilidades:
- Orquestar operaciones de múltiples repositories
- Aplicar reglas de negocio
- Coordinar transacciones
- Disparar eventos (Observer Pattern)

DEPENDENCY INJECTION:
--------------------
Los servicios reciben repositories por constructor (DI).
Beneficios:
- Facilita testing (inyectar mocks)
- Reduce acoplamiento
- Flexibilidad para cambiar implementaciones

JUSTIFICACIÓN:
-------------
¿Por qué no poner lógica en controllers?
- Controllers se enfocan en HTTP, no en negocio
- Lógica de negocio reutilizable desde múltiples controllers

¿Por qué no poner lógica en models?
- Evita "Fat Models" (modelos gordos)
- Models deben ser solo persistencia

¿Por qué no poner lógica en repositories?
- Repositories solo acceden a datos
- No deben conocer reglas de negocio
"""

from typing import TypeVar, Generic
from repositories.base_repository import BaseRepository

T = TypeVar('T')


class BaseService(Generic[T]):
    """
    Servicio base genérico.

    PATRÓN: Template Method + Dependency Injection

    Cada servicio específico:
    1. Hereda de BaseService
    2. Recibe su repository por constructor (DI)
    3. Implementa lógica de negocio específica
    """

    def __init__(self, repository: BaseRepository[T]):
        """
        Constructor con Dependency Injection.

        Args:
            repository: Repositorio inyectado (permite testing)
        """
        self.repository = repository

    # ==========================================
    # OPERACIONES CRUD CON LÓGICA DE NEGOCIO
    # ==========================================

    def get_by_id(self, id: int):
        """
        Obtiene entidad por ID.

        Aquí se puede agregar lógica adicional:
        - Logging
        - Caché
        - Verificación de permisos
        """
        entity = self.repository.find_by_id(id)
        if not entity:
            raise ValueError(f"Entidad con ID {id} no encontrada")
        return entity

    def get_all(self, filters: dict = None, limit: int = None, offset: int = None):
        """
        Obtiene todas las entidades con filtros opcionales.

        El servicio puede agregar filtros por defecto
        (ej: solo activos, solo del usuario actual, etc.)
        """
        return self.repository.find_all(filters, limit=limit, offset=offset)

    def create(self, entity: T):
        """
        Crea una nueva entidad.

        Template Method: Hook que subclases pueden sobrescribir
        para agregar validaciones o lógica adicional.
        """
        # Hook: Validaciones pre-creación
        self._validate_create(entity)

        # Crear en BD
        created = self.repository.create(entity)

        # Hook: Lógica post-creación (ej: enviar notificación)
        self._after_create(created)

        return created

    def update(self, entity: T):
        """
        Actualiza una entidad existente.

        Similar a create, con hooks personalizables.
        """
        self._validate_update(entity)

        updated = self.repository.update(entity)

        self._after_update(updated)

        return updated

    def delete(self, id: int):
        """
        Elimina una entidad por ID.

        Aquí se pueden implementar:
        - Soft delete (marcar como inactivo)
        - Validaciones de integridad referencial
        - Auditoría
        """
        entity = self.get_by_id(id)

        self._validate_delete(entity)

        result = self.repository.delete(entity)

        self._after_delete(entity)

        return result

    # ==========================================
    # HOOKS (TEMPLATE METHOD)
    # ==========================================
    # Estos métodos pueden ser sobrescritos en servicios específicos

    def _validate_create(self, entity: T):
        """Hook: Validaciones antes de crear."""
        pass

    def _validate_update(self, entity: T):
        """Hook: Validaciones antes de actualizar."""
        pass

    def _validate_delete(self, entity: T):
        """Hook: Validaciones antes de eliminar."""
        pass

    def _after_create(self, entity: T):
        """Hook: Lógica después de crear (notificaciones, logs, etc.)."""
        pass

    def _after_update(self, entity: T):
        """Hook: Lógica después de actualizar."""
        pass

    def _after_delete(self, entity: T):
        """Hook: Lógica después de eliminar."""
        pass

    # ==========================================
    # TRANSACCIONES
    # ==========================================

    def execute_in_transaction(self, func):
        """
        Ejecuta una función en una transacción.

        Útil para operaciones que involucran múltiples entidades.

        Ejemplo:
            service.execute_in_transaction(lambda: [
                service.create_turno(...),
                service.create_notificacion(...)
            ])
        """
        try:
            self.repository.begin_transaction()
            result = func()
            self.repository.commit()
            return result
        except Exception as e:
            self.repository.rollback()
            raise e
