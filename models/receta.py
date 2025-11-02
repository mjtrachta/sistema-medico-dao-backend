from .database import db
from datetime import datetime

class Medicamento(db.Model):
    __tablename__ = 'medicamentos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(255), unique=True, nullable=False)
    principio_activo = db.Column(db.String(255))
    descripcion = db.Column(db.Text)
    requiere_receta = db.Column(db.Boolean, default=True)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    items_receta = db.relationship('ItemReceta', back_populates='medicamento', lazy='dynamic')

    def __repr__(self):
        return f'<Medicamento {self.nombre}>'


class Receta(db.Model):
    __tablename__ = 'recetas'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    codigo_receta = db.Column(db.String(50), unique=True, nullable=False)
    historia_clinica_id = db.Column(db.BigInteger, db.ForeignKey('historia_clinica.id'))
    paciente_id = db.Column(db.BigInteger, db.ForeignKey('pacientes.id', ondelete='RESTRICT'), nullable=False)
    medico_id = db.Column(db.BigInteger, db.ForeignKey('medicos.id', ondelete='RESTRICT'), nullable=False)
    fecha = db.Column(db.Date, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='activa')
    valida_hasta = db.Column(db.Date)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    historia_clinica = db.relationship('HistoriaClinica', back_populates='recetas')
    paciente = db.relationship('Paciente', back_populates='recetas')
    medico = db.relationship('Medico', back_populates='recetas')
    items = db.relationship('ItemReceta', back_populates='receta', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Receta {self.codigo_receta}>'


class ItemReceta(db.Model):
    __tablename__ = 'items_receta'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    receta_id = db.Column(db.BigInteger, db.ForeignKey('recetas.id', ondelete='CASCADE'), nullable=False)
    medicamento_id = db.Column(db.Integer, db.ForeignKey('medicamentos.id'))
    nombre_medicamento = db.Column(db.String(255), nullable=False)
    dosis = db.Column(db.String(100))
    frecuencia = db.Column(db.String(100))
    cantidad = db.Column(db.SmallInteger)
    duracion_dias = db.Column(db.SmallInteger)
    instrucciones = db.Column(db.Text)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    receta = db.relationship('Receta', back_populates='items')
    medicamento = db.relationship('Medicamento', back_populates='items_receta')

    def __repr__(self):
        return f'<ItemReceta {self.nombre_medicamento}>'
