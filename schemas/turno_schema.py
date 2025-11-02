"""
PATRÓN: DTO (Data Transfer Object) Pattern con Marshmallow
==========================================================

DTO PATTERN:
-----------
Los schemas de Marshmallow actúan como DTOs:
- Transfieren datos entre capas (API ↔ Service ↔ Repository)
- Validan datos de entrada
- Serializan/deserializan objetos
- Separan modelo de BD de modelo de API

BENEFICIOS:
----------
1. Validación automática de datos
2. Documentación de API (qué campos se esperan)
3. Transformación de datos (ej: formatear fechas)
4. Seguridad (no exponer campos sensibles)
"""

from marshmallow import fields, validate, validates, ValidationError
from schemas import ma
from models import Turno, Ubicacion
from datetime import date, time

class TurnoSchema(ma.SQLAlchemyAutoSchema):
    """
    Schema para serialización de Turnos.

    DTO PATTERN: Define estructura de datos para transferencia
    """

    class Meta:
        model = Turno
        load_instance = True
        include_fk = True
        include_relationships = True

    # Campos de ID
    id = fields.Int(dump_only=True)
    codigo_turno = fields.Str(dump_only=True)
    creado_en = fields.DateTime(dump_only=True)

    # Campos requeridos
    paciente_id = fields.Int(required=True)
    medico_id = fields.Int(required=True)
    ubicacion_id = fields.Int(required=True)
    fecha = fields.Date(required=True)
    hora = fields.Time(required=True)

    # Campos opcionales
    duracion_min = fields.Int(validate=validate.Range(min=10, max=180), load_default=30)
    estado = fields.Str(validate=validate.OneOf(['pendiente', 'confirmado', 'completado', 'cancelado', 'ausente']))
    motivo_consulta = fields.Str(validate=validate.Length(max=500))

    # Relaciones anidadas (para GET)
    # Al serializar, incluye datos del paciente, médico, ubicación
    paciente = fields.Nested('PacienteSchema', only=['id', 'nombre_completo', 'email'], dump_only=True)
    medico = fields.Nested('MedicoSchema', only=['id', 'nombre_completo', 'especialidad'], dump_only=True)
    ubicacion = fields.Nested('UbicacionSchema', only=['id', 'nombre', 'direccion'], dump_only=True)

    # Campos calculados
    fecha_hora_formatted = fields.Method('get_fecha_hora_formatted', dump_only=True)

    def get_fecha_hora_formatted(self, obj):
        """Formatea fecha y hora para mostrar."""
        return f"{obj.fecha.strftime('%d/%m/%Y')} {obj.hora.strftime('%H:%M')}"

    @validates('fecha')
    def validate_fecha(self, value):
        """
        Valida que la fecha no sea pasada.

        DTO PATTERN: Validaciones en la capa de transferencia
        """
        if value < date.today():
            raise ValidationError('La fecha del turno no puede ser pasada')

    @validates('hora')
    def validate_hora(self, value):
        """
        Valida horario laboral básico.

        Nota: Validaciones de negocio más complejas van en Service Layer
        """
        # Validación básica: entre 6am y 8pm
        if value < time(6, 0) or value > time(20, 0):
            raise ValidationError('El horario debe estar entre 06:00 y 20:00')

class UbicacionSchema(ma.SQLAlchemyAutoSchema):
    """Schema para Ubicaciones."""

    class Meta:
        model = Ubicacion
        load_instance = True

turno_schema = TurnoSchema()
turnos_schema = TurnoSchema(many=True)
ubicacion_schema = UbicacionSchema()
