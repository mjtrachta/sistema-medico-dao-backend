from reportlab.lib.pagesizes import letter 
from reportlab.lib import colors 
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer 
from reportlab.platypus.tables import Table, TableStyle 
from reportlab.lib.styles import getSampleStyleSheet 
from reportlab.lib.units import inch
from datetime import datetime, timedelta


def obtener_pacientes_por_fecha(fecha_inicio, fecha_fin):
    
    pacientes = [
        {"nombre": "Juan Pérez", "fecha_atencion": "15-11-2025", "diagnostico": "Gripe"},
        {"nombre": "María López", "fecha_atencion": "16-11-2025", "diagnostico": "Migraña"},
        {"nombre": "Carlos Ruiz", "fecha_atencion": "17-11-2025", "diagnostico": "Dolor de espalda"},
    ]
    return pacientes

fecha_inicio = datetime(2025 , 11, 1)
fecha_fin = datetime(2025, 11, 30)

documento = SimpleDocTemplate("Pacientes_por_fecha.pdf", pagesize=letter) 
elementos = [] 
estilos = getSampleStyleSheet() 

titulo = f"Reporte de Pacientes Atendidos"
elementos.append(Paragraph(titulo, estilos['Title'])) 

fecha_texto = f"Período: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"
elementos.append(Paragraph(fecha_texto, estilos['Normal']))
elementos.append(Spacer(1, 0.3 * inch))

pacientes = obtener_pacientes_por_fecha(fecha_inicio, fecha_fin)

datos = [["Nombre", "Fecha de Atención", "Diagnóstico"]]
for paciente in pacientes:
    datos.append([
        paciente["nombre"],
        paciente["fecha_atencion"],
        paciente["diagnostico"]
    ])

table = Table(datos, colWidths=[2 * inch, 1.5 * inch, 2 * inch])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
]))

elementos.append(table)


elementos.append(Spacer(1, 0.3 * inch))
total_texto = f"Total de pacientes atendidos: {len(pacientes)}"
elementos.append(Paragraph(total_texto, estilos['Normal']))

documento.build(elementos) 
print("✓ Informe generado correctamente: Pacientes_por_fecha.pdf")