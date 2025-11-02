"""
Tests de Recetas Electrónicas
==============================

Tests que demuestran:
1. Service Layer Pattern
2. Repository Pattern
3. Template Method Pattern (generación de códigos)
"""

import pytest
from datetime import date, timedelta
from models import Receta, ItemReceta
from repositories.receta_repository import RecetaRepository
from services.receta_service import RecetaService


class TestRecetaRepository:
    """Tests del Repository Pattern para Recetas."""

    def test_generar_codigo_receta(self, app, paciente, medico):
        """
        Test: Genera código único para receta.

        PATRÓN: Template Method Pattern
        - Formato: R-YYYYMMDD-NNNN
        """
        with app.app_context():
            repo = RecetaRepository()

            codigo1 = repo.generar_codigo_receta()

            # Verificar formato
            assert codigo1.startswith('R-')
            assert len(codigo1.split('-')) == 3

            # Crear receta para incrementar contador
            receta1 = Receta(
                codigo_receta=codigo1,
                paciente_id=paciente.id,
                medico_id=medico.id,
                fecha=date.today(),
                estado='activa'
            )
            repo.create(receta1)

            # Generar segundo código
            codigo2 = repo.generar_codigo_receta()

            # Códigos diferentes
            assert codigo1 != codigo2

    def test_find_by_paciente(self, app, paciente, medico):
        """Test: Encuentra recetas de un paciente."""
        with app.app_context():
            repo = RecetaRepository()

            # Crear receta
            receta = Receta(
                codigo_receta='R-TEST-001',
                paciente_id=paciente.id,
                medico_id=medico.id,
                fecha=date.today(),
                estado='activa'
            )
            repo.create(receta)

            # Buscar
            recetas = repo.find_by_paciente(paciente.id)

            assert len(recetas) == 1
            assert recetas[0].paciente_id == paciente.id

    def test_find_by_medico(self, app, paciente, medico):
        """Test: Encuentra recetas de un médico."""
        with app.app_context():
            repo = RecetaRepository()

            # Crear receta
            receta = Receta(
                codigo_receta='R-TEST-002',
                paciente_id=paciente.id,
                medico_id=medico.id,
                fecha=date.today(),
                estado='activa'
            )
            repo.create(receta)

            # Buscar
            recetas = repo.find_by_medico(medico.id)

            assert len(recetas) == 1
            assert recetas[0].medico_id == medico.id

    def test_find_activas(self, app, paciente, medico):
        """
        Test: Encuentra solo recetas activas y no vencidas.

        PATRÓN: Specification Pattern
        """
        with app.app_context():
            repo = RecetaRepository()

            # Receta activa y válida
            receta_valida = Receta(
                codigo_receta='R-TEST-003',
                paciente_id=paciente.id,
                medico_id=medico.id,
                fecha=date.today(),
                estado='activa',
                valida_hasta=date.today() + timedelta(days=30)
            )
            repo.create(receta_valida)

            # Receta vencida
            receta_vencida = Receta(
                codigo_receta='R-TEST-004',
                paciente_id=paciente.id,
                medico_id=medico.id,
                fecha=date.today(),
                estado='activa',
                valida_hasta=date.today() - timedelta(days=1)
            )
            repo.create(receta_vencida)

            # Receta cancelada
            receta_cancelada = Receta(
                codigo_receta='R-TEST-005',
                paciente_id=paciente.id,
                medico_id=medico.id,
                fecha=date.today(),
                estado='cancelada'
            )
            repo.create(receta_cancelada)

            # Buscar activas
            activas = repo.find_activas(paciente.id)

            # Solo debe retornar la válida
            assert len(activas) == 1
            assert activas[0].codigo_receta == 'R-TEST-003'


class TestRecetaService:
    """Tests del Service Layer Pattern para Recetas."""

    def test_crear_receta_exitoso(self, app, paciente, medico, mocker):
        """
        Test: Crea receta con múltiples ítems.

        PATRÓN: Service Layer
        - Orquesta creación de receta e ítems
        - Transaction handling
        """
        with app.app_context():
            mock_repo = mocker.Mock()
            mock_repo.generar_codigo_receta.return_value = 'R-20251102-0001'

            receta_creada = Receta(
                id=1,
                codigo_receta='R-20251102-0001',
                paciente_id=paciente.id,
                medico_id=medico.id,
                fecha=date.today(),
                estado='activa',
                valida_hasta=date.today() + timedelta(days=30)
            )
            mock_repo.create.return_value = receta_creada

            service = RecetaService(receta_repository=mock_repo)

            # Crear receta
            items = [
                {
                    'nombre_medicamento': 'Ibuprofeno 600mg',
                    'dosis': '1 comprimido',
                    'frecuencia': 'Cada 8 horas',
                    'cantidad': 20,
                    'duracion_dias': 7,
                    'instrucciones': 'Tomar con alimentos'
                }
            ]

            receta = service.crear_receta(
                paciente_id=paciente.id,
                medico_id=medico.id,
                items=items,
                dias_validez=30
            )

            assert receta.codigo_receta == 'R-20251102-0001'
            mock_repo.create.assert_called_once()

    def test_crear_receta_sin_items_falla(self, app, paciente, medico, mocker):
        """Test: Falla si no hay ítems."""
        with app.app_context():
            mock_repo = mocker.Mock()
            service = RecetaService(receta_repository=mock_repo)

            # Debe lanzar error
            with pytest.raises(ValueError, match='al menos un medicamento'):
                service.crear_receta(
                    paciente_id=paciente.id,
                    medico_id=medico.id,
                    items=[],  # Sin ítems
                    dias_validez=30
                )

    def test_cancelar_receta(self, app, mocker):
        """Test: Cancela una receta."""
        with app.app_context():
            mock_repo = mocker.Mock()

            # Receta existente
            receta_existente = Receta(
                id=1,
                codigo_receta='R-TEST-001',
                estado='activa'
            )
            mock_repo.find_by_id.return_value = receta_existente
            mock_repo.update.return_value = receta_existente

            service = RecetaService(receta_repository=mock_repo)

            # Cancelar
            receta = service.cancelar_receta(1)

            assert receta.estado == 'cancelada'
            mock_repo.update.assert_called_once()

    def test_cancelar_receta_ya_cancelada_falla(self, app, mocker):
        """Test: No permite cancelar receta ya cancelada."""
        with app.app_context():
            mock_repo = mocker.Mock()

            # Receta ya cancelada
            receta_cancelada = Receta(
                id=1,
                codigo_receta='R-TEST-001',
                estado='cancelada'
            )
            mock_repo.find_by_id.return_value = receta_cancelada

            service = RecetaService(receta_repository=mock_repo)

            # Debe lanzar error
            with pytest.raises(ValueError, match='ya está cancelada'):
                service.cancelar_receta(1)

    def test_obtener_recetas_paciente_todas(self, app, paciente, mocker):
        """Test: Obtiene todas las recetas del paciente."""
        with app.app_context():
            mock_repo = mocker.Mock()
            mock_repo.find_by_paciente.return_value = [
                Receta(id=1, paciente_id=paciente.id),
                Receta(id=2, paciente_id=paciente.id)
            ]

            service = RecetaService(receta_repository=mock_repo)

            recetas = service.obtener_recetas_paciente(paciente.id, solo_activas=False)

            assert len(recetas) == 2
            mock_repo.find_by_paciente.assert_called_once()

    def test_obtener_recetas_paciente_solo_activas(self, app, paciente, mocker):
        """Test: Obtiene solo recetas activas."""
        with app.app_context():
            mock_repo = mocker.Mock()
            mock_repo.find_activas.return_value = [
                Receta(id=1, paciente_id=paciente.id, estado='activa')
            ]

            service = RecetaService(receta_repository=mock_repo)

            recetas = service.obtener_recetas_paciente(paciente.id, solo_activas=True)

            assert len(recetas) == 1
            mock_repo.find_activas.assert_called_once()
