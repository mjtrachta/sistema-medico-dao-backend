"""
PATRÓN: Repository Pattern + Template Method Pattern
=====================================================

REPOSITORY PATTERN:
------------------
Propósito: Abstraer el acceso a datos, separando la lógica de persistencia
           de la lógica de negocio.

Beneficios:
- Centraliza queries y operaciones de BD
- Facilita testing (se pueden crear repositorios mock)
- Permite cambiar el ORM sin afectar servicios
- Encapsula lógica de acceso a datos compleja

TEMPLATE METHOD PATTERN:
-----------------------
Propósito: Define el esqueleto de operaciones CRUD, permitiendo que
           las subclases personalicen pasos específicos.

Beneficios:
- Evita duplicación de código CRUD básico
- Mantiene consistencia en operaciones
- Permite hooks para validaciones personalizadas

COMBINACIÓN:
-----------
Se combinan ambos patrones porque:
1. Repository abstrae acceso a datos
2. Template Method evita duplicar CRUD en cada repositorio
3. Cada entidad hereda comportamiento base y personaliza lo necesario
"""

from typing import TypeVar, Generic, List, Optional, Dict, Any
from models.database import db
from sqlalchemy import desc, asc

# TypeVar para hacer el repositorio genérico (Generic Repository Pattern)
T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Repositorio base genérico que implementa operaciones CRUD comunes.

    PATRÓN APLICADO: Template Method
    - Define operaciones base (create, update, delete, find)
    - Subclases pueden sobrescribir métodos específicos

    Uso:
        class PacienteRepository(BaseRepository[Paciente]):
            def __init__(self):
                super().__init__(Paciente)
    """

    def __init__(self, model_class: type):
        """
        Constructor que recibe el modelo SQLAlchemy.

        PATRÓN: Dependency Injection
        - El modelo se inyecta, no se instancia internamente
        - Facilita testing y flexibilidad
        """
        self.model_class = model_class

    # ==========================================
    # OPERACIONES DE CONSULTA (READ)
    # ==========================================

    def find_by_id(self, id: int) -> Optional[T]:
        """
        Busca una entidad por su ID.

        Template Method: Método base que puede ser sobrescrito
        si se necesita lógica adicional (ej: soft deletes)
        """
        return db.session.get(self.model_class, id)

    def find_all(self, filters: Dict[str, Any] = None,
                 order_by: str = None,
                 limit: int = None,
                 offset: int = None) -> List[T]:
        """
        Busca todas las entidades con filtros opcionales.

        Args:
            filters: Diccionario de filtros {campo: valor}
            order_by: Campo para ordenar (prefijo '-' para descendente)
            limit: Límite de resultados
            offset: Offset para paginación

        Template Method: Implementación base reutilizable
        """
        query = db.session.query(self.model_class)

        # Aplicar filtros si existen
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)

        # Aplicar ordenamiento
        if order_by:
            if order_by.startswith('-'):
                query = query.order_by(desc(getattr(self.model_class, order_by[1:])))
            else:
                query = query.order_by(asc(getattr(self.model_class, order_by)))

        # Aplicar paginación
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()

    def find_one(self, filters: Dict[str, Any]) -> Optional[T]:
        """
        Busca una única entidad que cumpla los filtros.
        """
        query = db.session.query(self.model_class)

        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)

        return query.first()

    def count(self, filters: Dict[str, Any] = None) -> int:
        """
        Cuenta entidades que cumplen los filtros.
        """
        query = db.session.query(self.model_class)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)

        return query.count()

    def exists(self, filters: Dict[str, Any]) -> bool:
        """
        Verifica si existe al menos una entidad con los filtros dados.
        """
        return self.count(filters) > 0

    # ==========================================
    # OPERACIONES DE ESCRITURA (CREATE/UPDATE/DELETE)
    # ==========================================

    def create(self, entity: T) -> T:
        """
        Crea una nueva entidad.

        Template Method: Hook que puede ser sobrescrito para:
        - Validaciones previas
        - Lógica adicional antes/después de guardar
        - Auditoría

        Args:
            entity: Instancia del modelo a guardar

        Returns:
            Entidad guardada con ID asignado
        """
        # Hook: Validaciones pre-guardado (puede sobrescribirse)
        self._before_create(entity)

        db.session.add(entity)
        db.session.commit()
        db.session.refresh(entity)

        # Hook: Lógica post-guardado (puede sobrescribirse)
        self._after_create(entity)

        return entity

    def update(self, entity: T) -> T:
        """
        Actualiza una entidad existente.

        Template Method: Similar a create, con hooks personalizables
        """
        self._before_update(entity)

        db.session.commit()
        db.session.refresh(entity)

        self._after_update(entity)

        return entity

    def delete(self, entity: T) -> bool:
        """
        Elimina una entidad.

        Template Method: Puede sobrescribirse para soft delete
        """
        self._before_delete(entity)

        db.session.delete(entity)
        db.session.commit()

        self._after_delete(entity)

        return True

    def delete_by_id(self, id: int) -> bool:
        """
        Elimina una entidad por ID.
        """
        entity = self.find_by_id(id)
        if entity:
            return self.delete(entity)
        return False

    # ==========================================
    # HOOKS DEL TEMPLATE METHOD PATTERN
    # ==========================================
    # Estos métodos pueden ser sobrescritos en repositorios específicos
    # para agregar lógica personalizada

    def _before_create(self, entity: T):
        """Hook: Ejecutado antes de crear. Sobrescribir para validaciones."""
        pass

    def _after_create(self, entity: T):
        """Hook: Ejecutado después de crear. Sobrescribir para auditoría/logs."""
        pass

    def _before_update(self, entity: T):
        """Hook: Ejecutado antes de actualizar."""
        pass

    def _after_update(self, entity: T):
        """Hook: Ejecutado después de actualizar."""
        pass

    def _before_delete(self, entity: T):
        """Hook: Ejecutado antes de eliminar."""
        pass

    def _after_delete(self, entity: T):
        """Hook: Ejecutado después de eliminar."""
        pass

    # ==========================================
    # OPERACIONES DE TRANSACCIÓN
    # ==========================================

    def begin_transaction(self):
        """Inicia una transacción explícita."""
        return db.session.begin_nested()

    def commit(self):
        """Confirma la transacción."""
        db.session.commit()

    def rollback(self):
        """Revierte la transacción."""
        db.session.rollback()
