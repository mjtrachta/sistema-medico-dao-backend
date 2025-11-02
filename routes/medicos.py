"""
Blueprint de Médicos - Endpoints CRUD básicos
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models import Medico
from repositories.base_repository import BaseRepository
from schemas.medico_schema import medico_schema, medicos_schema
from services.horario_medico_service import HorarioMedicoService

medicos_bp = Blueprint('medicos', __name__)

# Repository
medico_repository = BaseRepository(Medico)

# Service
horario_service = HorarioMedicoService()


@medicos_bp.route('', methods=['GET'])
def list_medicos():
    """Lista todos los médicos activos."""
    try:
        medicos = medico_repository.find_all(filters={'activo': True})
        return jsonify(medicos_schema.dump(medicos)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@medicos_bp.route('/<int:id>', methods=['GET'])
def get_medico(id):
    """Obtiene un médico por ID."""
    try:
        medico = medico_repository.find_by_id(id)
        if not medico:
            return jsonify({'error': 'Médico no encontrado'}), 404
        return jsonify(medico_schema.dump(medico)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@medicos_bp.route('', methods=['POST'])
def create_medico():
    """Crea un nuevo médico."""
    try:
        data = request.get_json()
        medico = Medico(
            nombre=data['nombre'],
            apellido=data['apellido'],
            matricula=data['matricula'],
            especialidad_id=data.get('especialidad_id'),
            telefono=data.get('telefono'),
            email=data.get('email')
        )
        medico = medico_repository.create(medico)
        return jsonify(medico_schema.dump(medico)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@medicos_bp.route('/<int:id>', methods=['PUT'])
def update_medico(id):
    """
    Actualiza un médico existente.

    PATRÓN: Repository Pattern
    """
    try:
        medico = medico_repository.find_by_id(id)
        if not medico:
            return jsonify({'error': 'Médico no encontrado'}), 404

        data = request.get_json()

        # Actualizar campos
        if 'nombre' in data:
            medico.nombre = data['nombre']
        if 'apellido' in data:
            medico.apellido = data['apellido']
        if 'matricula' in data:
            medico.matricula = data['matricula']
        if 'especialidad_id' in data:
            medico.especialidad_id = data['especialidad_id']
        if 'telefono' in data:
            medico.telefono = data['telefono']
        if 'email' in data:
            medico.email = data['email']

        medico = medico_repository.update(medico)
        return jsonify(medico_schema.dump(medico)), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@medicos_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_medico(id):
    """
    Desactiva un médico (soft delete).

    Permisos: Solo admin

    IMPORTANTE: Al desactivar un médico:
    1. El médico se marca como inactivo (activo=False)
    2. Todos sus horarios se desactivan automáticamente
    3. Las historias clínicas y recetas SE PRESERVAN (datos del paciente no se pierden)
    4. Los turnos existentes no se modifican (mantienen el médico_id)

    PATRÓN: Repository Pattern + Service Layer
    """
    try:
        claims = get_jwt()
        user_rol = claims.get('rol')

        if user_rol != 'admin':
            return jsonify({'error': 'Solo el admin puede desactivar médicos'}), 403

        medico = medico_repository.find_by_id(id)
        if not medico:
            return jsonify({'error': 'Médico no encontrado'}), 404

        # Soft delete del médico
        medico.activo = False
        medico_repository.update(medico)

        # Desactivar todos los horarios del médico
        horarios_desactivados = horario_service.desactivar_todos_medico(id)

        return jsonify({
            'message': 'Médico desactivado exitosamente',
            'medico_id': id,
            'horarios_desactivados': horarios_desactivados,
            'nota': 'Las historias clínicas y recetas del médico se han preservado'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
