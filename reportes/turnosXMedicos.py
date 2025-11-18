from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime, date 

estilos = getSampleStyleSheet()

def _formatear_fecha(f):
    if isinstance(f, str):
        try:
            dt = datetime.fromisoformat(f)
        except ValueError:
            dt = datetime.strptime(f, "%Y-%m-%d")
    elif isinstance(f, datetime):
        dt = f
    elif isinstance(f, date):
        dt = datetime.combine(f, datetime.min.time())
    else:
        return str(f)
    return dt.strftime("%d/%m/%Y")

def _cabecera_footer(canvas, doc, titulo, rango):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(inch, doc.pagesize[1] - 0.75 * inch, titulo)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(inch, doc.pagesize[1] - 0.95 * inch, rango)
    # Pie de página: número de página
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(doc.pagesize[0] - inch, 0.75 * inch, f"Página {doc.page}")
    canvas.restoreState()

def generar_reporte_turnos_por_medico(turnos, fecha_inicio, fecha_fin, salida="Turnos_por_medicos.pdf"):
    # Normalizar fechas
    def to_date(d):
        if isinstance(d, str):
            try:
                return datetime.fromisoformat(d).date()
            except ValueError:
                return datetime.strptime(d, "%Y-%m-%d").date()
        if isinstance(d, datetime):
            return d.date()
        if isinstance(d, date):
            return d
        raise ValueError("Fecha no reconocida")
    fi = to_date(fecha_inicio)
    ff = to_date(fecha_fin)

    # Filtrar por rango de fechas e agrupar por médico
    grupos = {}
    for t in turnos:
        # Obtener fecha del turno
        raw = t.get("fecha") or t.get("fecha_turno") or t.get("date")
        if raw is None:
            continue
        if isinstance(raw, str):
            try:
                dt = datetime.fromisoformat(raw)
            except ValueError:
                dt = datetime.strptime(raw, "%Y-%m-%d")
        elif isinstance(raw, datetime):
            dt = raw
        elif isinstance(raw, date):
            dt = datetime.combine(raw, datetime.min.time())
        else:
            continue
        d = dt.date()
        if d < fi or d > ff:
            continue

        medico_nombre = t.get("medico_nombre") or t.get("medico") or "Sin nombre"
        grupos.setdefault(medico_nombre, []).append({**t, "fecha_dt": dt})

    # Construir PDF
    doc = SimpleDocTemplate(salida, pagesize=letter,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=inch + 0.5*inch, bottomMargin=inch)
    elementos = []

    titulo = "Turnos por médico"
    rango_texto = f"Período: {_formatear_fecha(fi)} - {_formatear_fecha(ff)}"

    # Ordenar médicos por nombre
    for medico in sorted(grupos.keys()):
        items = grupos[medico]
        # Encabezado por médico
        elementos.append(Paragraph(f"<b>Médico:</b> {medico}", estilos['Heading2']))
        elementos.append(Paragraph(f"<b>Cantidad de turnos:</b> {len(items)}", estilos['Normal']))
        elementos.append(Spacer(1, 0.1 * inch))

        # Tabla de turnos del médico
        data = [["Fecha", "Hora", "Paciente", "Especialidad", "Estado"]]
        # Ordenar por fecha/hora
        items_sorted = sorted(items, key=lambda x: x.get("fecha_dt"))
        for it in items_sorted:
            fecha = _formatear_fecha(it.get("fecha_dt"))
            hora = it.get("hora") or (it.get("fecha_dt").strftime("%H:%M") if isinstance(it.get("fecha_dt"), datetime) else "")
            paciente = it.get("paciente") or ""
            especialidad = it.get("especialidad") or ""
            estado = it.get("estado") or ""
            data.append([fecha, hora, paciente, especialidad, estado])

        col_widths = [1.2*inch, 0.9*inch, 2.2*inch, 1.6*inch, 1.0*inch]
        table = Table(data, colWidths=col_widths, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1, -1), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
        ]))
        elementos.append(table)
        elementos.append(Spacer(1, 0.2 * inch))
        elementos.append(PageBreak())

    if not elementos:
        elementos.append(Paragraph("No se encontraron turnos en el período seleccionado.", estilos['Normal']))

    # Eliminar el último PageBreak si existe
    if elementos and isinstance(elementos[-1], PageBreak):
        elementos = elementos[:-1]

    # Construir PDF con cabecera/pie
    doc.build(elementos, onFirstPage=lambda c, d: _cabecera_footer(c, d, titulo, rango_texto),
              onLaterPages=lambda c, d: _cabecera_footer(c, d, titulo, rango_texto))

    print(f"Informe generado correctamente: {salida}")


if __name__ == "__main__":
    turnos = [
        {"medico_nombre": "Dr. Pérez", "fecha": "2025-11-10T09:00:00", "hora": "09:00", "paciente": "Ana López", "especialidad": "Cardiología", "estado": "Confirmado"},
        {"medico_nombre": "Dr. Pérez", "fecha": "2025-11-11T10:30:00", "hora": "10:30", "paciente": "Juan Ruiz", "especialidad": "Cardiología", "estado": "Pendiente"},
        {"medico_nombre": "Dra. Gómez", "fecha": "2025-11-12T11:00:00", "hora": "11:00", "paciente": "María Díaz", "especialidad": "Pediatría", "estado": "Confirmado"},
    ]
    generar_reporte_turnos_por_medico(turnos, "2025-11-01", "2025-11-30", salida="Turnos_por_medicos.pdf")