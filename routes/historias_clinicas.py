"""
Blueprint de Historias Clínicas
================================

PATRÓN: Facade Pattern
- Endpoints simples que ocultan complejidad del service layer
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from services.historia_clinica_service import HistoriaClinicaService
from models import Paciente, Medico, Usuario

historias_clinicas_bp = Blueprint('historias_clinicas', __name__)

# Service
historia_service = HistoriaClinicaService()


@historias_clinicas_bp.route('', methods=['GET'])
@jwt_required()
def list_historias_clinicas():
    """
    Lista historias clínicas según el rol del usuario.

    - Médicos: historias de sus pacientes
    - Pacientes: solo sus propias historias
    - Admin: todas las historias
    """
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        if user_rol == 'paciente':
            # Paciente solo ve sus propias historias
            paciente = Paciente.query.filter_by(usuario_id=current_user_id).first()
            if not paciente:
                return jsonify({'error': 'Paciente no encontrado'}), 404
            historias = historia_service.obtener_historial_paciente(paciente.id, limit=100)

        elif user_rol == 'medico':
            # Médico ve historias de pacientes que atendió
            medico = Medico.query.filter_by(usuario_id=current_user_id).first()
            if not medico:
                return jsonify({'error': 'Médico no encontrado'}), 404
            historias = historia_service.obtener_historias_medico(medico.id, limit=100)

        elif user_rol in ['admin', 'recepcionista']:
            # Admin/recepcionista ve todas
            historias = historia_service.obtener_todas(limit=100)

        else:
            return jsonify({'error': 'Rol no autorizado'}), 403

        # Serializar
        resultado = []
        for h in historias:
            resultado.append({
                'id': h.id,
                'fecha_consulta': h.fecha_consulta.isoformat(),
                'motivo_consulta': h.motivo_consulta,
                'diagnostico': h.diagnostico,
                'tratamiento': h.tratamiento,
                'observaciones': h.observaciones,
                'paciente': {
                    'id': h.paciente.id,
                    'nombre_completo': h.paciente.nombre_completo,
                    'nro_historia_clinica': h.paciente.nro_historia_clinica
                } if h.paciente else None,
                'medico': {
                    'id': h.medico.id,
                    'nombre_completo': h.medico.nombre_completo
                } if h.medico else None
            })

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@historias_clinicas_bp.route('/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def get_historial_paciente(paciente_id):
    """
    Obtiene historial clínico completo de un paciente.

    Permisos:
    - El mismo paciente
    - Médicos que atendieron al paciente
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
                return jsonify({'error': 'No tiene permiso para ver este historial'}), 403

        elif user_rol not in ['medico', 'admin', 'recepcionista']:
            return jsonify({'error': 'Rol no autorizado'}), 403

        limit = request.args.get('limit', 10, type=int)
        historias = historia_service.obtener_historial_paciente(paciente_id, limit)

        # Serializar
        resultado = []
        for h in historias:
            resultado.append({
                'id': h.id,
                'fecha_consulta': h.fecha_consulta.isoformat(),
                'motivo_consulta': h.motivo_consulta,
                'diagnostico': h.diagnostico,
                'tratamiento': h.tratamiento,
                'observaciones': h.observaciones,
                'medico': {
                    'id': h.medico.id,
                    'nombre_completo': h.medico.nombre_completo
                } if h.medico else None
            })

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@historias_clinicas_bp.route('', methods=['POST'])
@jwt_required()
def create_historia_clinica():
    """
    Crea historia clínica desde un turno completado.

    Permisos: Solo médicos
    """
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        if user_rol != 'medico':
            return jsonify({'error': 'Solo los médicos pueden crear historias clínicas'}), 403

        data = request.get_json()

        historia = historia_service.crear_desde_turno(
            turno_id=data['turno_id'],
            diagnostico=data['diagnostico'],
            tratamiento=data.get('tratamiento'),
            observaciones=data.get('observaciones')
        )

        return jsonify({
            'id': historia.id,
            'turno_id': historia.turno_id,
            'paciente_id': historia.paciente_id,
            'medico_id': historia.medico_id,
            'fecha_consulta': historia.fecha_consulta.isoformat(),
            'diagnostico': historia.diagnostico,
            'mensaje': 'Historia clínica creada exitosamente'
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@historias_clinicas_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_historia_clinica(id):
    """
    Actualiza una historia clínica existente.

    Permisos: SOLO el médico que la creó
    Razón: Editar historias clínicas es un acto médico que requiere matrícula profesional.
    """
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        # SOLO médicos pueden editar historias clínicas
        if user_rol != 'medico':
            return jsonify({'error': 'Solo los médicos pueden actualizar historias clínicas'}), 403

        # Obtener médico actual
        medico = Medico.query.filter_by(usuario_id=current_user_id).first()
        if not medico:
            return jsonify({'error': 'Médico no encontrado'}), 404

        # Verificar que la historia fue creada por este médico
        historia_existente = historia_service.get_by_id(id)
        if historia_existente.medico_id != medico.id:
            return jsonify({'error': 'Solo puede actualizar sus propias historias clínicas'}), 403

        data = request.get_json()

        historia = historia_service.actualizar(
            historia_id=id,
            diagnostico=data.get('diagnostico'),
            tratamiento=data.get('tratamiento'),
            observaciones=data.get('observaciones')
        )

        return jsonify({
            'id': historia.id,
            'diagnostico': historia.diagnostico,
            'tratamiento': historia.tratamiento,
            'observaciones': historia.observaciones,
            'mensaje': 'Historia clínica actualizada exitosamente'
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
