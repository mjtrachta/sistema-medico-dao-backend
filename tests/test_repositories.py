"""
Tests de Repositories - Repository Pattern
==========================================

Estos tests demuestran:
1. Repository Pattern abstrae acceso a datos
2. Template Method Pattern en operaciones CRUD
3. Specification Pattern en validaciones
"""

import pytest
from datetime import date, time
from repositories.paciente_repository import PacienteRepository
from repositories.turno_repository import TurnoRepository
from models import Paciente, Turno


class TestPacienteRepository:
    """
    Tests del PacienteRepository.

    DEMUESTRA: Repository Pattern + Template Method Pattern
    """

    def test_create_paciente_genera_historia_clinica_automatica(self, app):
        """
        Test: Crear paciente genera número de historia clínica automático.

        PATRÓN DEMOSTRADO: Template Method Pattern
        - El hook _before_create() genera HC automáticamente
        """
        with app.app_context():
            repo = PacienteRepository()

            paciente = Paciente(
                nombre='Test',
                apellido='User',
                tipo_documento='DNI',
                nro_documento='99999999',
                fecha_nacimiento=date(1990, 1, 1),
                genero='masculino'
            )

            # NO seteamos nro_historia_clinica
            assert paciente.nro_historia_clinica is None

            # Crear (dispara _before_create hook)
            paciente_creado = repo.create(paciente)

            # Verificar que se generó HC automáticamente
            assert paciente_creado.nro_historia_clinica is not None
            assert paciente_creado.nro_historia_clinica.startswith('HC-')


    def test_create_paciente_valida_documento_unico(self, app, paciente):
        """
        Test: No permite duplicar documento.

        PATRÓN DEMOSTRADO: Specification Pattern (validación)
        - La regla de negocio "documento único" está encapsulada
        """
        with app.app_context():
            repo = PacienteRepository()

            # Intentar crear paciente con mismo documento
            paciente_duplicado = Paciente(
                nombre='Otro',
                apellido='Paciente',
                tipo_documento='DNI',
                nro_documento='12345678',  # Mismo que fixture
                fecha_nacimiento=date(1995, 1, 1)
            )

            # Debe lanzar ValueError
            with pytest.raises(ValueError, match='Ya existe un paciente con documento'):
                repo.create(paciente_duplicado)


    def test_find_by_documento(self, app, paciente):
        """
        Test: Buscar paciente por documento.

        PATRÓN DEMOSTRADO: Query Object Pattern
        - Método nombrado que encapsula query específica
        """
        with app.app_context():
            repo = PacienteRepository()

            encontrado = repo.find_by_documento('DNI', '12345678')

            assert encontrado is not None
            assert encontrado.id == paciente.id
            assert encontrado.nombre == 'Juan'


    def test_search_by_nombre(self, app, paciente):
        """
        Test: Búsqueda parcial por nombre.

        PATRÓN DEMOSTRADO: Query Object Pattern
        """
        with app.app_context():
            repo = PacienteRepository()

            # Búsqueda parcial (like)
            resultados = repo.search_by_nombre('Jua', 'Gon')

            assert len(resultados) == 1
            assert resultados[0].nombre == 'Juan'


    def test_get_total_pacientes_activos(self, app, paciente):
        """
        Test: Contar pacientes activos.

        PATRÓN DEMOSTRADO: Repository Pattern
        - Encapsula lógica de queries de estadísticas
        """
        with app.app_context():
            repo = PacienteRepository()

            total = repo.get_total_pacientes_activos()

            assert total == 1


class TestTurnoRepository:
    """
    Tests del TurnoRepository.

    DEMUESTRA: Repository Pattern + Specification Pattern
    """

    def test_verificar_disponibilidad_sin_horario(self, app, medico):
        """
        Test: Médico sin horario no está disponible.

        PATRÓN DEMOSTRADO: Specification Pattern
        - La especificación "tiene_horario_atencion" valida regla de negocio
        """
        with app.app_context():
            repo = TurnoRepository()

            disponible = repo.verificar_disponibilidad_medico(
                medico_id=medico.id,
                fecha=date(2025, 12, 15),  # Lunes
                hora=time(10, 0),
                duracion_min=30
            )

            # No debe estar disponible (no tiene horario)
            assert disponible is False


    def test_verificar_disponibilidad_con_horario(self, app, medico, ubicacion, horario_medico):
        """
        Test: Médico con horario está disponible.

        PATRÓN DEMOSTRADO: Specification Pattern
        """
        with app.app_context():
            repo = TurnoRepository()

            # horario_medico fixture: lunes 8:00-12:00
            disponible = repo.verificar_disponibilidad_medico(
                medico_id=medico.id,
                fecha=date(2025, 12, 15),  # Lunes
                hora=time(9, 0),  # Dentro del horario
                duracion_min=30
            )

            assert disponible is True


    def test_verificar_disponibilidad_detecta_superposicion(self, app, turno, horario_medico):
        """
        Test: Detecta superposición de turnos.

        PATRÓN DEMOSTRADO: Specification Pattern
        - La especificación "existe_superposicion" valida regla compleja
        """
        with app.app_context():
            repo = TurnoRepository()

            # turno fixture: 10:00, 30 min (hasta 10:30)
            # Intentar crear turno que se superpone: 10:15, 30 min

            disponible = repo.verificar_disponibilidad_medico(
                medico_id=turno.medico_id,
                fecha=turno.fecha,
                hora=time(10, 15),  # Se superpone con turno existente
                duracion_min=30
            )

            # No debe estar disponible (hay superposición)
            assert disponible is False


    def test_get_horarios_disponibles(self, app, medico, horario_medico):
        """
        Test: Obtener slots de horarios disponibles.

        PATRÓN DEMOSTRADO: Factory Method Pattern
        - Genera objetos time según disponibilidad
        """
        with app.app_context():
            repo = TurnoRepository()

            # horario_medico: lunes 8:00-12:00
            horarios = repo.get_horarios_disponibles(
                medico_id=medico.id,
                fecha=date(2025, 12, 15),  # Lunes
                duracion_min=30
            )

            # Debe generar slots cada 30 min: 8:00, 8:30, 9:00, 9:30, 10:00, 10:30, 11:00, 11:30
            assert len(horarios) == 8
            assert time(8, 0) in horarios
            assert time(9, 30) in horarios
            assert time(11, 30) in horarios


    def test_find_by_paciente(self, app, turno):
        """
        Test: Buscar turnos de un paciente.

        PATRÓN DEMOSTRADO: Query Object Pattern
        """
        with app.app_context():
            repo = TurnoRepository()

            turnos = repo.find_by_paciente(turno.paciente_id)

            assert len(turnos) == 1
            assert turnos[0].id == turno.id


class TestBaseRepository:
    """
    Tests del BaseRepository (Template Method Pattern).

    DEMUESTRA: Template Method Pattern
    """

    def test_find_all_con_filtros(self, app, paciente):
        """
        Test: find_all aplica filtros.

        PATRÓN DEMOSTRADO: Template Method
        - Método base reutilizable
        """
        with app.app_context():
            from repositories.base_repository import BaseRepository
            from models import Paciente

            repo = BaseRepository(Paciente)

            # Filtrar por activos
            activos = repo.find_all(filters={'activo': True})

            assert len(activos) == 1
            assert activos[0].id == paciente.id


    def test_count(self, app, paciente):
        """
        Test: count retorna cantidad.

        PATRÓN DEMOSTRADO: Template Method
        """
        with app.app_context():
            from repositories.base_repository import BaseRepository
            from models import Paciente

            repo = BaseRepository(Paciente)

            total = repo.count({'activo': True})

            assert total == 1


# ==========================================
# RESUMEN DE PATRONES DEMOSTRADOS
# ==========================================

"""
PATRONES DEMOSTRADOS EN ESTOS TESTS:

1. REPOSITORY PATTERN:
   - Abstrae acceso a datos
   - Facilita testing (tests usan repo, no queries directas)
   - Queries complejas encapsuladas

2. TEMPLATE METHOD PATTERN:
   - BaseRepository define flujo CRUD
   - Hooks (_before_create, etc.) personalizables
   - Reutilización de código

3. SPECIFICATION PATTERN:
   - Reglas de negocio encapsuladas (documento_unico, disponibilidad)
   - Reutilizables y testeables independientemente

4. QUERY OBJECT PATTERN:
   - Métodos nombrados (find_by_documento, search_by_nombre)
   - Queries legibles y mantenibles

5. FACTORY PATTERN (en fixtures):
   - pytest fixtures crean objetos de prueba
   - Reutilizables en todos los tests

BENEFICIOS:
- Tests claros y enfocados
- No hay SQL en los tests
- Fácil mockear repositories
- Tests aislados (no dependen de BD real en producción)
"""
