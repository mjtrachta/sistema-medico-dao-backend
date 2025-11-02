"""
Blueprint de Horarios de Médicos
==================================

PATRÓN: Facade Pattern
- Endpoints simples que ocultan complejidad del service layer

PERMISOS:
- Médicos: pueden gestionar sus propios horarios
- Admin: puede gestionar horarios de todos los médicos
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from services.horario_medico_service import HorarioMedicoService
from models import Medico
from datetime import time

horarios_bp = Blueprint('horarios', __name__)

# Service
horario_service = HorarioMedicoService()


@horarios_bp.route('', methods=['GET'])
@jwt_required()
def list_horarios():
    """
    Lista horarios según el rol del usuario.

    - Médicos: solo sus propios horarios
    - Admin: todos los horarios (o filtrados por medico_id)

    Query params:
        - medico_id: filtrar por médico (solo admin)
        - ubicacion_id: filtrar por ubicación
        - solo_activos: true/false (default: true)
    """
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        # Obtener filtros de query params
        medico_id_param = request.args.get('medico_id', type=int)
        ubicacion_id_param = request.args.get('ubicacion_id', type=int)
        solo_activos = request.args.get('solo_activos', 'true').lower() == 'true'

        horarios = []

        if user_rol == 'medico':
            # Médico solo ve sus propios horarios
            medico = Medico.query.filter_by(usuario_id=current_user_id).first()
            if not medico:
                return jsonify({'error': 'Médico no encontrado'}), 404

            if ubicacion_id_param:
                # Filtrar por ubicación específica
                from models import HorarioMedico
                query = HorarioMedico.query.filter_by(
                    medico_id=medico.id,
                    ubicacion_id=ubicacion_id_param
                )
                if solo_activos:
                    query = query.filter_by(activo=True)
                horarios = query.order_by(
                    HorarioMedico.dia_semana,
                    HorarioMedico.hora_inicio
                ).all()
            else:
                horarios = horario_service.obtener_horarios_medico(medico.id, solo_activos)

        elif user_rol == 'admin':
            # Admin puede ver todos o filtrar por médico
            if medico_id_param:
                horarios = horario_service.obtener_horarios_medico(medico_id_param, solo_activos)
            elif ubicacion_id_param:
                horarios = horario_service.obtener_horarios_ubicacion(ubicacion_id_param, solo_activos)
            else:
                # Obtener todos los horarios
                from models import HorarioMedico
                query = HorarioMedico.query
                if solo_activos:
                    query = query.filter_by(activo=True)
                horarios = query.order_by(
                    HorarioMedico.medico_id,
                    HorarioMedico.dia_semana,
                    HorarioMedico.hora_inicio
                ).all()

        else:
            return jsonify({'error': 'Rol no autorizado'}), 403

        # Serializar
        resultado = []
        for h in horarios:
            resultado.append({
                'id': h.id,
                'medico_id': h.medico_id,
                'medico': {
                    'id': h.medico.id,
                    'nombre_completo': h.medico.nombre_completo,
                    'especialidad': h.medico.especialidad.nombre if h.medico.especialidad else None
                } if h.medico else None,
                'ubicacion_id': h.ubicacion_id,
                'ubicacion': {
                    'id': h.ubicacion.id,
                    'nombre': h.ubicacion.nombre,
                    'direccion': h.ubicacion.direccion,
                    'ciudad': h.ubicacion.ciudad
                } if h.ubicacion else None,
                'dia_semana': h.dia_semana,
                'hora_inicio': h.hora_inicio.strftime('%H:%M'),
                'hora_fin': h.hora_fin.strftime('%H:%M'),
                'activo': h.activo
            })

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@horarios_bp.route('', methods=['POST'])
@jwt_required()
def create_horario():
    """
    Crea un nuevo horario.

    Permisos:
    - Médicos: pueden crear sus propios horarios
    - Admin: puede crear horarios para cualquier médico

    Body:
        - medico_id: ID del médico (si admin, requerido; si médico, se usa el propio)
        - ubicacion_id: ID de la ubicación (requerido)
        - dia_semana: lunes, martes, etc. (requerido)
        - hora_inicio: HH:MM formato 24h (requerido)
        - hora_fin: HH:MM formato 24h (requerido)
    """
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        data = request.get_json()

        # Validar datos requeridos
        if not data.get('ubicacion_id'):
            return jsonify({'error': 'ubicacion_id es requerido'}), 400
        if not data.get('dia_semana'):
            return jsonify({'error': 'dia_semana es requerido'}), 400
        if not data.get('hora_inicio'):
            return jsonify({'error': 'hora_inicio es requerido'}), 400
        if not data.get('hora_fin'):
            return jsonify({'error': 'hora_fin es requerido'}), 400

        # Determinar el médico
        if user_rol == 'medico':
            # Médico crea su propio horario
            medico = Medico.query.filter_by(usuario_id=current_user_id).first()
            if not medico:
                return jsonify({'error': 'Médico no encontrado'}), 404
            medico_id = medico.id

        elif user_rol == 'admin':
            # Admin debe especificar el médico
            if not data.get('medico_id'):
                return jsonify({'error': 'medico_id es requerido para admin'}), 400
            medico_id = data['medico_id']

        else:
            return jsonify({'error': 'Rol no autorizado'}), 403

        # Parsear horas
        try:
            hora_inicio = time.fromisoformat(data['hora_inicio'])
            hora_fin = time.fromisoformat(data['hora_fin'])
        except ValueError:
            return jsonify({'error': 'Formato de hora inválido. Use HH:MM'}), 400

        # Crear horario
        horario = horario_service.crear_horario(
            medico_id=medico_id,
            ubicacion_id=data['ubicacion_id'],
            dia_semana=data['dia_semana'],
            hora_inicio=hora_inicio,
            hora_fin=hora_fin
        )

        return jsonify({
            'id': horario.id,
            'medico_id': horario.medico_id,
            'ubicacion_id': horario.ubicacion_id,
            'dia_semana': horario.dia_semana,
            'hora_inicio': horario.hora_inicio.strftime('%H:%M'),
            'hora_fin': horario.hora_fin.strftime('%H:%M'),
            'mensaje': 'Horario creado exitosamente'
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@horarios_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_horario(id):
    """
    Obtiene un horario por ID.

    Permisos:
    - Médicos: solo pueden ver sus propios horarios
    - Admin: puede ver cualquier horario
    """
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        horario = horario_service.obtener_por_id(id)

        # Verificar permisos
        if user_rol == 'medico':
            medico = Medico.query.filter_by(usuario_id=current_user_id).first()
            if not medico or horario.medico_id != medico.id:
                return jsonify({'error': 'No tiene permiso para ver este horario'}), 403

        elif user_rol != 'admin':
            return jsonify({'error': 'Rol no autorizado'}), 403

        return jsonify({
            'id': horario.id,
            'medico_id': horario.medico_id,
            'medico': {
                'id': horario.medico.id,
                'nombre_completo': horario.medico.nombre_completo
            } if horario.medico else None,
            'ubicacion_id': horario.ubicacion_id,
            'ubicacion': {
                'id': horario.ubicacion.id,
                'nombre': horario.ubicacion.nombre,
                'direccion': horario.ubicacion.direccion
            } if horario.ubicacion else None,
            'dia_semana': horario.dia_semana,
            'hora_inicio': horario.hora_inicio.strftime('%H:%M'),
            'hora_fin': horario.hora_fin.strftime('%H:%M'),
            'activo': horario.activo
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@horarios_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_horario(id):
    """
    Actualiza un horario existente.

    Permisos:
    - Médicos: solo pueden actualizar sus propios horarios
    - Admin: puede actualizar cualquier horario

    Body (todos opcionales):
        - dia_semana: nuevo día
        - hora_inicio: nueva hora inicio (HH:MM)
        - hora_fin: nueva hora fin (HH:MM)
        - ubicacion_id: nueva ubicación
    """
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        # Obtener horario existente
        horario_existente = horario_service.obtener_por_id(id)

        # Verificar permisos
        if user_rol == 'medico':
            medico = Medico.query.filter_by(usuario_id=current_user_id).first()
            if not medico or horario_existente.medico_id != medico.id:
                return jsonify({'error': 'No tiene permiso para actualizar este horario'}), 403

        elif user_rol != 'admin':
            return jsonify({'error': 'Rol no autorizado'}), 403

        data = request.get_json()

        # Parsear horas si se proporcionan
        hora_inicio = None
        hora_fin = None

        if data.get('hora_inicio'):
            try:
                hora_inicio = time.fromisoformat(data['hora_inicio'])
            except ValueError:
                return jsonify({'error': 'Formato de hora_inicio inválido. Use HH:MM'}), 400

        if data.get('hora_fin'):
            try:
                hora_fin = time.fromisoformat(data['hora_fin'])
            except ValueError:
                return jsonify({'error': 'Formato de hora_fin inválido. Use HH:MM'}), 400

        # Actualizar horario
        horario = horario_service.actualizar_horario(
            horario_id=id,
            dia_semana=data.get('dia_semana'),
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            ubicacion_id=data.get('ubicacion_id')
        )

        return jsonify({
            'id': horario.id,
            'medico_id': horario.medico_id,
            'ubicacion_id': horario.ubicacion_id,
            'dia_semana': horario.dia_semana,
            'hora_inicio': horario.hora_inicio.strftime('%H:%M'),
            'hora_fin': horario.hora_fin.strftime('%H:%M'),
            'mensaje': 'Horario actualizado exitosamente'
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@horarios_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_horario(id):
    """
    Desactiva un horario (soft delete).

    Permisos:
    - Médicos: solo pueden desactivar sus propios horarios
    - Admin: puede desactivar cualquier horario
    """
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        # Obtener horario existente
        horario_existente = horario_service.obtener_por_id(id)

        # Verificar permisos
        if user_rol == 'medico':
            medico = Medico.query.filter_by(usuario_id=current_user_id).first()
            if not medico or horario_existente.medico_id != medico.id:
                return jsonify({'error': 'No tiene permiso para eliminar este horario'}), 403

        elif user_rol != 'admin':
            return jsonify({'error': 'Rol no autorizado'}), 403

        horario = horario_service.desactivar_horario(id)

        return jsonify({
            'id': horario.id,
            'mensaje': 'Horario desactivado exitosamente'
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@horarios_bp.route('/medico/<int:medico_id>/ubicacion/<int:ubicacion_id>', methods=['GET'])
@jwt_required()
def get_horarios_medico_ubicacion(medico_id, ubicacion_id):
    """
    Obtiene horarios de un médico en una ubicación específica.

    Útil para el módulo de turnos: mostrar disponibilidad por ubicación.

    Query params:
        - dia_semana: filtrar por día específico (opcional)
    """
    try:
        dia_semana = request.args.get('dia_semana')

        from models import HorarioMedico
        query = HorarioMedico.query.filter_by(
            medico_id=medico_id,
            ubicacion_id=ubicacion_id,
            activo=True
        )

        if dia_semana:
            query = query.filter_by(dia_semana=dia_semana.lower())

        horarios = query.order_by(
            HorarioMedico.dia_semana,
            HorarioMedico.hora_inicio
        ).all()

        # Serializar
        resultado = []
        for h in horarios:
            resultado.append({
                'id': h.id,
                'dia_semana': h.dia_semana,
                'hora_inicio': h.hora_inicio.strftime('%H:%M'),
                'hora_fin': h.hora_fin.strftime('%H:%M')
            })

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
