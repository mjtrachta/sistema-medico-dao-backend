from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from models import db, Usuario, Paciente, Medico, InvitacionMedico
from datetime import timedelta, datetime
from utils.auth_decorators import admin_required
import re

auth_bp = Blueprint('auth', __name__)

def validar_email(email):
    """Valida formato de email"""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def validar_password(password):
    """Valida que la contraseña tenga al menos 8 caracteres"""
    return len(password) >= 8

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Registro público de pacientes
    """
    try:
        data = request.get_json()

        # Validaciones
        required_fields = ['nombre_usuario', 'email', 'password', 'nombre', 'apellido',
                          'tipo_documento', 'nro_documento', 'fecha_nacimiento', 'genero']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400

        # Validar email
        if not validar_email(data['email']):
            return jsonify({'error': 'Email inválido'}), 400

        # Validar password
        if not validar_password(data['password']):
            return jsonify({'error': 'La contraseña debe tener al menos 8 caracteres'}), 400

        # Verificar si el usuario ya existe
        if Usuario.query.filter_by(nombre_usuario=data['nombre_usuario']).first():
            return jsonify({'error': 'El nombre de usuario ya está en uso'}), 400

        if Usuario.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'El email ya está registrado'}), 400

        if Paciente.query.filter_by(nro_documento=data['nro_documento']).first():
            return jsonify({'error': 'El número de documento ya está registrado'}), 400

        # Crear usuario con rol paciente
        nuevo_usuario = Usuario(
            nombre_usuario=data['nombre_usuario'],
            email=data['email'],
            rol='paciente'
        )
        nuevo_usuario.set_password(data['password'])

        db.session.add(nuevo_usuario)
        db.session.flush()  # Para obtener el ID del usuario

        # Generar número de historia clínica único
        nro_historia_clinica = f"HC-{nuevo_usuario.id:06d}"

        # Crear paciente
        nuevo_paciente = Paciente(
            usuario_id=nuevo_usuario.id,
            nro_historia_clinica=nro_historia_clinica,
            nombre=data['nombre'],
            apellido=data['apellido'],
            tipo_documento=data['tipo_documento'],
            nro_documento=data['nro_documento'],
            fecha_nacimiento=datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date(),
            genero=data['genero'],
            telefono=data.get('telefono'),
            email=data['email']
        )

        db.session.add(nuevo_paciente)
        db.session.commit()

        # Crear tokens (PyJWT 2.10+ requiere subject como string)
        access_token = create_access_token(
            identity=str(nuevo_usuario.id),
            additional_claims={'rol': nuevo_usuario.rol},
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            identity=str(nuevo_usuario.id),
            expires_delta=timedelta(days=30)
        )

        return jsonify({
            'message': 'Paciente registrado exitosamente',
            'usuario': nuevo_usuario.to_dict(),
            'paciente_id': nuevo_paciente.id,
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login con usuario/email y contraseña
    Devuelve JWT tokens
    """
    import logging
    try:
        print("=" * 60)
        print("DEBUG LOGIN: INICIO")
        print("=" * 60)

        print("DEBUG LOGIN: 1. Obteniendo datos del request...")
        data = request.get_json()
        print(f"DEBUG LOGIN:    username={data.get('username') if data else None}")

        if not data or not data.get('username') or not data.get('password'):
            print("DEBUG LOGIN:    ERROR - Faltan credenciales")
            return jsonify({'error': 'Usuario y contraseña requeridos'}), 400

        print("DEBUG LOGIN: 2. Buscando usuario en BD...")
        # Buscar por nombre de usuario o email
        usuario = Usuario.query.filter(
            (Usuario.nombre_usuario == data['username']) |
            (Usuario.email == data['username'])
        ).first()

        if not usuario:
            print(f"DEBUG LOGIN:    ERROR - Usuario no encontrado: {data['username']}")
            return jsonify({'error': 'Credenciales inválidas'}), 401

        print(f"DEBUG LOGIN:    Usuario encontrado: {usuario.nombre_usuario}")
        print(f"DEBUG LOGIN:    Hash type: {type(usuario.hash_contrasena)}")
        print(f"DEBUG LOGIN:    Hash length: {len(usuario.hash_contrasena) if usuario.hash_contrasena else 0}")
        if usuario.hash_contrasena:
            print(f"DEBUG LOGIN:    Hash preview: {repr(usuario.hash_contrasena[:50])}")

        # Verificar contraseña con mejor manejo de errores
        print("DEBUG LOGIN: 3. Verificando contraseña...")
        try:
            password_valida = usuario.check_password(data['password'])
            print(f"DEBUG LOGIN:    Verificación OK: {password_valida}")
        except UnicodeDecodeError as e:
            # Error específico de codificación UTF-8
            print(f"DEBUG LOGIN:    ERROR UTF-8 en check_password: {e}")
            logging.error(f"   ERROR UTF-8 al verificar contraseña para usuario {usuario.nombre_usuario}: {e}")
            logging.error(f"   Hash preview: {repr(usuario.hash_contrasena[:50]) if usuario.hash_contrasena else 'None'}")
            return jsonify({
                'error': 'Error en la verificación de credenciales. Contacte al administrador.',
                'detail': 'Password hash encoding error'
            }), 500
        except Exception as e:
            # Otros errores en la verificación de contraseña
            print(f"DEBUG LOGIN:    ERROR en check_password: {e}")
            logging.error(f"   ERROR al verificar contraseña para usuario {usuario.nombre_usuario}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return jsonify({'error': 'Error en la verificación de credenciales'}), 500

        if not password_valida:
            return jsonify({'error': 'Credenciales inválidas'}), 401

        if not usuario.activo:
            return jsonify({'error': 'Usuario inactivo'}), 403

        import logging
        logging.info(f"Login: Contraseña verificada OK para {usuario.nombre_usuario}")

        # Crear tokens con claims adicionales (PyJWT 2.10+ requiere subject como string)
        try:
            logging.info(f"Login: Creando access token...")
            access_token = create_access_token(
                identity=str(usuario.id),
                additional_claims={'rol': usuario.rol},
                expires_delta=timedelta(hours=1)
            )
            logging.info(f"Login: Access token creado OK")

            logging.info(f"Login: Creando refresh token...")
            refresh_token = create_refresh_token(
                identity=str(usuario.id),
                expires_delta=timedelta(days=30)
            )
            logging.info(f"Login: Refresh token creado OK")
        except Exception as e:
            logging.error(f"Login: Error creando tokens: {e}")
            raise

        # Obtener datos adicionales según el rol
        datos_adicionales = {}
        try:
            logging.info(f"Login: Obteniendo datos adicionales para rol {usuario.rol}...")
            if usuario.rol == 'paciente':
                paciente = Paciente.query.filter_by(usuario_id=usuario.id).first()
                if paciente:
                    datos_adicionales['paciente_id'] = paciente.id
                    datos_adicionales['nro_historia_clinica'] = paciente.nro_historia_clinica

            elif usuario.rol == 'medico':
                medico = Medico.query.filter_by(usuario_id=usuario.id).first()
                if medico:
                    datos_adicionales['medico_id'] = medico.id
                    datos_adicionales['matricula'] = medico.matricula
            logging.info(f"Login: Datos adicionales obtenidos OK")
        except Exception as e:
            logging.error(f"Login: Error obteniendo datos adicionales: {e}")
            raise

        try:
            logging.info(f"Login: Serializando usuario a dict...")
            usuario_dict = usuario.to_dict()
            logging.info(f"Login: Usuario serializado OK")

            logging.info(f"Login: Creando respuesta JSON...")
            response = jsonify({
                'message': 'Login exitoso',
                'usuario': usuario_dict,
                'access_token': access_token,
                'refresh_token': refresh_token,
                **datos_adicionales
            })
            logging.info(f"Login: Respuesta creada exitosamente")
            return response, 200
        except Exception as e:
            logging.error(f"Login: Error en serialización final: {e}")
            raise

    except UnicodeDecodeError as e:
        # Error de codificación en otra parte del proceso
        import logging
        logging.error(f"Error UTF-8 en login: {e}")
        return jsonify({
            'error': 'Error de codificación. Contacte al administrador.',
            'detail': str(e)
        }), 500
    except Exception as e:
        import logging
        logging.error(f"Error en login: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Renueva el access token usando el refresh token
    """
    try:
        # PyJWT 2.10+ devuelve subject como string, convertir a int
        current_user_id = int(get_jwt_identity())
        usuario = Usuario.query.get(current_user_id)

        if not usuario or not usuario.activo:
            return jsonify({'error': 'Usuario no válido'}), 401

        # Crear nuevo access token (PyJWT 2.10+ requiere subject como string)
        access_token = create_access_token(
            identity=str(usuario.id),
            additional_claims={'rol': usuario.rol},
            expires_delta=timedelta(hours=1)
        )

        return jsonify({
            'access_token': access_token
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_info():
    """
    Obtiene información del usuario actual
    """
    try:
        # PyJWT 2.10+ devuelve subject como string, convertir a int
        current_user_id = int(get_jwt_identity())
        usuario = Usuario.query.get(current_user_id)

        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        datos_usuario = usuario.to_dict()

        # Agregar datos adicionales según el rol
        if usuario.rol == 'paciente':
            paciente = Paciente.query.filter_by(usuario_id=usuario.id).first()
            if paciente:
                datos_usuario['paciente_id'] = paciente.id
                datos_usuario['nro_historia_clinica'] = paciente.nro_historia_clinica
                datos_usuario['nombre_completo'] = paciente.nombre_completo

        elif usuario.rol == 'medico':
            medico = Medico.query.filter_by(usuario_id=usuario.id).first()
            if medico:
                datos_usuario['medico_id'] = medico.id
                datos_usuario['matricula'] = medico.matricula
                datos_usuario['nombre_completo'] = medico.nombre_completo
                if medico.especialidad:
                    datos_usuario['especialidad'] = {
                        'id': medico.especialidad.id,
                        'nombre': medico.especialidad.nombre
                    }

        return jsonify(datos_usuario), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/invite-medico', methods=['POST'])
@jwt_required()
@admin_required
def invite_medico():
    """
    Admin invita a un médico enviando email con token de registro
    """
    try:
        data = request.get_json()

        if not data or not data.get('email'):
            return jsonify({'error': 'Email requerido'}), 400

        if not validar_email(data['email']):
            return jsonify({'error': 'Email inválido'}), 400

        # Verificar si el email ya está registrado
        if Usuario.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'El email ya está registrado'}), 400

        # Verificar si ya existe una invitación válida para este email
        invitacion_existente = InvitacionMedico.query.filter_by(
            email=data['email'],
            usado=False
        ).filter(
            InvitacionMedico.fecha_expiracion > datetime.utcnow()
        ).first()

        if invitacion_existente:
            return jsonify({
                'message': 'Ya existe una invitación válida para este email',
                'invitacion': invitacion_existente.to_dict()
            }), 200

        # Crear invitación (PyJWT 2.10+ devuelve subject como string)
        current_user_id = int(get_jwt_identity())
        dias_validos = data.get('dias_validos', 7)

        invitacion = InvitacionMedico.crear_invitacion(
            email=data['email'],
            creado_por_usuario_id=current_user_id,
            dias_validos=dias_validos
        )

        db.session.add(invitacion)
        db.session.commit()

        # TODO: Enviar email con el link de registro
        # Por ahora solo devolvemos el token
        registro_url = f"{request.host_url}register/medico?token={invitacion.token}"

        return jsonify({
            'message': 'Invitación creada exitosamente',
            'invitacion': invitacion.to_dict(),
            'registro_url': registro_url
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/register-medico', methods=['POST'])
def register_medico():
    """
    Registro de médico con token de invitación
    """
    try:
        data = request.get_json()

        # Validaciones
        required_fields = ['token', 'nombre_usuario', 'password', 'nombre', 'apellido',
                          'matricula', 'especialidad_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400

        # Verificar token de invitación
        invitacion = InvitacionMedico.query.filter_by(token=data['token']).first()

        if not invitacion:
            return jsonify({'error': 'Token de invitación inválido'}), 404

        if not invitacion.is_valida():
            return jsonify({'error': 'El token de invitación ha expirado o ya fue usado'}), 400

        # Validar password
        if not validar_password(data['password']):
            return jsonify({'error': 'La contraseña debe tener al menos 8 caracteres'}), 400

        # Verificar si el usuario ya existe
        if Usuario.query.filter_by(nombre_usuario=data['nombre_usuario']).first():
            return jsonify({'error': 'El nombre de usuario ya está en uso'}), 400

        if Medico.query.filter_by(matricula=data['matricula']).first():
            return jsonify({'error': 'La matrícula ya está registrada'}), 400

        # Crear usuario con rol medico
        nuevo_usuario = Usuario(
            nombre_usuario=data['nombre_usuario'],
            email=invitacion.email,
            rol='medico'
        )
        nuevo_usuario.set_password(data['password'])

        db.session.add(nuevo_usuario)
        db.session.flush()

        # Crear médico
        nuevo_medico = Medico(
            usuario_id=nuevo_usuario.id,
            nombre=data['nombre'],
            apellido=data['apellido'],
            matricula=data['matricula'],
            especialidad_id=data['especialidad_id'],
            telefono=data.get('telefono'),
            email=invitacion.email
        )

        db.session.add(nuevo_medico)

        # Marcar invitación como usada
        invitacion.marcar_como_usada()

        db.session.commit()

        # Crear tokens (PyJWT 2.10+ requiere subject como string)
        access_token = create_access_token(
            identity=str(nuevo_usuario.id),
            additional_claims={'rol': nuevo_usuario.rol},
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            identity=str(nuevo_usuario.id),
            expires_delta=timedelta(days=30)
        )

        return jsonify({
            'message': 'Médico registrado exitosamente',
            'usuario': nuevo_usuario.to_dict(),
            'medico_id': nuevo_medico.id,
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify-token/<token>', methods=['GET'])
def verify_invite_token(token):
    """
    Verifica si un token de invitación es válido
    """
    try:
        invitacion = InvitacionMedico.query.filter_by(token=token).first()

        if not invitacion:
            return jsonify({'valido': False, 'error': 'Token no encontrado'}), 404

        if not invitacion.is_valida():
            return jsonify({
                'valido': False,
                'error': 'Token expirado o ya usado',
                'usado': invitacion.usado,
                'fecha_expiracion': invitacion.fecha_expiracion.isoformat()
            }), 400

        return jsonify({
            'valido': True,
            'email': invitacion.email,
            'fecha_expiracion': invitacion.fecha_expiracion.isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
