from .database import db
from datetime import datetime

class Ubicacion(db.Model):
    __tablename__ = 'ubicaciones'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(200), nullable=False)
    direccion = db.Column(db.String(255))
    ciudad = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    horarios = db.relationship('HorarioMedico', back_populates='ubicacion', lazy='dynamic')
    turnos = db.relationship('Turno', back_populates='ubicacion', lazy='dynamic')

    def __repr__(self):
        return f'<Ubicacion {self.nombre}>'


class HorarioMedico(db.Model):
    __tablename__ = 'horarios_medico'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    medico_id = db.Column(db.BigInteger, db.ForeignKey('medicos.id', ondelete='CASCADE'), nullable=False)
    ubicacion_id = db.Column(db.Integer, db.ForeignKey('ubicaciones.id'))
    dia_semana = db.Column(db.String(10), nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    medico = db.relationship('Medico', back_populates='horarios')
    ubicacion = db.relationship('Ubicacion', back_populates='horarios')

    def __repr__(self):
        return f'<HorarioMedico {self.dia_semana} {self.hora_inicio}-{self.hora_fin}>'
