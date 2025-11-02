"""
Blueprint de Ubicaciones
========================

PATRÓN: Facade Pattern

PERMISOS:
- GET: Todos los usuarios autenticados (necesitan ver ubicaciones para sacar turnos)
- POST/PUT/DELETE: Solo admin
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from services.ubicacion_service import UbicacionService

ubicaciones_bp = Blueprint('ubicaciones', __name__)

# Service
ubicacion_service = UbicacionService()


@ubicaciones_bp.route('', methods=['GET'])
@jwt_required()
def list_ubicaciones():
    """
    Lista todas las ubicaciones activas.

    Accesible por todos los usuarios autenticados.
    Necesario para que pacientes puedan seleccionar ubicación al sacar turno.

    Query params:
        - buscar: término de búsqueda por nombre
        - ciudad: filtrar por ciudad
    """
    try:
        buscar = request.args.get('buscar')
        ciudad = request.args.get('ciudad')

        if buscar:
            ubicaciones = ubicacion_service.buscar_por_nombre(buscar)
        elif ciudad:
            ubicaciones = ubicacion_service.buscar_por_ciudad(ciudad)
        else:
            ubicaciones = ubicacion_service.obtener_todas_activas()

        # Serializar
        resultado = []
        for u in ubicaciones:
            resultado.append({
                'id': u.id,
                'nombre': u.nombre,
                'direccion': u.direccion,
                'ciudad': u.ciudad,
                'telefono': u.telefono,
                'activo': u.activo
            })

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ubicaciones_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_ubicacion(id):
    """
    Obtiene una ubicación por ID.

    Accesible por todos los usuarios autenticados.
    """
    try:
        ubicacion = ubicacion_service.obtener_por_id(id)

        return jsonify({
            'id': ubicacion.id,
            'nombre': ubicacion.nombre,
            'direccion': ubicacion.direccion,
            'ciudad': ubicacion.ciudad,
            'telefono': ubicacion.telefono,
            'activo': ubicacion.activo
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ubicaciones_bp.route('', methods=['POST'])
@jwt_required()
def create_ubicacion():
    """
    Crea una nueva ubicación.

    Permisos: Solo admin

    Body:
        - nombre: nombre de la ubicación (requerido)
        - direccion: dirección física (requerido)
        - ciudad: ciudad (requerido)
        - telefono: teléfono de contacto (opcional)
    """
    try:
        claims = get_jwt()
        user_rol = claims.get('rol')

        if user_rol != 'admin':
            return jsonify({'error': 'Solo el admin puede crear ubicaciones'}), 403

        data = request.get_json()

        # Validar datos requeridos
        if not data.get('nombre'):
            return jsonify({'error': 'nombre es requerido'}), 400
        if not data.get('direccion'):
            return jsonify({'error': 'direccion es requerida'}), 400
        if not data.get('ciudad'):
            return jsonify({'error': 'ciudad es requerida'}), 400

        ubicacion = ubicacion_service.crear_ubicacion(
            nombre=data['nombre'],
            direccion=data['direccion'],
            ciudad=data['ciudad'],
            telefono=data.get('telefono')
        )

        return jsonify({
            'id': ubicacion.id,
            'nombre': ubicacion.nombre,
            'direccion': ubicacion.direccion,
            'ciudad': ubicacion.ciudad,
            'telefono': ubicacion.telefono,
            'mensaje': 'Ubicación creada exitosamente'
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ubicaciones_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_ubicacion(id):
    """
    Actualiza una ubicación existente.

    Permisos: Solo admin

    Body (todos opcionales):
        - nombre: nuevo nombre
        - direccion: nueva dirección
        - ciudad: nueva ciudad
        - telefono: nuevo teléfono
    """
    try:
        claims = get_jwt()
        user_rol = claims.get('rol')

        if user_rol != 'admin':
            return jsonify({'error': 'Solo el admin puede actualizar ubicaciones'}), 403

        data = request.get_json()

        ubicacion = ubicacion_service.actualizar_ubicacion(
            ubicacion_id=id,
            nombre=data.get('nombre'),
            direccion=data.get('direccion'),
            ciudad=data.get('ciudad'),
            telefono=data.get('telefono')
        )

        return jsonify({
            'id': ubicacion.id,
            'nombre': ubicacion.nombre,
            'direccion': ubicacion.direccion,
            'ciudad': ubicacion.ciudad,
            'telefono': ubicacion.telefono,
            'mensaje': 'Ubicación actualizada exitosamente'
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ubicaciones_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_ubicacion(id):
    """
    Desactiva una ubicación (soft delete).

    Permisos: Solo admin

    IMPORTANTE: Los horarios asociados NO se desactivan automáticamente.
    El admin debe gestionar los horarios por separado.
    """
    try:
        claims = get_jwt()
        user_rol = claims.get('rol')

        if user_rol != 'admin':
            return jsonify({'error': 'Solo el admin puede eliminar ubicaciones'}), 403

        ubicacion = ubicacion_service.desactivar_ubicacion(id)

        return jsonify({
            'id': ubicacion.id,
            'mensaje': 'Ubicación desactivada exitosamente'
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ubicaciones_bp.route('/<int:id>/reactivar', methods=['PUT'])
@jwt_required()
def reactivar_ubicacion(id):
    """
    Reactiva una ubicación previamente desactivada.

    Permisos: Solo admin
    """
    try:
        claims = get_jwt()
        user_rol = claims.get('rol')

        if user_rol != 'admin':
            return jsonify({'error': 'Solo el admin puede reactivar ubicaciones'}), 403

        ubicacion = ubicacion_service.reactivar_ubicacion(id)

        return jsonify({
            'id': ubicacion.id,
            'nombre': ubicacion.nombre,
            'mensaje': 'Ubicación reactivada exitosamente'
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
