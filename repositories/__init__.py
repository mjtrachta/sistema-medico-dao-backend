"""
Capa de Repositorios - Repository Pattern
=========================================

Esta capa implementa el Repository Pattern para abstraer
el acceso a datos de la lógica de negocio.

Estructura:
- base_repository.py: Repositorio genérico con Template Method
- *_repository.py: Repositorios específicos por entidad

PATRÓN APLICADO: Repository Pattern
BENEFICIOS:
- Separa lógica de persistencia de lógica de negocio
- Facilita testing (repositories mock)
- Centraliza queries complejas
- Permite cambiar ORM sin afectar servicios
"""

from .base_repository import BaseRepository
from .paciente_repository import PacienteRepository
from .turno_repository import TurnoRepository

__all__ = [
    'BaseRepository',
    'PacienteRepository',
    'TurnoRepository'
]
