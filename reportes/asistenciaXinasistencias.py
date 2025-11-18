from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER
import matplotlib.pyplot as plt
import matplotlib
from io import BytesIO
from datetime import datetime

matplotlib.use('Agg')

def buscar_paciente(nombre_paciente):
    #pacientes hardcodeados
    pacientes_datos = {
        "juan": {"asistencias": 45, "inasistencias": 15},
        "maria": {"asistencias": 38, "inasistencias": 22},
        "pedro": {"asistencias": 50, "inasistencias": 10},
        "carlos": {"asistencias": 42, "inasistencias": 18},
        "ana": {"asistencias": 55, "inasistencias": 5},
        "jose": {"asistencias": 35, "inasistencias": 25},
        "carmen": {"asistencias": 48, "inasistencias": 12},
        "diego": {"asistencias": 40, "inasistencias": 20},
        "lucia": {"asistencias": 60, "inasistencias": 0},
        "miguel": {"asistencias": 30, "inasistencias": 30},
        "sofia": {"asistencias": 52, "inasistencias": 8},
        "francisco": {"asistencias": 46, "inasistencias": 14},
        "rosa": {"asistencias": 41, "inasistencias": 19},
        "manuel": {"asistencias": 58, "inasistencias": 2},
        "elena": {"asistencias": 36, "inasistencias": 24}
    }
    
    nombre_lower = nombre_paciente.lower().strip()
    return pacientes_datos.get(nombre_lower, None)

def generar_reporte_asistencia(nombre_paciente, asistencias=45, inasistencias=15):

    documento = SimpleDocTemplate(
        f"Asistencia_{nombre_paciente}.pdf",
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    estilos = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=estilos['Heading1'],
        fontSize=24,
        textColor='#1f4788',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    subtitulo_style = ParagraphStyle(
        'CustomSubtitle',
        parent=estilos['Heading2'],
        fontSize=14,
        textColor='#4a4a4a',
        spaceAfter=20,
        alignment=TA_CENTER
    )

    elementos = []

    elementos.append(Paragraph("INFORME DE ASISTENCIAS", titulo_style))
    elementos.append(Spacer(1, 0.3*inch))
    
    elementos.append(Paragraph(f"<b>Paciente:</b> {nombre_paciente}", estilos['Normal']))
    
    fecha_actual = datetime.now().strftime("%d de %B de %Y")
    elementos.append(Paragraph(f"<b>Generado:</b> {fecha_actual}", estilos['Normal']))
    elementos.append(Spacer(1, 0.2*inch))
    
    #subtitulo
    elementos.append(Paragraph("Asistencias vs Inasistencias", subtitulo_style))
    elementos.append(Spacer(1, 0.2*inch))
    
    total = asistencias + inasistencias
    pct_asistencias = (asistencias / total * 100) if total > 0 else 0
    pct_inasistencias = (inasistencias / total * 100) if total > 0 else 0
    
    stats_text = f"""
    <b>Total de Turnos:</b> {total}<br/>
    <b>Asistencias:</b> {asistencias} ({pct_asistencias:.1f}%)<br/>
    <b>Inasistencias:</b> {inasistencias} ({pct_inasistencias:.1f}%)
    """
    elementos.append(Paragraph(stats_text, estilos['Normal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    #grafico de torta
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    data = [asistencias, inasistencias]
    labels = ['Asistencias', 'Inasistencias']
    colors = ['#2ecc71', '#e74c3c']
    
    ax1.pie(data, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
    ax1.set_title('Distribución de Asistencias', fontsize=12, fontweight='bold')
    
    #grafico de barras
    ax2.bar(labels, data, color=colors, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Cantidad de Turnos', fontsize=10)
    ax2.set_title('Comparativa', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    #agreagar imagen a PDF
    elementos.append(Image(buffer, width=6*inch, height=2.5*inch))
    
    documento.build(elementos)
    print(f"Informe generado: Asistencia_{nombre_paciente}.pdf")

def main():
    
    nombre = input("\nIngresa el nombre del paciente: ").strip()
    
    if not nombre:
        print("Por favor ingresa un nombre válido.")
        return
    
    datos = buscar_paciente(nombre)
    
    if datos is None:
        print(f"No se encontró al paciente: {nombre}")
        return
    
    asistencias = datos["asistencias"]
    inasistencias = datos["inasistencias"]
    
    print(f"\nPaciente encontrado:")
    print(f"  - Asistencias: {asistencias}")
    print(f"  - Inasistencias: {inasistencias}")
    print(f"\nGenerando reporte...")
    
    generar_reporte_asistencia(nombre, asistencias, inasistencias)

if __name__ == "__main__":
    main()