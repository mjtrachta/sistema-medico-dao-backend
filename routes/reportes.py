"""
Blueprint de Reportes
=====================

PATRÓN: Facade Pattern
- Expone reportes complejos como endpoints simples
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from services.reporte_service import ReporteService

reportes_bp = Blueprint('reportes', __name__)

# Service
reporte_service = ReporteService()


@reportes_bp.route('/turnos-por-medico/<int:medico_id>', methods=['GET'])
def reporte_turnos_medico(medico_id):
    """
    Reporte: Listado de turnos por médico en un período.

    Query params:
        - fecha_inicio (YYYY-MM-DD): Fecha de inicio
        - fecha_fin (YYYY-MM-DD): Fecha de fin

    PATRÓN: Facade Pattern
    """
    try:
        # Parsear fechas
        fecha_inicio_str = request.args.get('fecha_inicio')
        fecha_fin_str = request.args.get('fecha_fin')

        if not fecha_inicio_str or not fecha_fin_str:
            raise ValueError("Los parámetros fecha_inicio y fecha_fin son requeridos")

        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()

        # Generar reporte
        reporte = reporte_service.turnos_por_medico(medico_id, fecha_inicio, fecha_fin)

        return jsonify(reporte), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reportes_bp.route('/turnos-por-especialidad', methods=['GET'])
def reporte_turnos_especialidad():
    """
    Reporte: Cantidad de turnos por especialidad.

    Query params (opcionales):
        - fecha_inicio (YYYY-MM-DD)
        - fecha_fin (YYYY-MM-DD)

    PATRÓN: Facade Pattern + Aggregate Pattern
    """
    try:
        # Parsear fechas opcionales
        fecha_inicio = None
        fecha_fin = None

        fecha_inicio_str = request.args.get('fecha_inicio')
        if fecha_inicio_str:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()

        fecha_fin_str = request.args.get('fecha_fin')
        if fecha_fin_str:
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()

        # Generar reporte
        reporte = reporte_service.turnos_por_especialidad(fecha_inicio, fecha_fin)

        return jsonify({
            'periodo': {
                'inicio': fecha_inicio.isoformat() if fecha_inicio else None,
                'fin': fecha_fin.isoformat() if fecha_fin else None
            },
            'especialidades': reporte
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reportes_bp.route('/pacientes-atendidos', methods=['GET'])
def reporte_pacientes_atendidos():
    """
    Reporte: Pacientes atendidos en un rango de fechas.

    Query params:
        - fecha_inicio (YYYY-MM-DD): Requerido
        - fecha_fin (YYYY-MM-DD): Requerido
        - medico_id (int): Opcional
        - especialidad_id (int): Opcional

    PATRÓN: Facade Pattern + Query Object Pattern
    """
    try:
        # Parsear parámetros requeridos
        fecha_inicio_str = request.args.get('fecha_inicio')
        fecha_fin_str = request.args.get('fecha_fin')

        if not fecha_inicio_str or not fecha_fin_str:
            raise ValueError("Los parámetros fecha_inicio y fecha_fin son requeridos")

        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()

        # Parámetros opcionales
        medico_id = request.args.get('medico_id', type=int)
        especialidad_id = request.args.get('especialidad_id', type=int)

        # Generar reporte
        reporte = reporte_service.pacientes_atendidos(
            fecha_inicio,
            fecha_fin,
            medico_id,
            especialidad_id
        )

        return jsonify(reporte), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reportes_bp.route('/estadisticas-asistencia', methods=['GET'])
def reporte_estadisticas_asistencia():
    """
    Reporte estadístico: Asistencia vs Inasistencias.

    Query params (opcionales):
        - fecha_inicio (YYYY-MM-DD)
        - fecha_fin (YYYY-MM-DD)
        - medico_id (int)

    Returns: Datos para gráfico de asistencias/cancelaciones.

    PATRÓN: Facade Pattern + Aggregate Pattern
    """
    try:
        # Parsear fechas opcionales
        fecha_inicio = None
        fecha_fin = None
        medico_id = None

        fecha_inicio_str = request.args.get('fecha_inicio')
        if fecha_inicio_str:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()

        fecha_fin_str = request.args.get('fecha_fin')
        if fecha_fin_str:
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()

        medico_id = request.args.get('medico_id', type=int)

        # Generar reporte
        reporte = reporte_service.estadisticas_asistencia(
            fecha_inicio,
            fecha_fin,
            medico_id
        )

        return jsonify(reporte), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
