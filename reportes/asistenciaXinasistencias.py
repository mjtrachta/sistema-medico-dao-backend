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

def generar_reporte_asistencia(asistencias=45, inasistencias=15):

    documento = SimpleDocTemplate(
        "Asistencia_vs_Inasistencias.pdf",
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
    
    # Fecha
    fecha_actual = datetime.now().strftime("%d de %B de %Y")
    elementos.append(Paragraph(f"Generado: {fecha_actual}", estilos['Normal']))
    elementos.append(Spacer(1, 0.2*inch))
    
    # Subtítulo
    elementos.append(Paragraph("Pacientes: Asistencias vs Inasistencias", subtitulo_style))
    elementos.append(Spacer(1, 0.2*inch))
    
    # Datos estadísticos
    total = asistencias + inasistencias
    pct_asistencias = (asistencias / total * 100) if total > 0 else 0
    pct_inasistencias = (inasistencias / total * 100) if total > 0 else 0
    
    stats_text = f"""
    <b>Total de Pacientes:</b> {total}<br/>
    <b>Asistencias:</b> {asistencias} ({pct_asistencias:.1f}%)<br/>
    <b>Inasistencias:</b> {inasistencias} ({pct_inasistencias:.1f}%)
    """
    elementos.append(Paragraph(stats_text, estilos['Normal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # Gráfico de pastel
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Gráfico 1: Pastel
    data = [asistencias, inasistencias]
    labels = ['Asistencias', 'Inasistencias']
    colors = ['#2ecc71', '#e74c3c']
    
    ax1.pie(data, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
    ax1.set_title('Distribución de Asistencias', fontsize=12, fontweight='bold')
    
    # Gráfico 2: Barras
    ax2.bar(labels, data, color=colors, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Cantidad de Pacientes', fontsize=10)
    ax2.set_title('Comparativa', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Guardar gráfico en buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    # Agregar imagen al PDF
    elementos.append(Image(buffer, width=6*inch, height=2.5*inch))
    
    documento.build(elementos)
    print("Informe generado correctamente: Asistencia_vs_Inasistencias.pdf")

if __name__ == "__main__":
    generar_reporte_asistencia(asistencias=45, inasistencias=15)