"""
Tests de Services - Service Layer Pattern + Observer Pattern
============================================================

Estos tests demuestran:
1. Service Layer Pattern para lógica de negocio
2. Dependency Injection facilita testing
3. Observer Pattern para notificaciones
4. Mock Objects para aislar tests
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import date, time
from services.turno_service import TurnoService
from models import Turno


class TestTurnoService:
    """
    Tests del TurnoService.

    DEMUESTRA: Service Layer + Observer + Dependency Injection
    """

    def test_crear_turno_valida_disponibilidad(self, app, mocker):
        """
        Test: Crear turno valida disponibilidad del médico.

        PATRONES DEMOSTRADOS:
        - Service Layer: Lógica de negocio centralizada
        - Dependency Injection: Repository inyectado (mock)
        - Specification Pattern: Validación encapsulada
        """
        with app.app_context():
            # MOCK del repository (Dependency Injection)
            mock_turno_repo = mocker.Mock()
            mock_paciente_repo = mocker.Mock()

            # Configurar comportamiento del mock
            mock_paciente_repo.find_by_id.return_value = Mock(
                id=1,
                nombre='Juan',
                activo=True
            )

            # Simular que NO hay disponibilidad
            mock_turno_repo.verificar_disponibilidad_medico.return_value = False

            # Crear service con mocks inyectados
            service = TurnoService(
                turno_repository=mock_turno_repo,
                paciente_repository=mock_paciente_repo
            )

            # Intentar crear turno
            with pytest.raises(ValueError, match='horario no está disponible'):
                service.crear_turno(
                    paciente_id=1,
                    medico_id=1,
                    ubicacion_id=1,
                    fecha=date(2025, 12, 15),
                    hora=time(10, 0),
                    duracion_min=30
                )

            # Verificar que se validó disponibilidad
            mock_turno_repo.verificar_disponibilidad_medico.assert_called_once()


    def test_crear_turno_notifica_observers(self, app, mocker):
        """
        Test: Crear turno notifica a observers.

        PATRÓN DEMOSTRADO: Observer Pattern
        - Service notifica evento sin conocer observers
        - Observers se suscriben y reaccionan
        """
        with app.app_context():
            # Mocks
            mock_turno_repo = mocker.Mock()
            mock_paciente_repo = mocker.Mock()
            mock_observer = mocker.Mock()

            # Configurar mocks
            mock_paciente_repo.find_by_id.return_value = Mock(
                id=1,
                nombre='Juan',
                activo=True
            )
            mock_turno_repo.verificar_disponibilidad_medico.return_value = True
            mock_turno_repo.create.return_value = Mock(
                id=1,
                codigo_turno='T-TEST-001'
            )

            # Crear service
            service = TurnoService(
                turno_repository=mock_turno_repo,
                paciente_repository=mock_paciente_repo
            )

            # SUSCRIBIR OBSERVER (Observer Pattern)
            service.attach_observer(mock_observer)

            # Crear turno
            service.crear_turno(
                paciente_id=1,
                medico_id=1,
                ubicacion_id=1,
                fecha=date(2025, 12, 15),
                hora=time(10, 0),
                duracion_min=30
            )

            # Verificar que se notificó al observer
            mock_observer.update.assert_called_once()
            args = mock_observer.update.call_args[0]
            assert args[0] == 'turno_creado'  # Tipo de evento


    def test_cancelar_turno_cambia_estado_y_notifica(self, app, mocker):
        """
        Test: Cancelar turno cambia estado y notifica.

        PATRONES DEMOSTRADOS:
        - Service Layer: Orquesta operación
        - Observer Pattern: Notifica cancelación
        - State Pattern (implícito): Cambio de estado
        """
        with app.app_context():
            # Mocks
            mock_turno_repo = mocker.Mock()
            mock_observer = mocker.Mock()

            # Mock del turno existente
            mock_turno = Mock(
                id=1,
                estado='pendiente',
                paciente_id=1,
                medico_id=1
            )
            mock_turno_repo.find_by_id.return_value = mock_turno
            mock_turno_repo.update.return_value = mock_turno

            # Service con observer
            service = TurnoService(turno_repository=mock_turno_repo)
            service.attach_observer(mock_observer)

            # Cancelar turno
            service.cancelar_turno(1)

            # Verificar cambio de estado
            assert mock_turno.estado == 'cancelado'

            # Verificar notificación
            mock_observer.update.assert_called_once()
            args = mock_observer.update.call_args[0]
            assert args[0] == 'turno_cancelado'


    def test_cancelar_turno_completado_lanza_error(self, app, mocker):
        """
        Test: No se puede cancelar turno completado.

        PATRÓN DEMOSTRADO: Specification Pattern
        - Regla de negocio: solo ciertos estados permiten cancelación
        """
        with app.app_context():
            mock_turno_repo = mocker.Mock()

            # Turno completado
            mock_turno = Mock(
                id=1,
                estado='completado'
            )
            mock_turno_repo.find_by_id.return_value = mock_turno

            service = TurnoService(turno_repository=mock_turno_repo)

            # Intentar cancelar
            with pytest.raises(ValueError, match='No se puede cancelar'):
                service.cancelar_turno(1)


    def test_obtener_horarios_disponibles_delega_a_repository(self, app, mocker):
        """
        Test: Service delega consulta de horarios a repository.

        PATRÓN DEMOSTRADO: Facade Pattern
        - Service simplifica llamada al repository
        """
        with app.app_context():
            mock_turno_repo = mocker.Mock()

            # Mock de horarios disponibles
            mock_turno_repo.get_horarios_disponibles.return_value = [
                time(8, 0),
                time(8, 30),
                time(9, 0)
            ]

            service = TurnoService(turno_repository=mock_turno_repo)

            # Obtener horarios
            horarios = service.obtener_horarios_disponibles(
                medico_id=1,
                fecha=date(2025, 12, 15),
                duracion_min=30
            )

            assert len(horarios) == 3
            assert time(8, 0) in horarios

            # Verificar delegación
            mock_turno_repo.get_horarios_disponibles.assert_called_once_with(
                1, date(2025, 12, 15), 30
            )


class TestObserverPattern:
    """
    Tests específicos del Observer Pattern.

    DEMUESTRA: Observer Pattern en detalle
    """

    def test_attach_observer_agrega_observer(self):
        """
        Test: attach_observer agrega observer a la lista.
        """
        service = TurnoService()
        mock_observer = Mock()

        service.attach_observer(mock_observer)

        assert mock_observer in service._observers


    def test_detach_observer_remueve_observer(self):
        """
        Test: detach_observer remueve observer.
        """
        service = TurnoService()
        mock_observer = Mock()

        service.attach_observer(mock_observer)
        service.detach_observer(mock_observer)

        assert mock_observer not in service._observers


    def test_multiples_observers_reciben_notificacion(self, app, mocker):
        """
        Test: Múltiples observers reciben notificación.

        PATRÓN DEMOSTRADO: Observer Pattern
        - Desacoplamiento: Service no conoce tipos de observers
        - Extensibilidad: Fácil agregar nuevos observers
        """
        with app.app_context():
            # Mocks
            mock_turno_repo = mocker.Mock()
            mock_paciente_repo = mocker.Mock()

            mock_paciente_repo.find_by_id.return_value = Mock(
                id=1, activo=True
            )
            mock_turno_repo.verificar_disponibilidad_medico.return_value = True
            mock_turno_repo.create.return_value = Mock(id=1)

            # Múltiples observers
            mock_notification = mocker.Mock()
            mock_logging = mocker.Mock()
            mock_audit = mocker.Mock()

            # Service
            service = TurnoService(
                turno_repository=mock_turno_repo,
                paciente_repository=mock_paciente_repo
            )

            # Suscribir múltiples observers
            service.attach_observer(mock_notification)
            service.attach_observer(mock_logging)
            service.attach_observer(mock_audit)

            # Crear turno
            service.crear_turno(
                paciente_id=1,
                medico_id=1,
                ubicacion_id=1,
                fecha=date(2025, 12, 15),
                hora=time(10, 0)
            )

            # Verificar que TODOS recibieron notificación
            mock_notification.update.assert_called_once()
            mock_logging.update.assert_called_once()
            mock_audit.update.assert_called_once()


# ==========================================
# RESUMEN DE PATRONES DEMOSTRADOS
# ==========================================

"""
PATRONES DEMOSTRADOS EN ESTOS TESTS:

1. SERVICE LAYER PATTERN:
   - Lógica de negocio centralizada
   - Orquesta múltiples repositories
   - Maneja transacciones complejas

2. DEPENDENCY INJECTION:
   - Repositories inyectados en constructor
   - Facilita testing (inyectar mocks)
   - Reduce acoplamiento

3. OBSERVER PATTERN:
   - Service notifica eventos
   - Observers se suscriben
   - Desacoplamiento total

4. MOCK OBJECT PATTERN (testing):
   - Aislar componente bajo test
   - Verificar interacciones
   - Control total del comportamiento

5. FACADE PATTERN:
   - Service simplifica operaciones complejas
   - API simple para controllers

BENEFICIOS PARA TESTING:
✅ Tests rápidos (no tocan BD real)
✅ Tests aislados (mocks)
✅ Fácil verificar comportamiento
✅ Tests legibles
✅ Cobertura completa de lógica de negocio

SIN PATRONES:
❌ Tests lentos (BD real)
❌ Tests acoplados
❌ Difícil aislar componentes
❌ Testing frágil
"""
