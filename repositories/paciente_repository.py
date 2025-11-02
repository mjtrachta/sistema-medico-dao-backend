"""
PATRÓN: Repository Pattern (Implementación Específica)
======================================================

Este repositorio extiende BaseRepository agregando:
1. Queries específicas de pacientes
2. Validaciones de unicidad (DNI, historia clínica)
3. Búsquedas complejas

HERENCIA DE PATRONES:
- Repository Pattern (del base)
- Template Method (hooks personalizados)
- Query Object (métodos de búsqueda específicos)
"""

from typing import List, Optional
from models import Paciente
from repositories.base_repository import BaseRepository
from datetime import date, datetime


class PacienteRepository(BaseRepository[Paciente]):
    """
    Repositorio específico para Paciente.

    Extiende BaseRepository con operaciones específicas:
    - Búsqueda por documento
    - Búsqueda por historia clínica
    - Validación de unicidad
    - Estadísticas de pacientes
    """

    def __init__(self):
        """
        Constructor que inyecta el modelo Paciente al repositorio base.

        PATRÓN: Dependency Injection
        - El modelo se pasa al constructor padre
        """
        super().__init__(Paciente)

    # ==========================================
    # QUERIES ESPECÍFICAS DE PACIENTES
    # ==========================================

    def find_by_documento(self, tipo_documento: str, nro_documento: str) -> Optional[Paciente]:
        """
        Busca paciente por tipo y número de documento.

        Este es un Query Object Pattern:
        - Encapsula una query específica en un método
        - Reutilizable en toda la aplicación
        - Nombre descriptivo del propósito

        Args:
            tipo_documento: Tipo de documento (DNI, LC, LE, Pasaporte)
            nro_documento: Número de documento

        Returns:
            Paciente si existe, None si no
        """
        return self.find_one({
            'tipo_documento': tipo_documento,
            'nro_documento': nro_documento,
            'activo': True
        })

    def find_by_historia_clinica(self, nro_historia_clinica: str) -> Optional[Paciente]:
        """
        Busca paciente por número de historia clínica.

        Query Object Pattern: Query nombrada y reutilizable
        """
        return self.find_one({
            'nro_historia_clinica': nro_historia_clinica,
            'activo': True
        })

    def find_by_email(self, email: str) -> Optional[Paciente]:
        """Busca paciente por email."""
        return self.find_one({'email': email, 'activo': True})

    def find_activos(self, limit: int = None, offset: int = None) -> List[Paciente]:
        """
        Busca todos los pacientes activos.

        Args:
            limit: Cantidad máxima de resultados
            offset: Offset para paginación

        Returns:
            Lista de pacientes activos ordenados por apellido, nombre
        """
        return self.find_all(
            filters={'activo': True},
            order_by='apellido',
            limit=limit,
            offset=offset
        )

    def search_by_nombre(self, nombre: str, apellido: str = None) -> List[Paciente]:
        """
        Busca pacientes por nombre y/o apellido (búsqueda parcial).

        PATRÓN: Query Object con criterios dinámicos

        Args:
            nombre: Nombre a buscar (parcial)
            apellido: Apellido a buscar (parcial, opcional)

        Returns:
            Lista de pacientes que coinciden
        """
        from models.database import db

        query = db.session.query(Paciente).filter(Paciente.activo == True)

        if nombre:
            query = query.filter(Paciente.nombre.ilike(f'%{nombre}%'))

        if apellido:
            query = query.filter(Paciente.apellido.ilike(f'%{apellido}%'))

        return query.order_by(Paciente.apellido, Paciente.nombre).all()

    def get_pacientes_por_edad(self, edad_min: int, edad_max: int) -> List[Paciente]:
        """
        Busca pacientes en un rango de edad.

        Este método demuestra cálculos en queries:
        - Calcula edad basado en fecha de nacimiento
        - Filtra por rango
        """
        from models.database import db
        from sqlalchemy import extract

        hoy = date.today()
        anio_nacimiento_max = hoy.year - edad_min
        anio_nacimiento_min = hoy.year - edad_max

        query = db.session.query(Paciente).filter(
            Paciente.activo == True,
            extract('year', Paciente.fecha_nacimiento) >= anio_nacimiento_min,
            extract('year', Paciente.fecha_nacimiento) <= anio_nacimiento_max
        )

        return query.all()

    # ==========================================
    # VALIDACIONES DE UNICIDAD
    # ==========================================
    # Estos métodos se usan en la capa de servicio
    # para validar antes de crear/actualizar

    def existe_documento(self, tipo_documento: str, nro_documento: str,
                        excluir_id: int = None) -> bool:
        """
        Verifica si ya existe un paciente con el documento dado.

        PATRÓN: Specification Pattern (simplificado)
        - Encapsula regla de negocio: documento debe ser único
        - Reutilizable en validaciones

        Args:
            tipo_documento: Tipo de documento
            nro_documento: Número de documento
            excluir_id: ID a excluir (útil en actualizaciones)

        Returns:
            True si existe, False si no
        """
        from models.database import db

        query = db.session.query(Paciente).filter(
            Paciente.tipo_documento == tipo_documento,
            Paciente.nro_documento == nro_documento
        )

        if excluir_id:
            query = query.filter(Paciente.id != excluir_id)

        return query.count() > 0

    def existe_historia_clinica(self, nro_historia_clinica: str,
                               excluir_id: int = None) -> bool:
        """
        Verifica si ya existe un paciente con la historia clínica dada.

        Specification Pattern: Regla de negocio encapsulada
        """
        from models.database import db

        query = db.session.query(Paciente).filter(
            Paciente.nro_historia_clinica == nro_historia_clinica
        )

        if excluir_id:
            query = query.filter(Paciente.id != excluir_id)

        return query.count() > 0

    # ==========================================
    # SOBRESCRITURA DE HOOKS (TEMPLATE METHOD)
    # ==========================================

    def _before_create(self, paciente: Paciente):
        """
        Hook ejecutado antes de crear un paciente.

        PATRÓN: Template Method (hook sobrescrito)
        - Validaciones específicas de paciente
        - Generación automática de historia clínica si no existe
        """
        # Validar que no exista el documento
        if self.existe_documento(paciente.tipo_documento, paciente.nro_documento):
            raise ValueError(f"Ya existe un paciente con documento {paciente.tipo_documento} {paciente.nro_documento}")

        # Generar número de historia clínica si no existe
        if not paciente.nro_historia_clinica:
            paciente.nro_historia_clinica = self._generar_nro_historia_clinica()

        # Validar que no exista la historia clínica
        if self.existe_historia_clinica(paciente.nro_historia_clinica):
            raise ValueError(f"Ya existe la historia clínica {paciente.nro_historia_clinica}")

    def _before_update(self, paciente: Paciente):
        """
        Hook ejecutado antes de actualizar un paciente.

        Template Method: Validaciones de actualización
        """
        # Validar unicidad de documento (excluyendo el paciente actual)
        if self.existe_documento(paciente.tipo_documento, paciente.nro_documento, paciente.id):
            raise ValueError(f"Ya existe otro paciente con documento {paciente.tipo_documento} {paciente.nro_documento}")

    # ==========================================
    # MÉTODOS AUXILIARES
    # ==========================================

    def _generar_nro_historia_clinica(self) -> str:
        """
        Genera un número de historia clínica único.

        Formato: HC-YYYYMMDD-NNNN
        Donde NNNN es un contador secuencial del día
        """
        from models.database import db

        hoy = datetime.now()
        prefijo = f"HC-{hoy.strftime('%Y%m%d')}"

        # Buscar el último número del día
        ultimo = db.session.query(Paciente).filter(
            Paciente.nro_historia_clinica.like(f"{prefijo}%")
        ).order_by(Paciente.nro_historia_clinica.desc()).first()

        if ultimo:
            # Extraer el número y sumar 1
            ultimo_numero = int(ultimo.nro_historia_clinica.split('-')[-1])
            nuevo_numero = ultimo_numero + 1
        else:
            nuevo_numero = 1

        return f"{prefijo}-{nuevo_numero:04d}"

    # ==========================================
    # ESTADÍSTICAS Y REPORTES
    # ==========================================

    def get_estadisticas_por_genero(self) -> dict:
        """
        Obtiene estadísticas de pacientes por género.

        Returns:
            Diccionario con conteo por género
        """
        from models.database import db
        from sqlalchemy import func

        resultados = db.session.query(
            Paciente.genero,
            func.count(Paciente.id).label('cantidad')
        ).filter(
            Paciente.activo == True
        ).group_by(
            Paciente.genero
        ).all()

        return {r.genero: r.cantidad for r in resultados}

    def get_total_pacientes_activos(self) -> int:
        """Retorna el total de pacientes activos."""
        return self.count({'activo': True})

    def find_pacientes_by_medico(self, medico_id: int, search: str = None) -> List[Paciente]:
        """
        Obtiene pacientes únicos atendidos por un médico.

        Args:
            medico_id: ID del médico
            search: Término de búsqueda (nombre, apellido, documento, historia clínica)

        Returns:
            Lista de pacientes únicos atendidos por el médico
        """
        from models.database import db
        from models import Turno

        # Query para obtener pacientes únicos que tienen turnos con el médico
        query = db.session.query(Paciente).join(
            Turno, Turno.paciente_id == Paciente.id
        ).filter(
            Turno.medico_id == medico_id,
            Paciente.activo == True
        ).distinct()

        # Aplicar búsqueda si se proporciona
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                (Paciente.nombre.ilike(search_pattern)) |
                (Paciente.apellido.ilike(search_pattern)) |
                (Paciente.nro_documento.ilike(search_pattern)) |
                (Paciente.nro_historia_clinica.ilike(search_pattern))
            )

        return query.order_by(Paciente.apellido, Paciente.nombre).all()
