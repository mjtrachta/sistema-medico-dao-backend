from .database import db
from datetime import datetime

class Especialidad(db.Model):
    __tablename__ = 'especialidades'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))
    duracion_turno_min = db.Column(db.SmallInteger, default=30)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    medicos = db.relationship('Medico', back_populates='especialidad', lazy='dynamic')
    medicos_especialidades = db.relationship('MedicoEspecialidad', back_populates='especialidad', lazy='dynamic')

    def __repr__(self):
        return f'<Especialidad {self.nombre}>'
