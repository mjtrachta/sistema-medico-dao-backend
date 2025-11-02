from .database import db
from datetime import datetime

class Notificacion(db.Model):
    __tablename__ = 'notificaciones'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    turno_id = db.Column(db.BigInteger, db.ForeignKey('turnos.id', ondelete='CASCADE'))
    tipo = db.Column(db.String(20))  # email, sms, sistema
    destinatario = db.Column(db.String(255), nullable=False)
    mensaje = db.Column(db.Text)
    enviado_en = db.Column(db.DateTime)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, enviado, fallido
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    turno = db.relationship('Turno', back_populates='notificaciones')

    def __repr__(self):
        return f'<Notificacion {self.tipo} - {self.estado}>'
