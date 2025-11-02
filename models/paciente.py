from .database import db
from datetime import datetime

class Paciente(db.Model):
    __tablename__ = 'pacientes'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id', ondelete='SET NULL'), unique=True)
    nro_historia_clinica = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    tipo_documento = db.Column(db.String(20), nullable=False)
    nro_documento = db.Column(db.String(50), unique=True, nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    genero = db.Column(db.String(20))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(255))
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    usuario = db.relationship('Usuario', back_populates='pacientes')
    turnos = db.relationship('Turno', back_populates='paciente', lazy='dynamic')
    historias_clinicas = db.relationship('HistoriaClinica', back_populates='paciente', lazy='dynamic')
    recetas = db.relationship('Receta', back_populates='paciente', lazy='dynamic')

    @property
    def nombre_completo(self):
        return f'{self.nombre} {self.apellido}'

    @property
    def edad(self):
        if self.fecha_nacimiento:
            today = datetime.utcnow().date()
            return today.year - self.fecha_nacimiento.year - (
                (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return None

    def __repr__(self):
        return f'<Paciente {self.nombre_completo} - HC: {self.nro_historia_clinica}>'
