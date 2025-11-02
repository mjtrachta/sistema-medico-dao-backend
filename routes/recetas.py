"""
Blueprint de Recetas Electrónicas
==================================

PATRÓN: Facade Pattern
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from services.receta_service import RecetaService
from models import Paciente, Medico

recetas_bp = Blueprint('recetas', __name__)

# Service
receta_service = RecetaService()


@recetas_bp.route('', methods=['GET'])
@jwt_required()
def list_recetas():
    """
    Lista recetas según el rol del usuario.

    - Médicos: recetas que emitieron
    - Pacientes: solo sus propias recetas
    - Admin: todas las recetas
    """
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        if user_rol == 'paciente':
            # Paciente solo ve sus propias recetas
            paciente = Paciente.query.filter_by(usuario_id=current_user_id).first()
            if not paciente:
                return jsonify({'error': 'Paciente no encontrado'}), 404
            recetas = receta_service.obtener_recetas_paciente(paciente.id, solo_activas=False)

        elif user_rol == 'medico':
            # Médico ve recetas que emitió
            medico = Medico.query.filter_by(usuario_id=current_user_id).first()
            if not medico:
                return jsonify({'error': 'Médico no encontrado'}), 404
            recetas = receta_service.obtener_recetas_medico(medico.id)

        elif user_rol in ['admin', 'recepcionista']:
            # Admin/recepcionista ve todas
            recetas = receta_service.obtener_todas(limit=100)

        else:
            return jsonify({'error': 'Rol no autorizado'}), 403

        # Serializar
        resultado = []
        for r in recetas:
            items = []
            for item in r.items:
                items.append({
                    'nombre_medicamento': item.nombre_medicamento,
                    'dosis': item.dosis,
                    'frecuencia': item.frecuencia,
                    'cantidad': item.cantidad,
                    'duracion_dias': item.duracion_dias,
                    'instrucciones': item.instrucciones
                })

            resultado.append({
                'id': r.id,
                'codigo_receta': r.codigo_receta,
                'fecha': r.fecha.isoformat(),
                'estado': r.estado,
                'valida_hasta': r.valida_hasta.isoformat() if r.valida_hasta else None,
                'paciente': {
                    'id': r.paciente.id,
                    'nombre_completo': r.paciente.nombre_completo
                } if r.paciente else None,
                'medico': {
                    'id': r.medico.id,
                    'nombre_completo': r.medico.nombre_completo
                } if r.medico else None,
                'items': items
            })

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recetas_bp.route('/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def get_recetas_paciente(paciente_id):
    """
    Obtiene recetas de un paciente.

    Permisos:
    - El mismo paciente
    - Médicos
    - Admin/Recepcionista
    """
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        # Verificar permisos
        if user_rol == 'paciente':
            paciente = Paciente.query.filter_by(usuario_id=current_user_id).first()
            if not paciente or paciente.id != paciente_id:
                return jsonify({'error': 'No tiene permiso para ver estas recetas'}), 403

        elif user_rol not in ['medico', 'admin', 'recepcionista']:
            return jsonify({'error': 'Rol no autorizado'}), 403

        solo_activas = request.args.get('solo_activas', 'false').lower() == 'true'
        recetas = receta_service.obtener_recetas_paciente(paciente_id, solo_activas)

        # Serializar
        resultado = []
        for r in recetas:
            items = []
            for item in r.items:
                items.append({
                    'nombre_medicamento': item.nombre_medicamento,
                    'dosis': item.dosis,
                    'frecuencia': item.frecuencia,
                    'cantidad': item.cantidad,
                    'duracion_dias': item.duracion_dias,
                    'instrucciones': item.instrucciones
                })

            resultado.append({
                'id': r.id,
                'codigo_receta': r.codigo_receta,
                'fecha': r.fecha.isoformat(),
                'estado': r.estado,
                'valida_hasta': r.valida_hasta.isoformat() if r.valida_hasta else None,
                'medico': {
                    'id': r.medico.id,
                    'nombre_completo': r.medico.nombre_completo
                } if r.medico else None,
                'items': items
            })

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recetas_bp.route('', methods=['POST'])
@jwt_required()
def create_receta():
    """
    Crea una receta electrónica.

    Permisos: Solo médicos
    """
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        if user_rol != 'medico':
            return jsonify({'error': 'Solo los médicos pueden crear recetas'}), 403

        # Obtener ID del médico
        medico = Medico.query.filter_by(usuario_id=current_user_id).first()
        if not medico:
            return jsonify({'error': 'Médico no encontrado'}), 404

        data = request.get_json()

        receta = receta_service.crear_receta(
            paciente_id=data['paciente_id'],
            medico_id=medico.id,
            items=data['items'],
            historia_clinica_id=data.get('historia_clinica_id'),
            dias_validez=data.get('dias_validez', 30)
        )

        return jsonify({
            'id': receta.id,
            'codigo_receta': receta.codigo_receta,
            'fecha': receta.fecha.isoformat(),
            'valida_hasta': receta.valida_hasta.isoformat() if receta.valida_hasta else None,
            'mensaje': 'Receta creada exitosamente'
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recetas_bp.route('/<int:id>/cancelar', methods=['PATCH'])
@jwt_required()
def cancelar_receta(id):
    """
    Cancela una receta.

    Permisos: Solo el médico que la creó o admin
    """
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        if user_rol not in ['medico', 'admin']:
            return jsonify({'error': 'No tiene permiso para cancelar recetas'}), 403

        # Si es médico, verificar que sea el que creó la receta
        if user_rol == 'medico':
            medico = Medico.query.filter_by(usuario_id=current_user_id).first()
            if not medico:
                return jsonify({'error': 'Médico no encontrado'}), 404

            # Verificar que la receta fue creada por este médico
            receta_existente = receta_service.get_by_id(id)
            if receta_existente.medico_id != medico.id:
                return jsonify({'error': 'Solo puede cancelar sus propias recetas'}), 403

        data = request.get_json() or {}
        motivo = data.get('motivo')

        receta = receta_service.cancelar_receta(id, motivo)

        return jsonify({
            'id': receta.id,
            'codigo_receta': receta.codigo_receta,
            'estado': receta.estado,
            'mensaje': 'Receta cancelada exitosamente'
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
