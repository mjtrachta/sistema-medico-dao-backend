"""
Blueprint de Especialidades - Endpoints CRUD básicos
"""

from flask import Blueprint, request, jsonify
from models import Especialidad
from repositories.base_repository import BaseRepository
from schemas.especialidad_schema import especialidad_schema, especialidades_schema

especialidades_bp = Blueprint('especialidades', __name__)

# Repository
especialidad_repository = BaseRepository(Especialidad)


@especialidades_bp.route('', methods=['GET'])
def list_especialidades():
    """Lista todas las especialidades."""
    try:
        especialidades = especialidad_repository.find_all(filters={'activo': True})
        return jsonify(especialidades_schema.dump(especialidades)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@especialidades_bp.route('/<int:id>', methods=['GET'])
def get_especialidad(id):
    """Obtiene una especialidad por ID."""
    try:
        especialidad = especialidad_repository.find_by_id(id)
        if not especialidad:
            return jsonify({'error': 'Especialidad no encontrada'}), 404
        return jsonify(especialidad_schema.dump(especialidad)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@especialidades_bp.route('', methods=['POST'])
def create_especialidad():
    """Crea una nueva especialidad."""
    try:
        data = request.get_json()
        especialidad = Especialidad(
            nombre=data['nombre'],
            descripcion=data.get('descripcion'),
            duracion_turno_min=data.get('duracion_turno_min', 30)
        )
        especialidad = especialidad_repository.create(especialidad)
        return jsonify(especialidad_schema.dump(especialidad)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
