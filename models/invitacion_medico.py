from .database import db
from datetime import datetime, timedelta
import secrets

class InvitacionMedico(db.Model):
    __tablename__ = 'invitaciones_medico'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    usado = db.Column(db.Boolean, default=False)
    fecha_expiracion = db.Column(db.DateTime, nullable=False)
    creado_por_usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación
    creado_por = db.relationship('Usuario', foreign_keys=[creado_por_usuario_id])

    @staticmethod
    def generar_token():
        """Genera un token único y seguro"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def crear_invitacion(email, creado_por_usuario_id, dias_validos=7):
        """Crea una nueva invitación con token y fecha de expiración"""
        token = InvitacionMedico.generar_token()
        fecha_expiracion = datetime.utcnow() + timedelta(days=dias_validos)

        invitacion = InvitacionMedico(
            email=email,
            token=token,
            fecha_expiracion=fecha_expiracion,
            creado_por_usuario_id=creado_por_usuario_id
        )
        return invitacion

    def is_valida(self):
        """Verifica si la invitación es válida (no usada y no expirada)"""
        if self.usado:
            return False
        if datetime.utcnow() > self.fecha_expiracion:
            return False
        return True

    def marcar_como_usada(self):
        """Marca la invitación como usada"""
        self.usado = True

    def to_dict(self):
        """Convierte la invitación a diccionario"""
        return {
            'id': self.id,
            'email': self.email,
            'token': self.token,
            'usado': self.usado,
            'fecha_expiracion': self.fecha_expiracion.isoformat() if self.fecha_expiracion else None,
            'creado_por_usuario_id': self.creado_por_usuario_id,
            'creado_en': self.creado_en.isoformat() if self.creado_en else None
        }

    def __repr__(self):
        return f'<InvitacionMedico {self.email} - Usado: {self.usado}>'
