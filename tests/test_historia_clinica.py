"""
Tests de Historia Clínica - Service y Repository
================================================

Tests que demuestran:
1. Service Layer Pattern
2. Repository Pattern
3. Specification Pattern (validaciones)
"""

import pytest
from datetime import date
from models import HistoriaClinica, Turno
from repositories.historia_clinica_repository import HistoriaClinicaRepository
from services.historia_clinica_service import HistoriaClinicaService


class TestHistoriaClinicaRepository:
    """Tests del Repository Pattern para Historia Clínica."""

    def test_find_by_paciente(self, app, paciente, medico):
        """Test: Encuentra historias clínicas de un paciente."""
        with app.app_context():
            repo = HistoriaClinicaRepository()

            # Crear historia clínica
            hc = HistoriaClinica(
                paciente_id=paciente.id,
                medico_id=medico.id,
                fecha_consulta=date.today(),
                motivo_consulta='Test',
                diagnostico='Diagnóstico de prueba'
            )
            repo.create(hc)

            # Buscar por paciente
            historias = repo.find_by_paciente(paciente.id)

            assert len(historias) == 1
            assert historias[0].paciente_id == paciente.id

    def test_find_by_medico(self, app, paciente, medico):
        """Test: Encuentra historias clínicas de un médico."""
        with app.app_context():
            repo = HistoriaClinicaRepository()

            # Crear historia clínica
            hc = HistoriaClinica(
                paciente_id=paciente.id,
                medico_id=medico.id,
                fecha_consulta=date.today(),
                motivo_consulta='Test',
                diagnostico='Diagnóstico de prueba'
            )
            repo.create(hc)

            # Buscar por médico
            historias = repo.find_by_medico(medico.id)

            assert len(historias) == 1
            assert historias[0].medico_id == medico.id

    def test_find_by_medico_con_filtro_fechas(self, app, paciente, medico):
        """Test: Filtra historias por rango de fechas."""
        with app.app_context():
            repo = HistoriaClinicaRepository()

            # Crear historia clínica
            hc = HistoriaClinica(
                paciente_id=paciente.id,
                medico_id=medico.id,
                fecha_consulta=date.today(),
                motivo_consulta='Test',
                diagnostico='Diagnóstico de prueba'
            )
            repo.create(hc)

            # Buscar con filtro de fechas
            historias = repo.find_by_medico(
                medico.id,
                fecha_inicio=date.today(),
                fecha_fin=date.today()
            )

            assert len(historias) == 1

    def test_exists_for_turno(self, app, turno):
        """Test: Verifica si existe HC para un turno."""
        with app.app_context():
            repo = HistoriaClinicaRepository()

            # Al principio no existe
            assert repo.exists_for_turno(turno.id) is False

            # Crear HC
            hc = HistoriaClinica(
                turno_id=turno.id,
                paciente_id=turno.paciente_id,
                medico_id=turno.medico_id,
                fecha_consulta=turno.fecha,
                motivo_consulta='Test',
                diagnostico='Diagnóstico de prueba'
            )
            repo.create(hc)

            # Ahora sí existe
            assert repo.exists_for_turno(turno.id) is True


class TestHistoriaClinicaService:
    """Tests del Service Layer Pattern para Historia Clínica."""

    def test_crear_desde_turno_exitoso(self, app, turno, mocker):
        """
        Test: Crea historia clínica desde turno completado.

        PATRÓN: Service Layer
        - Valida reglas de negocio
        - Orquesta repository
        """
        with app.app_context():
            # Mock repositories
            mock_hc_repo = mocker.Mock()
            mock_turno_repo = mocker.Mock()

            # Configurar turno como completado
            turno.estado = 'completado'
            mock_turno_repo.find_by_id.return_value = turno
            mock_hc_repo.exists_for_turno.return_value = False
            mock_hc_repo.create.return_value = HistoriaClinica(
                id=1,
                turno_id=turno.id,
                paciente_id=turno.paciente_id,
                medico_id=turno.medico_id,
                fecha_consulta=turno.fecha,
                diagnostico='Diagnóstico de prueba'
            )

            # Service con DI
            service = HistoriaClinicaService(
                historia_repository=mock_hc_repo,
                turno_repository=mock_turno_repo
            )

            # Crear HC
            hc = service.crear_desde_turno(
                turno_id=turno.id,
                diagnostico='Diagnóstico de prueba',
                tratamiento='Tratamiento de prueba'
            )

            assert hc.diagnostico == 'Diagnóstico de prueba'
            mock_hc_repo.create.assert_called_once()

    def test_crear_desde_turno_no_existente_falla(self, app, mocker):
        """Test: Falla si turno no existe."""
        with app.app_context():
            mock_hc_repo = mocker.Mock()
            mock_turno_repo = mocker.Mock()

            # Turno no existe
            mock_turno_repo.find_by_id.return_value = None

            service = HistoriaClinicaService(
                historia_repository=mock_hc_repo,
                turno_repository=mock_turno_repo
            )

            # Debe lanzar error
            with pytest.raises(ValueError, match='no encontrado'):
                service.crear_desde_turno(
                    turno_id=999,
                    diagnostico='Test'
                )

    def test_crear_desde_turno_no_completado_falla(self, app, turno, mocker):
        """Test: Falla si turno no está completado."""
        with app.app_context():
            mock_hc_repo = mocker.Mock()
            mock_turno_repo = mocker.Mock()

            # Turno pendiente (no completado)
            turno.estado = 'pendiente'
            mock_turno_repo.find_by_id.return_value = turno

            service = HistoriaClinicaService(
                historia_repository=mock_hc_repo,
                turno_repository=mock_turno_repo
            )

            # Debe lanzar error
            with pytest.raises(ValueError, match='completado'):
                service.crear_desde_turno(
                    turno_id=turno.id,
                    diagnostico='Test'
                )

    def test_crear_desde_turno_duplicado_falla(self, app, turno, mocker):
        """Test: No permite crear HC duplicada."""
        with app.app_context():
            mock_hc_repo = mocker.Mock()
            mock_turno_repo = mocker.Mock()

            # Turno completado
            turno.estado = 'completado'
            mock_turno_repo.find_by_id.return_value = turno

            # Ya existe HC
            mock_hc_repo.exists_for_turno.return_value = True

            service = HistoriaClinicaService(
                historia_repository=mock_hc_repo,
                turno_repository=mock_turno_repo
            )

            # Debe lanzar error
            with pytest.raises(ValueError, match='Ya existe'):
                service.crear_desde_turno(
                    turno_id=turno.id,
                    diagnostico='Test'
                )

    def test_actualizar_historia_clinica(self, app, mocker):
        """Test: Actualiza HC existente."""
        with app.app_context():
            mock_hc_repo = mocker.Mock()

            # HC existente
            hc_existente = HistoriaClinica(
                id=1,
                diagnostico='Original',
                tratamiento='Original'
            )
            mock_hc_repo.find_by_id.return_value = hc_existente
            mock_hc_repo.update.return_value = hc_existente

            service = HistoriaClinicaService(historia_repository=mock_hc_repo)

            # Actualizar
            hc = service.actualizar(
                historia_id=1,
                diagnostico='Actualizado',
                tratamiento='Actualizado'
            )

            assert hc.diagnostico == 'Actualizado'
            mock_hc_repo.update.assert_called_once()

    def test_obtener_historial_paciente(self, app, paciente, mocker):
        """Test: Obtiene historial completo."""
        with app.app_context():
            mock_hc_repo = mocker.Mock()
            mock_hc_repo.find_by_paciente.return_value = [
                HistoriaClinica(id=1, paciente_id=paciente.id),
                HistoriaClinica(id=2, paciente_id=paciente.id)
            ]

            service = HistoriaClinicaService(historia_repository=mock_hc_repo)

            # Obtener historial
            historial = service.obtener_historial_paciente(paciente.id, limit=10)

            assert len(historial) == 2
            mock_hc_repo.find_by_paciente.assert_called_once_with(paciente.id, 10)
