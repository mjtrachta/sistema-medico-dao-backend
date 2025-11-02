"""
Blueprint de Pacientes - Endpoints CRUD
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from models import Paciente, Medico
from repositories.paciente_repository import PacienteRepository
from schemas.paciente_schema import paciente_schema, pacientes_schema

pacientes_bp = Blueprint('pacientes', __name__)

# Repository
paciente_repository = PacienteRepository()


@pacientes_bp.route('', methods=['GET'])
def list_pacientes():
    """Lista todos los pacientes activos."""
    try:
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)

        pacientes = paciente_repository.find_activos(limit=limit, offset=offset)
        return jsonify(pacientes_schema.dump(pacientes)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pacientes_bp.route('/<int:id>', methods=['GET'])
def get_paciente(id):
    """Obtiene un paciente por ID."""
    try:
        paciente = paciente_repository.find_by_id(id)
        if not paciente:
            return jsonify({'error': 'Paciente no encontrado'}), 404
        return jsonify(paciente_schema.dump(paciente)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pacientes_bp.route('', methods=['POST'])
def create_paciente():
    """Crea un nuevo paciente."""
    try:
        data = request.get_json()

        paciente = Paciente(
            nombre=data['nombre'],
            apellido=data['apellido'],
            tipo_documento=data['tipo_documento'],
            nro_documento=data['nro_documento'],
            fecha_nacimiento=datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date(),
            genero=data.get('genero'),
            telefono=data.get('telefono'),
            email=data.get('email'),
            nro_historia_clinica=data.get('nro_historia_clinica')
        )

        paciente = paciente_repository.create(paciente)
        return jsonify(paciente_schema.dump(paciente)), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pacientes_bp.route('/<int:id>', methods=['PUT'])
def update_paciente(id):
    """
    Actualiza un paciente existente.

    PATRÓN: Repository Pattern
    - Actualización encapsulada en repository
    """
    try:
        paciente = paciente_repository.find_by_id(id)
        if not paciente:
            return jsonify({'error': 'Paciente no encontrado'}), 404

        data = request.get_json()

        # Actualizar campos
        if 'nombre' in data:
            paciente.nombre = data['nombre']
        if 'apellido' in data:
            paciente.apellido = data['apellido']
        if 'tipo_documento' in data:
            paciente.tipo_documento = data['tipo_documento']
        if 'nro_documento' in data:
            paciente.nro_documento = data['nro_documento']
        if 'fecha_nacimiento' in data:
            paciente.fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
        if 'genero' in data:
            paciente.genero = data['genero']
        if 'telefono' in data:
            paciente.telefono = data['telefono']
        if 'email' in data:
            paciente.email = data['email']

        paciente = paciente_repository.update(paciente)
        return jsonify(paciente_schema.dump(paciente)), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pacientes_bp.route('/<int:id>', methods=['DELETE'])
def delete_paciente(id):
    """
    Desactiva un paciente (soft delete).

    PATRÓN: Repository Pattern
    - No se elimina físicamente, solo se marca como inactivo
    """
    try:
        paciente = paciente_repository.find_by_id(id)
        if not paciente:
            return jsonify({'error': 'Paciente no encontrado'}), 404

        # Soft delete
        paciente.activo = False
        paciente_repository.update(paciente)

        return jsonify({'message': 'Paciente desactivado exitosamente'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pacientes_bp.route('/buscar', methods=['GET'])
def search_pacientes():
    """Busca pacientes por nombre/apellido."""
    try:
        nombre = request.args.get('nombre', '')
        apellido = request.args.get('apellido', '')

        pacientes = paciente_repository.search_by_nombre(nombre, apellido)
        return jsonify(pacientes_schema.dump(pacientes)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pacientes_bp.route('/mis-pacientes', methods=['GET'])
@jwt_required()
def get_mis_pacientes():
    """
    Obtiene la lista de pacientes únicos atendidos por el médico.

    Permisos: Solo médicos
    Query params:
        - search: Término de búsqueda (nombre, apellido, documento, historia clínica)
    """
    try:
        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_rol = claims.get('rol')

        if user_rol != 'medico':
            return jsonify({'error': 'Solo los médicos pueden acceder a esta vista'}), 403

        # Obtener ID del médico
        medico = Medico.query.filter_by(usuario_id=current_user_id).first()
        if not medico:
            return jsonify({'error': 'Médico no encontrado'}), 404

        # Obtener término de búsqueda opcional
        search = request.args.get('search', '')

        # Obtener pacientes del médico
        pacientes = paciente_repository.find_pacientes_by_medico(
            medico_id=medico.id,
            search=search if search else None
        )

        return jsonify(pacientes_schema.dump(pacientes)), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
