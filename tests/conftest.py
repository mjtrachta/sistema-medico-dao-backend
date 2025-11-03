"""
Configuración de Pytest - Fixtures compartidos
==============================================

PATRÓN: Test Fixtures (Factory Pattern para testing)

Este archivo define fixtures reutilizables para todos los tests.
Los fixtures son instancias de objetos necesarios para testing.
"""

import pytest
from datetime import date, time, datetime
from app import create_app
from models import db, Paciente, Medico, Especialidad, Ubicacion, Turno, HorarioMedico


@pytest.fixture
def app():
    """
    Fixture: Aplicación Flask en modo testing.

    PATRÓN: Factory Pattern
    - Usa create_app('testing') para crear app de prueba
    - Base de datos en memoria (SQLite)
    """
    app = create_app('testing')

    with app.app_context():
        # Crear todas las tablas
        db.create_all()

        yield app

        # Limpiar después de tests
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """
    Fixture: Cliente de prueba para hacer requests HTTP.

    Permite probar endpoints sin levantar servidor.
    """
    return app.test_client()


@pytest.fixture
def db_session(app):
    """
    Fixture: Sesión de base de datos.

    Automáticamente hace rollback después de cada test.
    """
    with app.app_context():
        yield db.session
        db.session.rollback()


# ==========================================
# FIXTURES DE DATOS - Factory Pattern
# ==========================================

@pytest.fixture
def especialidad(db_session):
    """
    Fixture: Crea una especialidad de prueba.

    PATRÓN: Factory Pattern para testing
    - Retorna objeto listo para usar en tests
    """
    especialidad = Especialidad(
        nombre='Cardiología',
        descripcion='Especialidad del corazón',
        duracion_turno_min=30
    )
    db_session.add(especialidad)
    db_session.commit()
    return especialidad


@pytest.fixture
def ubicacion(db_session):
    """Fixture: Crea una ubicación de prueba."""
    ubicacion = Ubicacion(
        nombre='Consultorio Test',
        direccion='Calle Falsa 123',
        ciudad='Test City',
        telefono='123456789'
    )
    db_session.add(ubicacion)
    db_session.commit()
    return ubicacion


@pytest.fixture
def medico(db_session, especialidad):
    """Fixture: Crea un médico de prueba."""
    medico = Medico(
        nombre='Dr. Juan',
        apellido='Pérez',
        matricula='MN12345',
        especialidad_id=especialidad.id,
        email='dr.perez@test.com',
        telefono='123456789'
    )
    db_session.add(medico)
    db_session.commit()
    return medico


@pytest.fixture
def paciente(db_session):
    """Fixture: Crea un paciente de prueba."""
    paciente = Paciente(
        nombre='Juan',
        apellido='González',
        tipo_documento='DNI',
        nro_documento='12345678',
        nro_historia_clinica='HC-TEST-001',
        fecha_nacimiento=date(1990, 1, 1),
        genero='masculino',
        email='utn-frc-dao-g31@yopmail.com',
        telefono='987654321'
    )
    db_session.add(paciente)
    db_session.commit()
    return paciente


@pytest.fixture
def horario_medico(db_session, medico, ubicacion):
    """Fixture: Crea un horario de atención."""
    horario = HorarioMedico(
        medico_id=medico.id,
        ubicacion_id=ubicacion.id,
        dia_semana='lunes',
        hora_inicio=time(8, 0),
        hora_fin=time(12, 0),
        activo=True
    )
    db_session.add(horario)
    db_session.commit()
    return horario


@pytest.fixture
def turno(db_session, paciente, medico, ubicacion):
    """Fixture: Crea un turno de prueba."""
    turno = Turno(
        codigo_turno='T-TEST-001',
        paciente_id=paciente.id,
        medico_id=medico.id,
        ubicacion_id=ubicacion.id,
        fecha=date(2025, 12, 15),
        hora=time(10, 0),
        duracion_min=30,
        estado='pendiente',
        motivo_consulta='Test'
    )
    db_session.add(turno)
    db_session.commit()
    return turno


# ==========================================
# FIXTURES DE AUTENTICACIÓN JWT
# ==========================================

@pytest.fixture
def admin_user(db_session):
    """Fixture: Crea un usuario admin de prueba."""
    from models import Usuario
    admin = Usuario(
        nombre_usuario='admin_test',
        email='admin@test.com',
        rol='admin'
    )
    admin.set_password('testpass123')
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def medico_user(db_session, medico):
    """Fixture: Crea un usuario médico de prueba."""
    from models import Usuario
    user = Usuario(
        nombre_usuario='medico_test',
        email='medico@test.com',
        rol='medico'
    )
    user.set_password('testpass123')
    db_session.add(user)
    db_session.commit()
    # Asociar usuario con médico
    medico.usuario_id = user.id
    db_session.commit()
    return user


@pytest.fixture
def paciente_user(db_session, paciente):
    """Fixture: Crea un usuario paciente de prueba."""
    from models import Usuario
    user = Usuario(
        nombre_usuario='paciente_test',
        email='paciente@test.com',
        rol='paciente'
    )
    user.set_password('testpass123')
    db_session.add(user)
    db_session.commit()
    # Asociar usuario con paciente
    paciente.usuario_id = user.id
    db_session.commit()
    return user


@pytest.fixture
def admin_token(app, admin_user):
    """Fixture: Genera token JWT para admin."""
    from flask_jwt_extended import create_access_token
    with app.app_context():
        token = create_access_token(
            identity=str(admin_user.id),
            additional_claims={'rol': admin_user.rol}
        )
        return token


@pytest.fixture
def medico_token(app, medico_user):
    """Fixture: Genera token JWT para médico."""
    from flask_jwt_extended import create_access_token
    with app.app_context():
        token = create_access_token(
            identity=str(medico_user.id),
            additional_claims={'rol': medico_user.rol}
        )
        return token


@pytest.fixture
def paciente_token(app, paciente_user):
    """Fixture: Genera token JWT para paciente."""
    from flask_jwt_extended import create_access_token
    with app.app_context():
        token = create_access_token(
            identity=str(paciente_user.id),
            additional_claims={'rol': paciente_user.rol}
        )
        return token


@pytest.fixture
def auth_headers_admin(admin_token):
    """Fixture: Headers de autorización para admin."""
    return {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def auth_headers_medico(medico_token):
    """Fixture: Headers de autorización para médico."""
    return {
        'Authorization': f'Bearer {medico_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def auth_headers_paciente(paciente_token):
    """Fixture: Headers de autorización para paciente."""
    return {
        'Authorization': f'Bearer {paciente_token}',
        'Content-Type': 'application/json'
    }


# ==========================================
# FIXTURES DE MOCKS
# ==========================================

@pytest.fixture
def mock_notification_service(mocker):
    """
    Fixture: Mock de NotificationService.

    PATRÓN: Mock Object Pattern
    - Simula el servicio de notificaciones
    - Permite verificar que se llamó sin enviar emails reales
    """
    mock = mocker.Mock()
    mock.update.return_value = None
    return mock
