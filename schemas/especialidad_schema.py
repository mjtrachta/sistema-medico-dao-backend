from marshmallow import fields, validate
from schemas import ma
from models import Especialidad

class EspecialidadSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Especialidad
        load_instance = True
        include_fk = True

    nombre = fields.Str(required=True, validate=validate.Length(min=3, max=100))
    descripcion = fields.Str(validate=validate.Length(max=255))
    duracion_turno_min = fields.Int(validate=validate.Range(min=10, max=180))

especialidad_schema = EspecialidadSchema()
especialidades_schema = EspecialidadSchema(many=True)
