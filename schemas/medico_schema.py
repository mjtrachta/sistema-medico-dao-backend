from marshmallow import fields, validate
from schemas import ma
from models import Medico, MedicoEspecialidad

class MedicoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Medico
        load_instance = True
        include_fk = True
        exclude = ('usuario_id',)

    nombre = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    apellido = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    matricula = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email()
    telefono = fields.Str(validate=validate.Length(max=20))

    # Campos anidados
    especialidad = fields.Nested('EspecialidadSchema', only=['id', 'nombre'])

    # Campos calculados
    nombre_completo = fields.Method('get_nombre_completo')

    def get_nombre_completo(self, obj):
        return f"Dr./Dra. {obj.nombre} {obj.apellido}"

class MedicoEspecialidadSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = MedicoEspecialidad
        load_instance = True
        include_fk = True

    especialidad = fields.Nested('EspecialidadSchema', only=['id', 'nombre'])

medico_schema = MedicoSchema()
medicos_schema = MedicoSchema(many=True)
medico_especialidad_schema = MedicoEspecialidadSchema()
medicos_especialidades_schema = MedicoEspecialidadSchema(many=True)
