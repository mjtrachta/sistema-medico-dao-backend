from reportlab.lib.pagesizes import letter 
from reportlab.lib import colors 
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer 
from reportlab.platypus.tables import Table, TableStyle 
from reportlab.lib.styles import getSampleStyleSheet 
from reportlab.lib.units import inch
from datetime import datetime

documento = SimpleDocTemplate("Turnos_por_especialidad.pdf", pagesize=letter) 

elementos = [] 

estilos = getSampleStyleSheet() 

titulo = "Reporte de Turnos por Especialidad" 
elementos.append(Paragraph(titulo, estilos['Title'])) 

#fecha de generacion de reporte
fecha = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
elementos.append(Paragraph(fecha, estilos['Normal']))
elementos.append(Spacer(1, 0.3 * inch))

#especialidades hardcodeadas
datos_especialidades = {
    "Cardiología": 12,
    "Dermatología": 8,
    "Neurología": 15,
    "Pediatría": 20,
    "Oftalmología": 10
}

data = [["Especialidad", "Cantidad de Turnos"]]
total_turnos = 0

for especialidad, cantidad in datos_especialidades.items():
    data.append([especialidad, str(cantidad)])
    total_turnos += cantidad

data.append(["TOTAL", str(total_turnos)])

table = Table(data, colWidths=[3 * inch, 2 * inch])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
    ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
]))

elementos.append(table)

#generar informe
documento.build(elementos) 

print("Informe generado correctamente: Turnos_por_especialidad.pdf")