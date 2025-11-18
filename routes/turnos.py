"""
PATRÓN: Facade Pattern + MVC Controller
=======================================

Este módulo implementa:
1. FACADE PATTERN: API REST simple que oculta complejidad interna
2. MVC PATTERN: Controller que maneja requests HTTP
3. DTO PATTERN: Marshmallow para serialización

FACADE PATTERN:
--------------
El controller expone endpoints simples (POST /turnos, GET /turnos, etc.)
que internamente coordinan múltiples servicios y operaciones complejas.

Cliente ve:
    POST /api/turnos → Turno creado

Internamente:
    1. Validar JSON (DTO)
    2. Validar disponibilidad (Service + Repository)
    3. Crear turno (Service)
    4. Notificar (Observer + Strategy)
    5. Retornar respuesta (DTO)

BENEFICIOS:
- API simple y consistente
- Cliente no conoce complejidad interna
- Fácil mantener y evolucionar backend sin afectar cliente
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import ValidationError
from datetime import datetime, date
from services.turno_service import TurnoService
from services.notification_service import NotificationService
from repositories.turno_repository import TurnoRepository
from schemas.turno_schema import turno_schema, turnos_schema
from models import Turno, Usuario, Paciente, Medico
import os

# Blueprint de Flask
turnos_bp = Blueprint('turnos', __name__)

# ==========================================
# CONFIGURACIÓN DE EMAIL
# ==========================================
def get_email_config():
    """Obtiene configuración de email desde variables de entorno."""
    return {
        'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'port': int(os.getenv('SMTP_PORT', 587)),
        'username': os.getenv('SMTP_USERNAME', ''),
        'password': os.getenv('SMTP_PASSWORD', ''),
        'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
    }

# ==========================================
# INICIALIZACIÓN DE SERVICIOS
# ==========================================
# PATRÓN: Dependency Injection (manual)
# En una aplicación más grande, usar un DI Container

# Crear instancias de servicios
turno_repository = TurnoRepository()
turno_service = TurnoService(turno_repository=turno_repository)

# Configurar notification service con config de email
email_config = get_email_config()
config = {'email': email_config}
notification_service = NotificationService(config=config)

# OBSERVER PATTERN: Suscribir notification service
turno_service.attach_observer(notification_service)


# ==========================================
# ENDPOINTS - FACADE PATTERN
# ==========================================

@turnos_bp.route('', methods=['POST'])
@jwt_required()
def create_turno():
    """
    Crea un nuevo turno.

    SEGURIDAD:
    - Pacientes: Solo pueden crear turnos para sí mismos
    - Médicos: No pueden crear turnos
    - Admin/Recepcionista: Pueden crear turnos para cualquier paciente

    PATRÓN: Facade Pattern
    - Endpoint simple: POST /api/turnos
    - Internamente ejecuta flujo complejo

    Request:
    ``` json
    {
        "paciente_id": 1,  # Ignorado si el usuario es paciente
        "medico_id": 5,
        "ubicacion_id": 1,
        "fecha": "2024-12-15",
        "hora": "14:30",
        "duracion_min": 30,
        "motivo_consulta": "Control"
    }
    ```

    Response:
    ```json
    {
        "id": 123,
        "codigo_turno": "T-20241215-0001",
        "estado": "pendiente",
        ...
    }
    ```

    FLUJO INTERNO (oculto al cliente):
    1. Validar JSON (Marshmallow)
    2. Verificar autorización
    3. Llamar Service Layer
    4. Service valida disponibilidad
    5. Service crea turno
    6. Service notifica observers
    7. Observer envía email
    8. Retornar turno serializado
    """
    try:
        # Obtener usuario actual (PyJWT 2.10+ devuelve subject como string)
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        # 1. OBTENER DATOS (DTO Pattern)
        data = request.get_json()

        # Validar campos requeridos
        required_fields = ['medico_id', 'ubicacion_id', 'fecha', 'hora']
        if not all(k in data for k in required_fields):
            return jsonify({'error': 'Faltan campos requeridos'}), 400

        # Parsear fecha y hora
        fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        hora = datetime.strptime(data['hora'], '%H:%M').time()

        # AUTORIZACIÓN: Determinar paciente_id según rol
        if user_rol == 'paciente':
            # Pacientes solo pueden crear turnos para sí mismos
            paciente = Paciente.query.filter_by(usuario_id=current_user_id).first()
            if not paciente:
                return jsonify({'error': 'Paciente no encontrado'}), 404
            paciente_id = paciente.id

        elif user_rol in ['admin', 'recepcionista']:
            # Admin y recepcionista pueden crear turnos para cualquier paciente
            if 'paciente_id' not in data:
                return jsonify({'error': 'Falta campo paciente_id'}), 400
            paciente_id = data['paciente_id']

        elif user_rol == 'medico':
            # Médicos no pueden crear turnos (solo admin/recepcionista/pacientes)
            return jsonify({'error': 'Los médicos no pueden crear turnos'}), 403

        else:
            return jsonify({'error': 'Rol no autorizado'}), 403

        # 2. LLAMAR SERVICE LAYER (Facade Pattern)
        # Este único método coordina toda la operación compleja
        turno = turno_service.crear_turno(
            paciente_id=paciente_id,
            medico_id=data['medico_id'],
            ubicacion_id=data['ubicacion_id'],
            fecha=fecha,
            hora=hora,
            duracion_min=data.get('duracion_min', 30),
            motivo_consulta=data.get('motivo_consulta'),
            usuario_id=current_user_id
        )

        # 3. SERIALIZAR RESPUESTA (DTO Pattern)
        return jsonify(turno_schema.dump(turno)), 201

    except ValueError as e:
        # Errores de validación de negocio
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        # Errores inesperados
        return jsonify({'error': 'Error interno del servidor'}), 500


@turnos_bp.route('/<int:turno_id>', methods=['GET'])
@jwt_required()
def get_turno(turno_id):
    """
    Obtiene un turno por ID.

    SEGURIDAD:
    - Pacientes: Solo pueden ver sus propios turnos
    - Médicos: Solo pueden ver sus propios turnos
    - Admin/Recepcionista: Pueden ver cualquier turno

    FACADE: Simplifica obtención de turno con relaciones cargadas

    GET /api/turnos/123
    """
    try:
        # Obtener usuario actual (PyJWT 2.10+ devuelve subject como string)
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        turno = turno_service.get_by_id(turno_id)

        # AUTORIZACIÓN: Verificar que el usuario pueda ver este turno
        if user_rol == 'paciente':
            paciente = Paciente.query.filter_by(usuario_id=current_user_id).first()
            if not paciente or turno.paciente_id != paciente.id:
                return jsonify({'error': 'No tiene permiso para ver este turno'}), 403

        elif user_rol == 'medico':
            medico = Medico.query.filter_by(usuario_id=current_user_id).first()
            if not medico or turno.medico_id != medico.id:
                return jsonify({'error': 'No tiene permiso para ver este turno'}), 403

        # Admin y recepcionista pueden ver cualquier turno

        return jsonify(turno_schema.dump(turno)), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500


@turnos_bp.route('', methods=['GET'])
@jwt_required()
def list_turnos():
    """
    Lista turnos con filtros opcionales.

    SEGURIDAD:
    - Pacientes: Solo pueden ver sus propios turnos
    - Médicos: Solo pueden ver sus propios turnos
    - Admin/Recepcionista: Pueden ver todos los turnos

    FACADE: Query params simples ocultan query SQL compleja

    GET /api/turnos?desde=2024-12-01&hasta=2024-12-31

    Query params opcionales:
    - desde: Fecha desde (YYYY-MM-DD)
    - hasta: Fecha hasta (YYYY-MM-DD)
    - estado: Estado del turno
    - limit: Límite de resultados
    - offset: Offset para paginación
    """
    try:
        # Obtener usuario actual (PyJWT 2.10+ devuelve subject como string)
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        # Obtener usuario
        usuario = Usuario.query.get(current_user_id)
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Obtener parámetros
        desde = request.args.get('desde')
        hasta = request.args.get('hasta')
        estado = request.args.get('estado')
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)

        # Parsear fechas
        fecha_desde = datetime.strptime(desde, '%Y-%m-%d').date() if desde else None
        fecha_hasta = datetime.strptime(hasta, '%Y-%m-%d').date() if hasta else None

        # AUTORIZACIÓN: Filtrar según rol
        if user_rol == 'paciente':
            # Pacientes solo ven sus propios turnos
            paciente = Paciente.query.filter_by(usuario_id=current_user_id).first()
            if not paciente:
                return jsonify({'error': 'Paciente no encontrado'}), 404

            turnos = turno_service.buscar_turnos_paciente(
                paciente.id, fecha_desde, fecha_hasta
            )

        elif user_rol == 'medico':
            # Médicos solo ven sus propios turnos
            medico = Medico.query.filter_by(usuario_id=current_user_id).first()
            if not medico:
                return jsonify({'error': 'Médico no encontrado'}), 404

            turnos = turno_service.buscar_turnos_medico(
                medico.id, fecha_desde, fecha_hasta
            )

        elif user_rol in ['admin', 'recepcionista']:
            # Admin y recepcionista pueden ver todos los turnos
            filters = {}
            if estado:
                filters['estado'] = estado
            turnos = turno_service.get_all(filters, limit, offset)

        else:
            return jsonify({'error': 'Rol no autorizado'}), 403

        return jsonify(turnos_schema.dump(turnos)), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@turnos_bp.route('/<int:turno_id>/cancelar', methods=['PATCH'])
def cancelar_turno(turno_id):
    """
    Cancela un turno.

    FACADE: Endpoint dedicado que internamente cambia estado y notifica

    PATCH /api/turnos/123/cancelar
    """
    try:
        turno = turno_service.cancelar_turno(turno_id)
        return jsonify(turno_schema.dump(turno)), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500


@turnos_bp.route('/<int:turno_id>/confirmar', methods=['PATCH'])
def confirmar_turno(turno_id):
    """
    Confirma un turno.

    PATCH /api/turnos/123/confirmar
    """
    try:
        turno = turno_service.confirmar_turno(turno_id)
        return jsonify(turno_schema.dump(turno)), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500


@turnos_bp.route('/<int:turno_id>/completar', methods=['PATCH'])
def completar_turno(turno_id):
    """
    Marca turno como completado (paciente asistió).

    PATCH /api/turnos/123/completar
    """
    try:
        turno = turno_service.marcar_completado(turno_id)
        return jsonify(turno_schema.dump(turno)), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500


@turnos_bp.route('/<int:turno_id>/ausente', methods=['PATCH'])
def marcar_ausente(turno_id):
    """
    Marca turno como ausente (paciente no asistió).

    PATCH /api/turnos/123/ausente
    """
    try:
        turno = turno_service.marcar_ausente(turno_id)
        return jsonify(turno_schema.dump(turno)), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500


@turnos_bp.route('/fechas-disponibles', methods=['GET'])
def get_fechas_disponibles():
    """
    Obtiene las fechas con disponibilidad de un médico en los próximos N días.

    GET /api/turnos/fechas-disponibles?medico_id=5&dias=30&duracion=30

    Query params:
    - medico_id: ID del médico (requerido)
    - dias: Cantidad de días a buscar desde hoy (default: 30)
    - duracion: Duración en minutos (default: 30)

    Response:
    ```json
    {
        "medico_id": 5,
        "fechas_disponibles": [
            {"fecha": "2025-11-05", "tiene_horarios": true},
            {"fecha": "2025-11-06", "tiene_horarios": true},
            ...
        ]
    }
    ```
    """
    try:
        medico_id = request.args.get('medico_id', type=int)
        dias = request.args.get('dias', default=30, type=int)
        duracion = request.args.get('duracion', default=30, type=int)

        if not medico_id:
            return jsonify({'error': 'medico_id es requerido'}), 400

        from datetime import timedelta
        fecha_inicio = date.today()
        fecha_fin = fecha_inicio + timedelta(days=dias)

        fechas_disponibles = []
        fecha_actual = fecha_inicio

        while fecha_actual <= fecha_fin:
            horarios = turno_service.obtener_horarios_disponibles(
                medico_id, fecha_actual, duracion
            )
            if horarios:  # Si tiene al menos un horario disponible
                fechas_disponibles.append({
                    'fecha': fecha_actual.strftime('%Y-%m-%d'),
                    'cantidad_horarios': len(horarios)
                })
            fecha_actual += timedelta(days=1)

        return jsonify({
            'medico_id': medico_id,
            'fechas_disponibles': fechas_disponibles
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@turnos_bp.route('/disponibilidad', methods=['GET'])
def get_disponibilidad():
    """
    Obtiene horarios disponibles de un médico en una fecha.

    FACADE: Endpoint simple que oculta algoritmo complejo de disponibilidad

    GET /api/turnos/disponibilidad?medico_id=5&fecha=2024-12-15&duracion=30

    Query params:
    - medico_id: ID del médico (requerido)
    - fecha: Fecha en formato YYYY-MM-DD (requerido)
    - duracion: Duración en minutos (default: 30)

    Response:
    ```json
    {
        "medico_id": 5,
        "fecha": "2024-12-15",
        "horarios_disponibles": ["08:00", "08:30", "09:00", ...]
    }
    ```

    COMPLEJIDAD INTERNA (oculta al cliente):
    1. Obtener horarios de atención del médico ese día
    2. Generar slots de tiempo según duración
    3. Buscar turnos ya asignados
    4. Calcular superposiciones
    5. Filtrar slots ocupados
    6. Retornar solo disponibles
    """
    try:
        # Validar parámetros
        medico_id = request.args.get('medico_id', type=int)
        fecha_str = request.args.get('fecha')
        duracion = request.args.get('duracion', default=30, type=int)

        if not medico_id or not fecha_str:
            return jsonify({'error': 'medico_id y fecha son requeridos'}), 400

        # Parsear fecha
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

        # Delegar a service (Facade)
        horarios = turno_service.obtener_horarios_disponibles(
            medico_id, fecha, duracion
        )

        # Formatear horarios para respuesta
        horarios_str = [h.strftime('%H:%M') for h in horarios]

        return jsonify({
            'medico_id': medico_id,
            'fecha': fecha_str,
            'duracion_min': duracion,
            'horarios_disponibles': horarios_str
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@turnos_bp.route('/estadisticas', methods=['GET'])
def get_estadisticas():
    """
    Obtiene estadísticas de turnos.

    FACADE: Endpoint de reportes que agrega datos de múltiples queries

    GET /api/turnos/estadisticas?desde=2024-12-01&hasta=2024-12-31

    Response:
    ```json
    {
        "periodo": {"desde": "2024-12-01", "hasta": "2024-12-31"},
        "turnos_por_estado": {
            "pendiente": 50,
            "confirmado": 30,
            "completado": 100,
            "cancelado": 20,
            "ausente": 10
        },
        "turnos_por_especialidad": {
            "Cardiología": 80,
            "Pediatría": 60,
            ...
        },
        "tasa_ausentismo": 8.5
    }
    ```
    """
    try:
        # Parámetros
        desde = request.args.get('desde')
        hasta = request.args.get('hasta')

        if not desde or not hasta:
            return jsonify({'error': 'desde y hasta son requeridos'}), 400

        # Parsear fechas
        fecha_desde = datetime.strptime(desde, '%Y-%m-%d').date()
        fecha_hasta = datetime.strptime(hasta, '%Y-%m-%d').date()

        # Delegar a service (Facade)
        estadisticas = turno_service.obtener_estadisticas_periodo(
            fecha_desde, fecha_hasta
        )

        # Agregar información del período
        estadisticas['periodo'] = {
            'desde': desde,
            'hasta': hasta
        }

        return jsonify(estadisticas), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==========================================
# DOCUMENTACIÓN DEL PATRÓN FACADE
# ==========================================

"""
RESUMEN DEL FACADE PATTERN EN ESTE CONTROLADOR:
===============================================

COMPLEJIDAD OCULTA:
------------------
Cada endpoint simple oculta operaciones complejas:

1. POST /turnos:
   - Validar JSON
   - Verificar disponibilidad (query compleja)
   - Crear turno
   - Generar código único
   - Notificar paciente (email)
   - Registrar notificación
   - Retornar respuesta

2. GET /disponibilidad:
   - Buscar horarios médico
   - Generar slots de tiempo
   - Buscar turnos existentes
   - Calcular superposiciones
   - Filtrar disponibles

API SIMPLE:
----------
Cliente solo ve:
- POST /api/turnos → 201 Created
- GET /api/turnos/123 → 200 OK
- PATCH /api/turnos/123/cancelar → 200 OK

BENEFICIOS:
----------
1. Cliente desacoplado de implementación
2. Fácil cambiar backend sin afectar cliente
3. API consistente y predecible
4. Testeable (mock services)

COMPARACIÓN:

Sin Facade:
    Cliente debe llamar múltiples endpoints:
    POST /validar-disponibilidad
    POST /crear-turno
    POST /enviar-notificacion

Con Facade:
    Cliente llama un solo endpoint:
    POST /turnos
"""


# ==========================================
# RECORDATORIOS AUTOMÁTICOS
# ==========================================

@turnos_bp.route('/<int:turno_id>/enviar-recordatorio', methods=['POST'])
def enviar_recordatorio(turno_id):
    """
    Envía recordatorio manual de un turno.

    PATRÓN: Observer Pattern + Strategy Pattern
    - Usa RecordatorioService para enviar notificación
    - Strategy Pattern para canal de envío (email)

    POST /api/turnos/123/enviar-recordatorio
    """
    try:
        from services.recordatorio_service import RecordatorioService

        recordatorio_service = RecordatorioService()
        recordatorio_service.enviar_recordatorio_manual(turno_id)

        return jsonify({
            'mensaje': 'Recordatorio enviado exitosamente',
            'turno_id': turno_id
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
