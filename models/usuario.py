from .database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nombre_usuario = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    hash_contrasena = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default='paciente', nullable=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    medicos = db.relationship('Medico', back_populates='usuario', lazy='dynamic')
    pacientes = db.relationship('Paciente', back_populates='usuario', lazy='dynamic')

    def set_password(self, password):
        """Establece la contraseña hasheada"""
        self.hash_contrasena = generate_password_hash(password)

    def check_password(self, password):
        """Verifica si la contraseña es correcta"""
        # Asegurar que el hash es string (no bytes)
        hash_val = self.hash_contrasena
        if isinstance(hash_val, bytes):
            try:
                hash_val = hash_val.decode('utf-8')
            except UnicodeDecodeError:
                # Si no se puede decodificar, el hash está corrupto
                import logging
                logging.error(f"Hash corrupto para usuario {self.nombre_usuario}: no puede decodificarse como UTF-8")
                raise

        return check_password_hash(hash_val, password)

    def has_role(self, *roles):
        """Verifica si el usuario tiene alguno de los roles especificados"""
        return self.rol in roles

    def is_admin(self):
        """Verifica si el usuario es administrador"""
        return self.rol == 'admin'

    def is_medico(self):
        """Verifica si el usuario es médico"""
        return self.rol == 'medico'

    def is_paciente(self):
        """Verifica si el usuario es paciente"""
        return self.rol == 'paciente'

    def to_dict(self):
        """Convierte el usuario a diccionario (sin hash de contraseña)"""
        return {
            'id': self.id,
            'nombre_usuario': self.nombre_usuario,
            'email': self.email,
            'rol': self.rol,
            'activo': self.activo,
            'creado_en': self.creado_en.isoformat() if self.creado_en else None
        }

    def __repr__(self):
        return f'<Usuario {self.nombre_usuario} ({self.rol})>'
