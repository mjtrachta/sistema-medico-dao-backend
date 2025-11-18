"""
Testing endpoints - Solo para desarrollo
========================================
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date, time
from strategies.notification_strategy import NotificationStrategyFactory
import os

testing_bp = Blueprint('testing', __name__, url_prefix='/api/testing')

def get_email_config():
    """Configuración de email desde .env"""
    return {
        'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'port': int(os.getenv('SMTP_PORT', 587)),
        'username': os.getenv('SMTP_USERNAME', ''),
        'password': os.getenv('SMTP_PASSWORD', ''),
        'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
    }

def crear_turno_ficticio(email_destinatario):
    """Crea turno mock para testing"""
    class MockEspecialidad:
        nombre = "Cardiología"
    
    class MockUbicacion:
        nombre = "Clínica Centro"
        direccion = "Av. Principal 123"
        telefono = "(0351) 123-4567"
    
    class MockMedico:
        nombre_completo = "Dr. Juan Pérez"
        especialidad = MockEspecialidad()
    
    class MockPaciente:
        nombre_completo = "Usuario Test"
        email = email_destinatario
    
    class MockTurno:
        id = 999999
        codigo_turno = f"TEST-{datetime.now().strftime('%Y%m%d')}-001"
        fecha = date(2024, 12, 25)
        hora = time(14, 30)
        estado = "confirmado"
        motivo_consulta = "Consulta de prueba"
        medico = MockMedico()
        paciente = MockPaciente()
        ubicacion = MockUbicacion()
    
    return MockTurno()

def construir_mensaje_turno_creado(turno):
    """Template HTML para turno creado"""
    return f"""
    <p>Estimado/a <strong>{turno.paciente.nombre_completo}</strong>,</p>
    <p>Su turno médico ha sido confirmado:</p>
    <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Código:</strong> {turno.codigo_turno}</p>
        <p><strong>Médico:</strong> {turno.medico.nombre_completo}</p>
        <p><strong>Especialidad:</strong> {turno.medico.especialidad.nombre}</p>
        <p><strong>Fecha:</strong> {turno.fecha.strftime('%d/%m/%Y')}</p>
        <p><strong>Hora:</strong> {turno.hora.strftime('%H:%M')}</p>
        <p><strong>Ubicación:</strong> {turno.ubicacion.nombre}</p>
    </div>
    <p>Saludos cordiales,<br><strong>Sistema de Turnos Médicos</strong></p>
    """

@testing_bp.route('/notificacion', methods=['POST'])
def test_notification():
    """
    Prueba envío de notificación
    Body: {"destinatario": "email@gmail.com", "tipo": "turno_creado"}
    """
    try:
        data = request.get_json()
        if not data or 'destinatario' not in data:
            return jsonify({'error': 'Campo destinatario requerido'}), 400
        
        destinatario = data['destinatario']
        tipo = data.get('tipo', 'turno_creado')
        
        # Configurar email
        config = {'email': get_email_config()}
        strategy = NotificationStrategyFactory.create('email', config['email'])
        
        # Crear turno ficticio y enviar
        turno_ficticio = crear_turno_ficticio(destinatario)
        asunto = "Turno Médico Confirmado"
        mensaje_html = construir_mensaje_turno_creado(turno_ficticio)
        
        exito = strategy.send(destinatario, asunto, mensaje_html)
        
        if exito:
            return jsonify({
                'success': True,
                'message': 'Notificación enviada',
                'destinatario': destinatario,
                'codigo_turno': turno_ficticio.codigo_turno
            }), 200
        else:
            return jsonify({'error': 'Error enviando email'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@testing_bp.route('/crear-turno', methods=['POST'])
def crear_turno_sin_jwt():
    """
    Crea turno SIN JWT y SIN BD - Solo envía notificación
    
    Body (igual que endpoint original):
    {
        "medico_id": 1,
        "ubicacion_id": 1, 
        "fecha": "2024-12-25",
        "hora": "10:30",
        "duracion_min": 30,
        "motivo_consulta": "Consulta de prueba",
        "email_paciente": "tu-email@gmail.com"
    }
    """
    try:
        data = request.get_json()
        
        # Validar campos requeridos (igual que original)
        required_fields = ['medico_id', 'ubicacion_id', 'fecha', 'hora', 'email_paciente']
        if not all(k in data for k in required_fields):
            return jsonify({'error': 'Faltan campos requeridos', 'required': required_fields}), 400

        # Parsear fecha y hora (igual que original)
        try:
            fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
            hora = datetime.strptime(data['hora'], '%H:%M').time()
        except ValueError as e:
            return jsonify({'error': f'Error en formato de fecha/hora: {str(e)}'}), 400

        email_paciente = data['email_paciente']
        
        # Crear turno ficticio con datos del request
        turno_ficticio = crear_turno_ficticio(email_paciente)
        turno_ficticio.fecha = fecha
        turno_ficticio.hora = hora
        turno_ficticio.motivo_consulta = data.get('motivo_consulta', 'Consulta')
        turno_ficticio.codigo_turno = f"TEST-{fecha.strftime('%Y%m%d')}-{hora.strftime('%H%M')}"
        
        # Configurar y enviar notificación
        config = {'email': get_email_config()}
        strategy = NotificationStrategyFactory.create('email', config['email'])
        
        asunto = "Turno Médico Confirmado"
        mensaje_html = construir_mensaje_turno_creado(turno_ficticio)
        
        exito = strategy.send(email_paciente, asunto, mensaje_html)
        
        if exito:
            return jsonify({
                'success': True,
                'message': 'Turno creado (ficticio) y notificación enviada',
                'turno': {
                    'codigo_turno': turno_ficticio.codigo_turno,
                    'fecha': fecha.isoformat(),
                    'hora': hora.strftime('%H:%M'),
                    'motivo_consulta': turno_ficticio.motivo_consulta,
                    'email_paciente': email_paciente
                }
            }), 201
        else:
            return jsonify({'error': 'Error enviando notificación'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500