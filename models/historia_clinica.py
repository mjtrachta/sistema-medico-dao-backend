from .database import db
from datetime import datetime

class HistoriaClinica(db.Model):
    __tablename__ = 'historia_clinica'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    turno_id = db.Column(db.BigInteger, db.ForeignKey('turnos.id', ondelete='SET NULL'), unique=True)
    paciente_id = db.Column(db.BigInteger, db.ForeignKey('pacientes.id', ondelete='RESTRICT'), nullable=False)
    medico_id = db.Column(db.BigInteger, db.ForeignKey('medicos.id', ondelete='RESTRICT'), nullable=False)
    fecha_consulta = db.Column(db.Date, nullable=False)
    motivo_consulta = db.Column(db.Text)
    diagnostico = db.Column(db.Text)
    tratamiento = db.Column(db.Text)
    observaciones = db.Column(db.Text)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    turno = db.relationship('Turno', back_populates='historia_clinica')
    paciente = db.relationship('Paciente', back_populates='historias_clinicas')
    medico = db.relationship('Medico', back_populates='historias_clinicas')
    recetas = db.relationship('Receta', back_populates='historia_clinica', lazy='dynamic')

    def __repr__(self):
        return f'<HistoriaClinica P:{self.paciente_id} - {self.fecha_consulta}>'
