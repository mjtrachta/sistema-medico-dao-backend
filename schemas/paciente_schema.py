from marshmallow import fields, validate, validates, ValidationError
from schemas import ma
from models import Paciente
from datetime import date

class PacienteSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Paciente
        load_instance = True
        include_fk = True
        exclude = ('usuario_id',)

    nombre = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    apellido = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    nro_historia_clinica = fields.Str(required=True)
    tipo_documento = fields.Str(required=True, validate=validate.OneOf(['DNI', 'LC', 'LE', 'Pasaporte']))
    nro_documento = fields.Str(required=True, validate=validate.Length(min=7, max=50))
    fecha_nacimiento = fields.Date(required=True)
    genero = fields.Str(validate=validate.OneOf(['masculino', 'femenino', 'otro', 'no_especifica']))
    email = fields.Email()
    telefono = fields.Str(validate=validate.Length(max=20))

    # Campos calculados
    nombre_completo = fields.Method('get_nombre_completo')
    edad = fields.Method('get_edad')

    def get_nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"

    def get_edad(self, obj):
        if obj.fecha_nacimiento:
            today = date.today()
            return today.year - obj.fecha_nacimiento.year - (
                (today.month, today.day) < (obj.fecha_nacimiento.month, obj.fecha_nacimiento.day)
            )
        return None

    @validates('fecha_nacimiento')
    def validate_fecha_nacimiento(self, value):
        if value > date.today():
            raise ValidationError('La fecha de nacimiento no puede ser futura')
        if value < date(1900, 1, 1):
            raise ValidationError('Fecha de nacimiento inválida')

paciente_schema = PacienteSchema()
pacientes_schema = PacienteSchema(many=True)
