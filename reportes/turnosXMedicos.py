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

def _obtener_rango_fechas():
    fecha_actual = date.today()

    while True:
        try:
            fecha_inicio_str = input("Fecha inicio (DD/MM/YYYY): ").strip()
            fecha_fin_str = input("Fecha fin (DD/MM/YYYY): ").strip()
            
            fecha_inicio = datetime.strptime(fecha_inicio_str, "%d/%m/%Y").date()
            fecha_fin = datetime.strptime(fecha_fin_str, "%d/%m/%Y").date()
            
            if fecha_inicio > fecha_actual:
                print("Error: La fecha de inicio no puede ser mayor a la fecha actual.")
                continue
            
            if fecha_fin > fecha_actual:
                print("Error: La fecha de fin no puede ser mayor a la fecha actual.")
                continue
            
            if fecha_fin < fecha_inicio:
                print("Error: La fecha de fin no puede ser menor a la fecha de inicio.")
                continue
            
            print(f"Rango válido: {fecha_inicio_str} a {fecha_fin_str}")
            return fecha_inicio, fecha_fin
            
        except ValueError:
            print("Error: Formato de fecha inválido. Use DD/MM/YYYY")
        except KeyboardInterrupt:
            print("\n\nOperación cancelada por el usuario.")
            exit()

def _cabecera_footer(canvas, doc, titulo, rango):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(inch, doc.pagesize[1] - 0.75 * inch, titulo)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(inch, doc.pagesize[1] - 0.95 * inch, rango)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(doc.pagesize[0] - inch, 0.75 * inch, f"Página {doc.page}")
    canvas.restoreState()

def generar_reporte_turnos_por_medico(turnos, fecha_inicio, fecha_fin, salida="Turnos_por_medicos.pdf"):
    #normalizar fechas
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

    #filtrar por rango de fechas y agrupar por médico
    grupos = {}
    for t in turnos:
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

    #genera el documento
    documento = SimpleDocTemplate(salida, pagesize=letter,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=inch + 0.5*inch, bottomMargin=inch)
    elementos = []

    titulo = "Turnos por médico"
    rango_texto = f"Período: {_formatear_fecha(fi)} - {_formatear_fecha(ff)}"

    # Ordenar médicos por nombre
    for medico in sorted(grupos.keys()):
        items = grupos[medico]
        elementos.append(Paragraph(f"<b>Médico:</b> {medico}", estilos['Heading2']))
        elementos.append(Paragraph(f"<b>Cantidad de turnos:</b> {len(items)}", estilos['Normal']))
        elementos.append(Spacer(1, 0.1 * inch))

        data = [["Fecha", "Hora", "Paciente", "Especialidad", "Estado"]]
        #ordenar por fecha y hora
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

    if not elementos:
        elementos.append(Paragraph("No se encontraron turnos en el período seleccionado.", estilos['Normal']))

    documento.build(elementos, onFirstPage=lambda c, d: _cabecera_footer(c, d, titulo, rango_texto),
              onLaterPages=lambda c, d: _cabecera_footer(c, d, titulo, rango_texto))

    print(f"Informe generado correctamente: {salida}")


if __name__ == "__main__":
    turnos = [
        {"medico_nombre": "Dr. Pérez", "fecha": "2025-11-10T09:00:00", "hora": "09:00", "paciente": "Ana López", "especialidad": "Cardiología", "estado": "Confirmado"},
        {"medico_nombre": "Dr. Pérez", "fecha": "2025-11-11T10:30:00", "hora": "10:30", "paciente": "Juan Ruiz", "especialidad": "Cardiología", "estado": "Pendiente"},
        {"medico_nombre": "Dra. Gómez", "fecha": "2025-11-12T11:00:00", "hora": "11:00", "paciente": "María Díaz", "especialidad": "Pediatría", "estado": "Confirmado"},
        {"medico_nombre": "Dr. Pérez", "fecha": "2025-11-13T14:00:00", "hora": "14:00", "paciente": "Carlos Martín", "especialidad": "Cardiología", "estado": "Confirmado"},
        {"medico_nombre": "Dr. Rodríguez", "fecha": "2025-11-10T08:30:00", "hora": "08:30", "paciente": "Laura Sánchez", "especialidad": "Dermatología", "estado": "Confirmado"},
        {"medico_nombre": "Dra. Gómez", "fecha": "2025-11-14T09:15:00", "hora": "09:15", "paciente": "Pedro González", "especialidad": "Pediatría", "estado": "Cancelado"},
        {"medico_nombre": "Dr. Rodríguez", "fecha": "2025-11-15T15:45:00", "hora": "15:45", "paciente": "Sofía Ramírez", "especialidad": "Dermatología", "estado": "Confirmado"},
        {"medico_nombre": "Dr. Pérez", "fecha": "2025-11-12T16:00:00", "hora": "16:00", "paciente": "Roberto Vega", "especialidad": "Cardiología", "estado": "Pendiente"},
        {"medico_nombre": "Dra. Gómez", "fecha": "2025-11-11T14:30:00", "hora": "14:30", "paciente": "Lucía Fernández", "especialidad": "Pediatría", "estado": "Confirmado"},
        {"medico_nombre": "Dr. Rodríguez", "fecha": "2025-11-13T10:00:00", "hora": "10:00", "paciente": "Diego Moreno", "especialidad": "Dermatología", "estado": "Confirmado"},
        {"medico_nombre": "Dr. Pérez", "fecha": "2025-11-10T15:30:00", "hora": "15:30", "paciente": "Valentina Cruz", "especialidad": "Cardiología", "estado": "Confirmado"},
        {"medico_nombre": "Dra. Gómez", "fecha": "2025-11-13T16:20:00", "hora": "16:20", "paciente": "Andrés Gutiérrez", "especialidad": "Pediatría", "estado": "Confirmado"},
    ]

    # Ingresar rango de fechas (usa fechas válidas: hasta hoy 18/11/2025)
    fecha_inicio, fecha_fin = _obtener_rango_fechas()
    
    generar_reporte_turnos_por_medico(turnos, fecha_inicio, fecha_fin, salida="Turnos_por_medicos.pdf")