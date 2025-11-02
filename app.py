from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config.config import config
from models import init_db, db
from schemas import init_ma
import os

def create_app(config_name='development'):
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)

    # Cargar configuración
    app.config.from_object(config[config_name])

    # Configurar CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:4200"],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Inicializar JWT
    jwt = JWTManager(app)

    # Configurar callbacks JWT
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token expirado',
            'message': 'El token de autenticación ha expirado'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Token inválido',
            'message': 'La firma del token es inválida'
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Token faltante',
            'message': 'Se requiere autenticación para acceder a este recurso'
        }), 401

    # Inicializar base de datos
    init_db(app)

    # Inicializar Marshmallow
    init_ma(app)

    # Registrar blueprints
    from routes import register_blueprints
    register_blueprints(app)

    # Ruta de salud básica
    @app.route('/api/health', methods=['GET'])
    def health():
        try:
            # Verificar conexión a la base de datos
            db.session.execute(db.text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'

        return jsonify({
            'status': 'ok',
            'message': 'Sistema de Turnos Médicos - API funcionando',
            'database': db_status
        })

    # Manejador de errores
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Recurso no encontrado'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

    return app

if __name__ == '__main__':
    env = os.getenv('FLASK_ENV', 'development')
    app = create_app(env)
    # use_reloader=False para evitar que los tokens JWT se invaliden con cada reload
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
