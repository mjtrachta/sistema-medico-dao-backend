from .database import db
from datetime import datetime

class Turno(db.Model):
    __tablename__ = 'turnos'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    codigo_turno = db.Column(db.String(50), unique=True, nullable=False)
    paciente_id = db.Column(db.BigInteger, db.ForeignKey('pacientes.id', ondelete='RESTRICT'), nullable=False)
    medico_id = db.Column(db.BigInteger, db.ForeignKey('medicos.id', ondelete='RESTRICT'), nullable=False)
    ubicacion_id = db.Column(db.Integer, db.ForeignKey('ubicaciones.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    duracion_min = db.Column(db.SmallInteger, default=30)
    estado = db.Column(db.String(20), nullable=False, default='pendiente')
    motivo_consulta = db.Column(db.Text)
    creado_por_usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    paciente = db.relationship('Paciente', back_populates='turnos')
    medico = db.relationship('Medico', back_populates='turnos')
    ubicacion = db.relationship('Ubicacion', back_populates='turnos')
    historia_clinica = db.relationship('HistoriaClinica', back_populates='turno', uselist=False)
    notificaciones = db.relationship('Notificacion', back_populates='turno', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Turno {self.codigo_turno} - {self.fecha} {self.hora}>'
