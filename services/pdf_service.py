"""
Servicio de Generación de PDFs
================================

PATRÓN: Adapter Pattern + Builder Pattern
- Adapta los scripts de reportes existentes para usar datos reales
- Construye PDFs con formato profesional usando ReportLab
"""

from io import BytesIO
from datetime import datetime, date
from typing import Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, PageBreak
)

import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt


class PDFService:
    """
    Servicio para generar reportes en PDF.

    PATRÓN: Adapter Pattern
    - Adapta datos de reporte_service a formato PDF

    PATRÓN: Builder Pattern
    - Construye PDFs paso a paso con elementos reutilizables
    """

    def __init__(self):
        self.estilos = getSampleStyleSheet()
        self._configurar_estilos()

    def _configurar_estilos(self):
        """Configura estilos personalizados para PDFs."""
        self.titulo_style = ParagraphStyle(
            'CustomTitle',
            parent=self.estilos['Heading1'],
            fontSize=24,
            textColor='#1f4788',
            spaceAfter=30,
            alignment=TA_CENTER
        )

        self.subtitulo_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.estilos['Heading2'],
            fontSize=14,
            textColor='#4a4a4a',
            spaceAfter=20,
            alignment=TA_CENTER
        )

    # ==========================================
    # REPORTE 1: Turnos por Médico
    # ==========================================

    def generar_pdf_turnos_medico(self, reporte_data: Dict) -> BytesIO:
        """
        Genera PDF de turnos por médico.

        Args:
            reporte_data: Datos del reporte (de reporte_service.turnos_por_medico)

        Returns:
            BytesIO con el PDF generado
        """
        buffer = BytesIO()

        documento = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch + 0.5*inch,
            bottomMargin=inch
        )

        elementos = []

        # Título
        titulo = f"Turnos de Dr./Dra. {reporte_data['medico_nombre']}"
        elementos.append(Paragraph(titulo, self.titulo_style))
        elementos.append(Spacer(1, 0.2*inch))

        # Período
        periodo_texto = f"Período: {reporte_data['fecha_inicio']} - {reporte_data['fecha_fin']}"
        elementos.append(Paragraph(periodo_texto, self.estilos['Normal']))
        elementos.append(Spacer(1, 0.1*inch))

        # Estadísticas
        stats = reporte_data['estadisticas']
        stats_html = f"""
        <b>Estadísticas del Período:</b><br/>
        Total de turnos: {stats['total']}<br/>
        Completados: {stats['completados']}<br/>
        Confirmados: {stats.get('confirmados', 0)}<br/>
        Cancelados: {stats['cancelados']}<br/>
        Ausentes: {stats.get('ausentes', 0)}<br/>
        Pendientes: {stats['pendientes']}
        """
        elementos.append(Paragraph(stats_html, self.estilos['Normal']))
        elementos.append(Spacer(1, 0.3*inch))

        # Tabla de turnos
        if reporte_data['turnos']:
            elementos.append(Paragraph("<b>Detalle de Turnos:</b>", self.estilos['Heading3']))
            elementos.append(Spacer(1, 0.1*inch))

            data = [["Código", "Fecha", "Hora", "Paciente", "Estado"]]

            for turno in reporte_data['turnos']:
                data.append([
                    turno['codigo_turno'],
                    turno['fecha'],
                    turno['hora'],
                    turno['paciente']['nombre_completo'] if turno.get('paciente') else 'N/A',
                    turno['estado'].capitalize()
                ])

            col_widths = [1.2*inch, 1.0*inch, 0.8*inch, 2.0*inch, 1.0*inch]
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
            ]))
            elementos.append(table)
        else:
            elementos.append(Paragraph("No se encontraron turnos en el período.", self.estilos['Normal']))

        # Footer
        elementos.append(Spacer(1, 0.5*inch))
        fecha_gen = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        elementos.append(Paragraph(fecha_gen, self.estilos['Normal']))

        documento.build(elementos)
        buffer.seek(0)
        return buffer

    # ==========================================
    # REPORTE 2: Estadísticas de Asistencia
    # ==========================================

    def generar_pdf_estadisticas_asistencia(self, reporte_data: Dict) -> BytesIO:
        """
        Genera PDF de estadísticas de asistencia con gráficos.

        Args:
            reporte_data: Datos del reporte (de reporte_service.estadisticas_asistencia)

        Returns:
            BytesIO con el PDF generado
        """
        buffer = BytesIO()

        documento = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        elementos = []

        # Título
        elementos.append(Paragraph("INFORME DE ASISTENCIAS", self.titulo_style))
        elementos.append(Spacer(1, 0.3*inch))

        # Período
        if reporte_data.get('fecha_inicio'):
            periodo_texto = f"<b>Período:</b> {reporte_data['fecha_inicio']} - {reporte_data['fecha_fin']}"
            elementos.append(Paragraph(periodo_texto, self.estilos['Normal']))

        fecha_actual = datetime.now().strftime("%d de %B de %Y")
        elementos.append(Paragraph(f"<b>Generado:</b> {fecha_actual}", self.estilos['Normal']))
        elementos.append(Spacer(1, 0.2*inch))

        # Subtítulo
        elementos.append(Paragraph("Asistencias vs Inasistencias", self.subtitulo_style))
        elementos.append(Spacer(1, 0.2*inch))

        # Estadísticas
        resumen = reporte_data['resumen']
        completados = resumen['completados']
        cancelados = resumen['cancelados']
        total = resumen['total_turnos']

        stats_text = f"""
        <b>Total de Turnos:</b> {total}<br/>
        <b>Completados:</b> {completados} ({reporte_data.get('porcentaje_completados', 0):.1f}%)<br/>
        <b>Cancelados:</b> {cancelados} ({reporte_data.get('porcentaje_cancelados', 0):.1f}%)<br/>
        <b>Ausentes:</b> {reporte_data.get('ausentes', 0)} ({reporte_data.get('porcentaje_ausentes', 0):.1f}%)
        """
        elementos.append(Paragraph(stats_text, self.estilos['Normal']))
        elementos.append(Spacer(1, 0.3*inch))

        # Gráficos (solo si hay datos)
        if total > 0:
            chart_buffer = self._generar_grafico_asistencia(completados, cancelados + reporte_data.get('ausentes', 0))
            elementos.append(Image(chart_buffer, width=6*inch, height=2.5*inch))

        documento.build(elementos)
        buffer.seek(0)
        return buffer

    def _generar_grafico_asistencia(self, asistencias: int, inasistencias: int) -> BytesIO:
        """Genera gráfico de torta y barras de asistencias."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        data = [asistencias, inasistencias]
        labels = ['Asistencias', 'Inasistencias']
        chart_colors = ['#2ecc71', '#e74c3c']

        # Gráfico de torta
        ax1.pie(data, labels=labels, autopct='%1.1f%%', colors=chart_colors, startangle=90)
        ax1.set_title('Distribución de Asistencias', fontsize=12, fontweight='bold')

        # Gráfico de barras
        ax2.bar(labels, data, color=chart_colors, edgecolor='black', linewidth=1.5)
        ax2.set_ylabel('Cantidad de Turnos', fontsize=10)
        ax2.set_title('Comparativa', fontsize=12, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close()

        return buffer

    # ==========================================
    # REPORTE 3: Turnos por Especialidad
    # ==========================================

    def generar_pdf_turnos_especialidad(self, reporte_data: Dict) -> BytesIO:
        """
        Genera PDF de turnos por especialidad.

        Args:
            reporte_data: Datos del reporte (de reporte_service.turnos_por_especialidad)

        Returns:
            BytesIO con el PDF generado
        """
        buffer = BytesIO()

        documento = SimpleDocTemplate(buffer, pagesize=letter)
        elementos = []

        # Título
        titulo = f"Reporte de Turnos - {reporte_data['especialidad_nombre']}"
        elementos.append(Paragraph(titulo, self.estilos['Title']))

        # Fecha de generación
        fecha = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        elementos.append(Paragraph(fecha, self.estilos['Normal']))

        # Período
        periodo_texto = f"Período: {reporte_data['fecha_inicio']} - {reporte_data['fecha_fin']}"
        elementos.append(Paragraph(periodo_texto, self.estilos['Normal']))
        elementos.append(Spacer(1, 0.3*inch))

        # Estadísticas
        elementos.append(Paragraph(f"<b>Total de médicos:</b> {reporte_data['total_medicos']}", self.estilos['Normal']))
        elementos.append(Paragraph(f"<b>Total de turnos:</b> {reporte_data['total_turnos']}", self.estilos['Normal']))
        elementos.append(Spacer(1, 0.3*inch))

        # Tabla de médicos y turnos
        data = [["Médico", "Cantidad de Turnos"]]

        for medico in reporte_data['medicos_turnos']:
            data.append([
                medico['medico_nombre'],
                str(medico['total'])
            ])

        data.append(["TOTAL", str(reporte_data['total_turnos'])])

        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-2), colors.beige),
            ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))

        elementos.append(table)

        documento.build(elementos)
        buffer.seek(0)
        return buffer

    # ==========================================
    # REPORTE 4: Pacientes Atendidos
    # ==========================================

    def generar_pdf_pacientes_atendidos(self, reporte_data: Dict) -> BytesIO:
        """
        Genera PDF de pacientes atendidos.

        Args:
            reporte_data: Datos del reporte (de reporte_service.pacientes_atendidos)

        Returns:
            BytesIO con el PDF generado
        """
        buffer = BytesIO()

        documento = SimpleDocTemplate(buffer, pagesize=letter)
        elementos = []

        # Título
        titulo = "Reporte de Pacientes Atendidos"
        elementos.append(Paragraph(titulo, self.estilos['Title']))

        # Período
        fecha_texto = f"Período: {reporte_data['fecha_inicio']} - {reporte_data['fecha_fin']}"
        elementos.append(Paragraph(fecha_texto, self.estilos['Normal']))
        elementos.append(Spacer(1, 0.3*inch))

        # Tabla de pacientes
        if reporte_data['pacientes']:
            data = [["Nombre", "HC", "Consultas", "Última Consulta"]]

            for paciente in reporte_data['pacientes']:
                data.append([
                    paciente['nombre_completo'],
                    paciente['nro_historia_clinica'],
                    str(paciente['consultas']),
                    paciente.get('ultima_consulta', 'N/A')
                ])

            table = Table(data, colWidths=[2*inch, 1.5*inch, 1*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 12),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.lightgrey])
            ]))

            elementos.append(table)
            elementos.append(Spacer(1, 0.3*inch))

        # Total
        total_texto = f"Total de pacientes atendidos: {reporte_data['total_pacientes']}"
        elementos.append(Paragraph(total_texto, self.estilos['Normal']))

        documento.build(elementos)
        buffer.seek(0)
        return buffer
