from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from models import Usuario

def roles_required(*roles):
    """
    Decorador que verifica si el usuario tiene alguno de los roles especificados

    Uso:
        @roles_required('admin', 'medico')
        def mi_funcion():
            pass
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('rol')

            if user_role not in roles:
                return jsonify({
                    'error': 'No tiene permisos para realizar esta acción',
                    'rol_requerido': list(roles),
                    'rol_actual': user_role
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(fn):
    """
    Decorador que verifica si el usuario es administrador
    """
    return roles_required('admin')(fn)

def medico_required(fn):
    """
    Decorador que verifica si el usuario es médico
    """
    return roles_required('medico')(fn)

def admin_or_medico_required(fn):
    """
    Decorador que verifica si el usuario es admin o médico
    """
    return roles_required('admin', 'medico')(fn)

def get_current_user():
    """
    Obtiene el usuario actual desde el token JWT

    Returns:
        Usuario o None
    """
    try:
        verify_jwt_in_request()
        # PyJWT 2.10+ devuelve subject como string, convertir a int
        user_id = int(get_jwt_identity())
        return Usuario.query.get(user_id)
    except:
        return None

def get_current_user_id():
    """
    Obtiene el ID del usuario actual desde el token JWT

    Returns:
        int o None
    """
    try:
        verify_jwt_in_request()
        # PyJWT 2.10+ devuelve subject como string, convertir a int
        return int(get_jwt_identity())
    except:
        return None

def owns_resource(resource_user_id_attr='usuario_id'):
    """
    Decorador que verifica si el usuario es dueño del recurso o es admin

    Uso:
        @owns_resource('paciente_id')
        def ver_datos_paciente(paciente_id):
            pass
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            current_user = get_current_user()

            if current_user.is_admin():
                # Admin puede acceder a todo
                return fn(*args, **kwargs)

            # Obtener el ID del recurso de los kwargs
            resource_user_id = kwargs.get(resource_user_id_attr)

            if not resource_user_id:
                return jsonify({'error': 'Recurso no encontrado'}), 404

            if current_user.id != resource_user_id:
                return jsonify({'error': 'No tiene permisos para acceder a este recurso'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator
