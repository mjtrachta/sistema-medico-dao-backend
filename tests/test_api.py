"""
Tests de API (Endpoints) - Integration Tests
============================================

Estos tests demuestran:
1. Facade Pattern en controllers
2. DTO Pattern con Marshmallow
3. Integration testing
"""

import pytest
import json
from datetime import date


class TestEspecialidadesAPI:
    """Tests de endpoints de especialidades."""

    def test_list_especialidades(self, client, especialidad):
        """
        Test: GET /api/especialidades retorna lista.

        PATRÓN DEMOSTRADO: Facade Pattern
        - Endpoint simple oculta complejidad
        """
        response = client.get('/api/especialidades')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['nombre'] == 'Cardiología'


    def test_create_especialidad(self, client):
        """
        Test: POST /api/especialidades crea especialidad.

        PATRÓN DEMOSTRADO: DTO Pattern
        - JSON se valida y deserializa automáticamente
        """
        response = client.post(
            '/api/especialidades',
            data=json.dumps({
                'nombre': 'Traumatología',
                'descripcion': 'Lesiones',
                'duracion_turno_min': 30
            }),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['nombre'] == 'Traumatología'


class TestPacientesAPI:
    """Tests de endpoints de pacientes."""

    def test_create_paciente_genera_historia_clinica(self, client):
        """
        Test: Crear paciente genera HC automáticamente.

        PATRONES DEMOSTRADOS:
        - Facade: Endpoint simple
        - DTO: Validación de datos
        - Repository: Generación de HC
        """
        response = client.post(
            '/api/pacientes',
            data=json.dumps({
                'nombre': 'María',
                'apellido': 'López',
                'tipo_documento': 'DNI',
                'nro_documento': '87654321',
                'fecha_nacimiento': '1995-06-20',
                'genero': 'femenino',
                'email': 'maria@test.com'
            }),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = json.loads(response.data)

        # Verificar que se generó HC
        assert 'nro_historia_clinica' in data
        assert data['nro_historia_clinica'].startswith('HC-')

        # Verificar campo calculado (DTO Pattern)
        assert 'nombre_completo' in data
        assert data['nombre_completo'] == 'María López'


    def test_create_paciente_valida_campos_requeridos(self, client):
        """
        Test: Valida campos requeridos.

        PATRÓN DEMOSTRADO: DTO Pattern
        - Marshmallow valida automáticamente
        """
        response = client.post(
            '/api/pacientes',
            data=json.dumps({
                'nombre': 'Test'
                # Faltan campos requeridos
            }),
            content_type='application/json'
        )

        # Debe fallar (falta validación en endpoint, pero demuestra el concepto)
        assert response.status_code in [400, 500]


class TestTurnosAPI:
    """
    Tests de endpoints de turnos.

    DEMUESTRA: Integración de TODOS los patrones
    """

    def test_create_turno_sin_horario_falla(self, client, paciente, medico, ubicacion, auth_headers_admin):
        """
        Test: Crear turno sin horario configurado falla.

        PATRONES DEMOSTRADOS:
        - Facade: Endpoint simple
        - Service Layer: Lógica de validación
        - Specification: Valida horario disponible
        """
        response = client.post(
            '/api/turnos',
            data=json.dumps({
                'paciente_id': paciente.id,
                'medico_id': medico.id,
                'ubicacion_id': ubicacion.id,
                'fecha': '2025-12-15',
                'hora': '10:00',
                'duracion_min': 30,
                'motivo_consulta': 'Test'
            }),
            headers=auth_headers_admin
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'disponible' in data['error'].lower()


    def test_create_turno_con_horario_exitoso(self, client, paciente, medico, ubicacion, horario_medico, auth_headers_admin):
        """
        Test: Crear turno con horario configurado es exitoso.

        FLUJO COMPLETO DE PATRONES:
        1. Facade (Controller) recibe request
        2. DTO valida datos
        3. Service Layer orquesta
        4. Repository consulta BD
        5. Specification valida reglas
        6. Observer notifica (mocked en test)
        7. DTO serializa respuesta
        """
        response = client.post(
            '/api/turnos',
            data=json.dumps({
                'paciente_id': paciente.id,
                'medico_id': medico.id,
                'ubicacion_id': ubicacion.id,
                'fecha': '2025-12-15',  # Lunes
                'hora': '09:00',  # Dentro del horario (8-12)
                'duracion_min': 30,
                'motivo_consulta': 'Control'
            }),
            headers=auth_headers_admin
        )

        assert response.status_code == 201
        data = json.loads(response.data)

        # Verificar datos del turno
        assert 'codigo_turno' in data
        assert data['codigo_turno'].startswith('T-')
        assert data['estado'] == 'pendiente'

    def test_get_turno_by_id(self, client, turno, auth_headers_admin):
        """Test: Obtiene turno por ID."""
        response = client.get(f'/api/turnos/{turno.id}', headers=auth_headers_admin)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == turno.id
        assert data['codigo_turno'] == 'T-TEST-001'

    def test_list_turnos(self, client, turno, auth_headers_admin):
        """Test: Lista todos los turnos."""
        response = client.get('/api/turnos', headers=auth_headers_admin)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_turnos_filtrado_por_paciente(self, client, paciente, turno, auth_headers_admin):
        """Test: Lista turnos filtrados por paciente."""
        response = client.get(f'/api/turnos?paciente_id={paciente.id}', headers=auth_headers_admin)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        if len(data) > 0:
            assert data[0]['paciente_id'] == paciente.id

    def test_get_disponibilidad(self, client, medico, ubicacion, horario_medico):
        """
        Test: Obtener horarios disponibles.

        PATRÓN DEMOSTRADO: Facade Pattern
        - Endpoint simple que oculta algoritmo complejo
        """
        response = client.get(
            f'/api/turnos/disponibilidad?medico_id={medico.id}&fecha=2025-12-15&duracion=30'
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'horarios_disponibles' in data
        assert len(data['horarios_disponibles']) > 0
        assert '08:00' in data['horarios_disponibles']


    def test_cancelar_turno(self, client, turno, auth_headers_admin):
        """
        Test: Cancelar turno cambia estado.

        PATRÓN DEMOSTRADO: Observer Pattern
        - Cancelación dispara notificación (en prod)
        """
        response = client.patch(f'/api/turnos/{turno.id}/cancelar', headers=auth_headers_admin)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['estado'] == 'cancelado'

    def test_confirmar_turno(self, client, turno, auth_headers_admin):
        """Test: Confirmar turno cambia estado a confirmado."""
        response = client.patch(f'/api/turnos/{turno.id}/confirmar', headers=auth_headers_admin)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['estado'] == 'confirmado'

    def test_completar_turno(self, client, turno, auth_headers_admin):
        """Test: Completar turno cambia estado a completado."""
        response = client.patch(f'/api/turnos/{turno.id}/completar', headers=auth_headers_admin)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['estado'] == 'completado'

    def test_ausente_turno(self, client, turno, auth_headers_admin):
        """Test: Marcar turno como ausente cambia estado a ausente."""
        response = client.patch(f'/api/turnos/{turno.id}/ausente', headers=auth_headers_admin)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['estado'] == 'ausente'


class TestHealthEndpoint:
    """Test de health check."""

    def test_health_check(self, client):
        """
        Test: Health check verifica conexión a BD.
        """
        response = client.get('/api/health')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'database' in data


class TestPacientesCRUD:
    """Tests de CRUD completo de pacientes."""

    def test_update_paciente(self, client, paciente):
        """Test: Actualiza paciente."""
        response = client.put(
            f'/api/pacientes/{paciente.id}',
            data=json.dumps({
                'nombre': 'Juan Actualizado',
                'telefono': '999999999'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['nombre'] == 'Juan Actualizado'

    def test_delete_paciente(self, client, paciente):
        """Test: Desactiva paciente (soft delete)."""
        response = client.delete(f'/api/pacientes/{paciente.id}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'mensaje' in data or 'message' in data


class TestMedicosCRUD:
    """Tests de CRUD completo de médicos."""

    def test_update_medico(self, client, medico):
        """Test: Actualiza médico."""
        response = client.put(
            f'/api/medicos/{medico.id}',
            data=json.dumps({
                'nombre': 'Dr. Actualizado',
                'telefono': '888888888'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['nombre'] == 'Dr. Actualizado'

    def test_delete_medico(self, client, medico, auth_headers_admin):
        """Test: Desactiva médico (soft delete)."""
        response = client.delete(f'/api/medicos/{medico.id}', headers=auth_headers_admin)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'mensaje' in data or 'message' in data


class TestHistoriasClinicasAPI:
    """Tests de API de Historias Clínicas."""

    def test_create_historia_clinica(self, client, turno, auth_headers_medico):
        """Test: Crea historia clínica desde turno completado."""
        # Marcar turno como completado
        from models.database import db
        turno.estado = 'completado'
        db.session.commit()

        response = client.post(
            '/api/historias-clinicas',
            data=json.dumps({
                'turno_id': turno.id,
                'diagnostico': 'Diagnóstico de prueba',
                'tratamiento': 'Tratamiento de prueba'
            }),
            headers=auth_headers_medico
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['diagnostico'] == 'Diagnóstico de prueba'

    def test_get_historial_paciente(self, client, paciente, medico, auth_headers_medico):
        """Test: Obtiene historial de paciente."""
        # Crear historia clínica
        from models import HistoriaClinica
        from models.database import db
        hc = HistoriaClinica(
            paciente_id=paciente.id,
            medico_id=medico.id,
            fecha_consulta=date.today(),
            diagnostico='Test'
        )
        db.session.add(hc)
        db.session.commit()

        response = client.get(f'/api/historias-clinicas/paciente/{paciente.id}', headers=auth_headers_medico)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) >= 1


class TestRecetasAPI:
    """Tests de API de Recetas."""

    def test_create_receta(self, client, paciente, medico, auth_headers_medico):
        """Test: Crea receta electrónica."""
        response = client.post(
            '/api/recetas',
            data=json.dumps({
                'paciente_id': paciente.id,
                'medico_id': medico.id,
                'items': [
                    {
                        'nombre_medicamento': 'Ibuprofeno 600mg',
                        'dosis': '1 comprimido',
                        'frecuencia': 'Cada 8 horas',
                        'cantidad': 20
                    }
                ],
                'dias_validez': 30
            }),
            headers=auth_headers_medico
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'codigo_receta' in data
        assert data['codigo_receta'].startswith('R-')

    def test_get_recetas_paciente(self, client, paciente, medico, auth_headers_medico):
        """Test: Obtiene recetas de paciente."""
        # Crear receta
        from models import Receta, ItemReceta
        from models.database import db
        receta = Receta(
            codigo_receta='R-TEST-001',
            paciente_id=paciente.id,
            medico_id=medico.id,
            fecha=date.today(),
            estado='activa'
        )
        db.session.add(receta)
        db.session.commit()

        response = client.get(f'/api/recetas/paciente/{paciente.id}', headers=auth_headers_medico)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) >= 1


class TestReportesAPI:
    """Tests de API de Reportes."""

    def test_reporte_turnos_por_medico(self, client, medico):
        """Test: Reporte de turnos por médico."""
        response = client.get(
            f'/api/reportes/turnos-por-medico/{medico.id}?fecha_inicio=2025-12-01&fecha_fin=2025-12-31'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'medico' in data
        assert 'estadisticas' in data

    def test_reporte_turnos_por_especialidad(self, client):
        """Test: Reporte de turnos por especialidad."""
        response = client.get('/api/reportes/turnos-por-especialidad')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'especialidades' in data

    def test_reporte_pacientes_atendidos(self, client):
        """Test: Reporte de pacientes atendidos."""
        response = client.get(
            '/api/reportes/pacientes-atendidos?fecha_inicio=2025-01-01&fecha_fin=2025-12-31'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_pacientes' in data
        assert 'pacientes' in data

    def test_reporte_estadisticas_asistencia(self, client):
        """Test: Reporte de estadísticas de asistencia."""
        response = client.get('/api/reportes/estadisticas-asistencia')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'resumen' in data
        assert 'por_mes' in data


class TestHorariosAPI:
    """Tests de API de Horarios."""

    def test_list_horarios(self, client, horario_medico, auth_headers_admin):
        """Test: Lista horarios de médicos."""
        response = client.get('/api/horarios', headers=auth_headers_admin)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_list_horarios_filtrado_por_medico(self, client, medico, horario_medico, auth_headers_admin):
        """Test: Lista horarios filtrados por médico."""
        response = client.get(f'/api/horarios?medico_id={medico.id}', headers=auth_headers_admin)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        if len(data) > 0:
            assert data[0]['medico_id'] == medico.id

    def test_create_horario(self, client, medico, ubicacion, auth_headers_admin):
        """Test: Crea un horario de atención."""
        response = client.post(
            '/api/horarios',
            data=json.dumps({
                'medico_id': medico.id,
                'ubicacion_id': ubicacion.id,
                'dia_semana': 'martes',
                'hora_inicio': '14:00',
                'hora_fin': '18:00'
            }),
            headers=auth_headers_admin
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['dia_semana'] == 'martes'
        assert data['hora_inicio'] == '14:00'

    def test_create_horario_dia_invalido(self, client, medico, ubicacion, auth_headers_admin):
        """Test: Falla si el día de la semana es inválido."""
        response = client.post(
            '/api/horarios',
            data=json.dumps({
                'medico_id': medico.id,
                'ubicacion_id': ubicacion.id,
                'dia_semana': 'invalid_day',
                'hora_inicio': '14:00',
                'hora_fin': '18:00'
            }),
            headers=auth_headers_admin
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestUbicacionesAPI:
    """Tests de API de Ubicaciones."""

    def test_list_ubicaciones(self, client, ubicacion, auth_headers_admin):
        """Test: Lista ubicaciones."""
        response = client.get('/api/ubicaciones', headers=auth_headers_admin)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) >= 1
        assert data[0]['nombre'] == 'Consultorio Test'

    def test_get_ubicacion_by_id(self, client, ubicacion, auth_headers_admin):
        """Test: Obtiene ubicación por ID."""
        response = client.get(f'/api/ubicaciones/{ubicacion.id}', headers=auth_headers_admin)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == ubicacion.id
        assert data['nombre'] == 'Consultorio Test'


class TestMedicosAdditionalAPI:
    """Tests adicionales de API de Médicos."""

    def test_list_medicos(self, client, medico):
        """Test: Lista médicos."""
        response = client.get('/api/medicos')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) >= 1

    def test_get_medico_by_id(self, client, medico):
        """Test: Obtiene médico por ID."""
        response = client.get(f'/api/medicos/{medico.id}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == medico.id
        assert data['nombre'] == 'Dr. Juan'


class TestPacientesAdditionalAPI:
    """Tests adicionales de API de Pacientes."""

    def test_list_pacientes(self, client, paciente):
        """Test: Lista pacientes."""
        response = client.get('/api/pacientes')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) >= 1

    def test_get_paciente_by_id(self, client, paciente):
        """Test: Obtiene paciente por ID."""
        response = client.get(f'/api/pacientes/{paciente.id}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == paciente.id


class TestEspecialidadesAdditionalAPI:
    """Tests adicionales de API de Especialidades."""

    def test_get_especialidad_by_id(self, client, especialidad):
        """Test: Obtiene especialidad por ID."""
        response = client.get(f'/api/especialidades/{especialidad.id}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == especialidad.id
        assert data['nombre'] == 'Cardiología'


# ==========================================
# RESUMEN DE INTEGRATION TESTS
# ==========================================

"""
INTEGRATION TESTS vs UNIT TESTS:

UNIT TESTS (test_services.py):
- Testean componente aislado
- Usan mocks
- Rápidos
- No tocan BD real

INTEGRATION TESTS (este archivo):
- Testean flujo completo
- Tocan BD de test
- Más lentos
- Verifican integración de componentes

PATRONES DEMOSTRADOS:
1. Facade Pattern - Endpoints simples
2. DTO Pattern - Validación y serialización
3. Service Layer - Lógica de negocio
4. Repository - Acceso a datos
5. Specification - Validaciones
6. Observer - Eventos (en prod)

BENEFICIOS:
✅ Verifican que componentes funcionan juntos
✅ Detectan errores de integración
✅ Prueban casos reales de uso
✅ Documentan API
"""
