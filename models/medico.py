from .database import db
from datetime import datetime

class Medico(db.Model):
    __tablename__ = 'medicos'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id', ondelete='SET NULL'), unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    matricula = db.Column(db.String(50), unique=True, nullable=False)
    especialidad_id = db.Column(db.Integer, db.ForeignKey('especialidades.id'))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(255))
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    usuario = db.relationship('Usuario', back_populates='medicos')
    especialidad = db.relationship('Especialidad', back_populates='medicos')
    medicos_especialidades = db.relationship('MedicoEspecialidad', back_populates='medico', lazy='dynamic', cascade='all, delete-orphan')
    horarios = db.relationship('HorarioMedico', back_populates='medico', lazy='dynamic', cascade='all, delete-orphan')
    turnos = db.relationship('Turno', back_populates='medico', lazy='dynamic')
    historias_clinicas = db.relationship('HistoriaClinica', back_populates='medico', lazy='dynamic')
    recetas = db.relationship('Receta', back_populates='medico', lazy='dynamic')

    @property
    def nombre_completo(self):
        return f'{self.nombre} {self.apellido}'

    def __repr__(self):
        return f'<Medico {self.nombre_completo} - Mat: {self.matricula}>'


class MedicoEspecialidad(db.Model):
    __tablename__ = 'medicos_especialidades'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    medico_id = db.Column(db.BigInteger, db.ForeignKey('medicos.id', ondelete='CASCADE'), nullable=False)
    especialidad_id = db.Column(db.Integer, db.ForeignKey('especialidades.id', ondelete='CASCADE'), nullable=False)
    es_principal = db.Column(db.Boolean, default=False)
    fecha_certificacion = db.Column(db.Date)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    medico = db.relationship('Medico', back_populates='medicos_especialidades')
    especialidad = db.relationship('Especialidad', back_populates='medicos_especialidades')

    __table_args__ = (
        db.UniqueConstraint('medico_id', 'especialidad_id', name='uq_medico_especialidad'),
    )

    def __repr__(self):
        return f'<MedicoEspecialidad M:{self.medico_id} E:{self.especialidad_id}>'
