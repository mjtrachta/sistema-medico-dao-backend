"""
Blueprint de Reportes
=====================

PATRÓN: Facade Pattern
- Expone reportes complejos como endpoints simples
"""

from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
from services.reporte_service import ReporteService
from services.pdf_service import PDFService

reportes_bp = Blueprint('reportes', __name__)

# PDF Service
pdf_service = PDFService()

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


@reportes_bp.route('/turnos-por-especialidad/<int:especialidad_id>', methods=['GET'])
def reporte_turnos_especialidad(especialidad_id):
    """
    Reporte: Cantidad de turnos por especialidad con detalle de médicos.

    Query params:
        - fecha_inicio (YYYY-MM-DD): Fecha de inicio
        - fecha_fin (YYYY-MM-DD): Fecha de fin

    PATRÓN: Facade Pattern + Aggregate Pattern
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
        reporte = reporte_service.turnos_por_especialidad(especialidad_id, fecha_inicio, fecha_fin)

        return jsonify(reporte), 200

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


# ==========================================
# ENDPOINTS PDF - DESCARGA DE REPORTES
# ==========================================

@reportes_bp.route('/turnos-por-medico/<int:medico_id>/pdf', methods=['GET'])
def descargar_pdf_turnos_medico(medico_id):
    """
    Descarga reporte de turnos por médico en PDF.

    Query params:
        - fecha_inicio (YYYY-MM-DD): Fecha de inicio
        - fecha_fin (YYYY-MM-DD): Fecha de fin

    Returns:
        PDF file para descarga
    """
    try:
        # Parsear fechas
        fecha_inicio_str = request.args.get('fecha_inicio')
        fecha_fin_str = request.args.get('fecha_fin')

        if not fecha_inicio_str or not fecha_fin_str:
            raise ValueError("Los parámetros fecha_inicio y fecha_fin son requeridos")

        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()

        # Obtener datos del reporte
        reporte = reporte_service.turnos_por_medico(medico_id, fecha_inicio, fecha_fin)

        # Generar PDF
        pdf_buffer = pdf_service.generar_pdf_turnos_medico(reporte)

        # Nombre del archivo
        filename = f"turnos_medico_{medico_id}_{fecha_inicio}_{fecha_fin}.pdf"

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reportes_bp.route('/turnos-por-especialidad/<int:especialidad_id>/pdf', methods=['GET'])
def descargar_pdf_turnos_especialidad(especialidad_id):
    """
    Descarga reporte de turnos por especialidad en PDF.

    Query params:
        - fecha_inicio (YYYY-MM-DD): Fecha de inicio
        - fecha_fin (YYYY-MM-DD): Fecha de fin

    Returns:
        PDF file para descarga
    """
    try:
        # Parsear fechas
        fecha_inicio_str = request.args.get('fecha_inicio')
        fecha_fin_str = request.args.get('fecha_fin')

        if not fecha_inicio_str or not fecha_fin_str:
            raise ValueError("Los parámetros fecha_inicio y fecha_fin son requeridos")

        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()

        # Obtener datos del reporte
        reporte = reporte_service.turnos_por_especialidad(especialidad_id, fecha_inicio, fecha_fin)

        # Generar PDF
        pdf_buffer = pdf_service.generar_pdf_turnos_especialidad(reporte)

        # Nombre del archivo
        filename = f"turnos_especialidad_{especialidad_id}_{fecha_inicio}_{fecha_fin}.pdf"

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reportes_bp.route('/pacientes-atendidos/pdf', methods=['GET'])
def descargar_pdf_pacientes_atendidos():
    """
    Descarga reporte de pacientes atendidos en PDF.

    Query params:
        - fecha_inicio (YYYY-MM-DD): Requerido
        - fecha_fin (YYYY-MM-DD): Requerido
        - medico_id (int): Opcional
        - especialidad_id (int): Opcional

    Returns:
        PDF file para descarga
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

        # Obtener datos del reporte
        reporte = reporte_service.pacientes_atendidos(
            fecha_inicio,
            fecha_fin,
            medico_id,
            especialidad_id
        )

        # Generar PDF
        pdf_buffer = pdf_service.generar_pdf_pacientes_atendidos(reporte)

        # Nombre del archivo
        filename = f"pacientes_atendidos_{fecha_inicio}_{fecha_fin}.pdf"

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reportes_bp.route('/estadisticas-asistencia/pdf', methods=['GET'])
def descargar_pdf_estadisticas_asistencia():
    """
    Descarga reporte estadístico de asistencia en PDF.

    Query params (opcionales):
        - fecha_inicio (YYYY-MM-DD)
        - fecha_fin (YYYY-MM-DD)
        - medico_id (int)

    Returns:
        PDF file para descarga con gráficos
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

        # Obtener datos del reporte
        reporte = reporte_service.estadisticas_asistencia(
            fecha_inicio,
            fecha_fin,
            medico_id
        )

        # Generar PDF
        pdf_buffer = pdf_service.generar_pdf_estadisticas_asistencia(reporte)

        # Nombre del archivo
        if fecha_inicio and fecha_fin:
            filename = f"estadisticas_asistencia_{fecha_inicio}_{fecha_fin}.pdf"
        else:
            filename = f"estadisticas_asistencia_{datetime.now().strftime('%Y%m%d')}.pdf"

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
