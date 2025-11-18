def register_blueprints(app):
    """Registra todos los blueprints de la aplicación"""
    from .auth import auth_bp
    from .especialidades import especialidades_bp
    from .pacientes import pacientes_bp
    from .medicos import medicos_bp
    from .ubicaciones import ubicaciones_bp
    from .turnos import turnos_bp
    from .historias_clinicas import historias_clinicas_bp
    from .recetas import recetas_bp
    from .horarios import horarios_bp
    from .reportes import reportes_bp
    from .testing import testing_bp  # Endpoint para testing

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(especialidades_bp, url_prefix='/api/especialidades')
    app.register_blueprint(pacientes_bp, url_prefix='/api/pacientes')
    app.register_blueprint(medicos_bp, url_prefix='/api/medicos')
    app.register_blueprint(ubicaciones_bp, url_prefix='/api/ubicaciones')
    app.register_blueprint(turnos_bp, url_prefix='/api/turnos')
    app.register_blueprint(historias_clinicas_bp, url_prefix='/api/historias-clinicas')
    app.register_blueprint(recetas_bp, url_prefix='/api/recetas')
    app.register_blueprint(horarios_bp, url_prefix='/api/horarios')
    app.register_blueprint(reportes_bp, url_prefix='/api/reportes')
    app.register_blueprint(testing_bp)  # Solo para desarrollo
