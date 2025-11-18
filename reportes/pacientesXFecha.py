from reportlab.lib.pagesizes import letter 
from reportlab.lib import colors 
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer 
from reportlab.platypus.tables import Table, TableStyle 
from reportlab.lib.styles import getSampleStyleSheet 
from reportlab.lib.units import inch
from datetime import datetime, timedelta

def obtener_fechas_validadas():
    
    #Validar rango de fechas ingresadas
    fecha_actual = datetime.now()
    
    while True:
        try:
            fecha_inicio_str = input("Ingrese la fecha de inicio (DD/MM/YYYY): ")
            fecha_inicio = datetime.strptime(fecha_inicio_str, "%d/%m/%Y")
            
            fecha_fin_str = input("Ingrese la fecha de fin (DD/MM/YYYY): ")
            fecha_fin = datetime.strptime(fecha_fin_str, "%d/%m/%Y")
            
            if fecha_fin < fecha_inicio:
                print("Error: La fecha de fin no puede ser menor a la fecha de inicio.")
                continue
            
            if fecha_inicio > fecha_actual or fecha_fin > fecha_actual:
                print("Error: No puede ingresar fechas futuras. El rango debe ser menor o igual a la fecha actual.")
                continue
            
            print("Fechas validadas correctamente.\n")
            return fecha_inicio, fecha_fin
            
        except ValueError:
            print("Error: Formato de fecha inválido. Use el formato DD/MM/YYYY\n")

def obtener_pacientes_por_fecha(fecha_inicio, fecha_fin):
    
    #pacientes de ejemplo
    pacientes_todos = [
        {"nombre": "Juan Pérez", "fecha_atencion": "15-11-2025", "diagnostico": "Gripe"},
        {"nombre": "María López", "fecha_atencion": "16-11-2025", "diagnostico": "Migraña"},
        {"nombre": "Carlos Ruiz", "fecha_atencion": "17-11-2025", "diagnostico": "Dolor de espalda"},
        {"nombre": "Ana García", "fecha_atencion": "10-11-2025", "diagnostico": "Resfriado"},
        {"nombre": "Pedro Martínez", "fecha_atencion": "18-11-2025", "diagnostico": "Consulta general"},
    ]
    
    #filtrar pacientes por rango de fechas
    pacientes_filtrados = []
    
    for paciente in pacientes_todos:
        fecha_paciente = datetime.strptime(paciente["fecha_atencion"], "%d-%m-%Y")
        
        if fecha_inicio <= fecha_paciente <= fecha_fin:
            pacientes_filtrados.append(paciente)
    
    pacientes_filtrados.sort(key=lambda x: datetime.strptime(x["fecha_atencion"], "%d-%m-%Y"))
    return pacientes_filtrados


if __name__ == "__main__":
    try:
        #ingresar fechas
        fecha_inicio, fecha_fin = obtener_fechas_validadas()

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
        print("Informe generado correctamente: Pacientes_por_fecha.pdf")

    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario.")