"""
Servicio de Recordatorios Automáticos
======================================

PATRÓN: Observer Pattern + Strategy Pattern + Scheduler Pattern
- Envía recordatorios automáticos de turnos
"""

from datetime import date, timedelta
from typing import List
from flask import current_app
from models import Turno, Notificacion
from models.database import db
from services.notification_service import NotificationService
from strategies.notification_strategy import EmailStrategy


class RecordatorioService:
    """
    Servicio para enviar recordatorios automáticos de turnos.

    PATRÓN: Observer Pattern
    - Notifica a pacientes sobre turnos próximos
    - Usa Strategy Pattern para diferentes canales de notificación
    """

    def __init__(self, notification_service=None):
        """
        Constructor con Dependency Injection.

        PATRÓN: Dependency Injection
        """
        self.notification_service = notification_service or NotificationService()

    def enviar_recordatorios_del_dia(self, dias_anticipacion: int = 1) -> int:
        """
        Envía recordatorios de turnos programados para dentro de N días.

        PATRÓN: Business Logic Encapsulation
        - Encuentra turnos próximos
        - Filtra los que ya tienen recordatorio
        - Envía notificación
        - Registra envío

        Args:
            dias_anticipacion: Días de anticipación para el recordatorio

        Returns:
            int: Cantidad de recordatorios enviados

        Example:
            # Enviar recordatorios de turnos de mañana
            service.enviar_recordatorios_del_dia(dias_anticipacion=1)
        """
        # Calcular fecha objetivo
        fecha_objetivo = date.today() + timedelta(days=dias_anticipacion)

        # Buscar turnos pendientes para esa fecha
        turnos = Turno.query.filter(
            Turno.fecha == fecha_objetivo,
            Turno.estado == 'pendiente'
        ).all()

        recordatorios_enviados = 0

        for turno in turnos:
            try:
                # Verificar si ya se envió recordatorio
                if self._ya_tiene_recordatorio(turno.id):
                    continue

                # Enviar recordatorio
                self._enviar_recordatorio_turno(turno)
                recordatorios_enviados += 1

            except Exception as e:
                print(f"Error enviando recordatorio para turno {turno.id}: {e}")
                # Continuar con el siguiente turno

        return recordatorios_enviados

    def _ya_tiene_recordatorio(self, turno_id: int) -> bool:
        """
        Verifica si ya se envió recordatorio para un turno.

        PATRÓN: Specification Pattern
        """
        return Notificacion.query.filter(
            Notificacion.turno_id == turno_id,
            Notificacion.tipo == 'email',
            Notificacion.mensaje.like('%Recordatorio%')
        ).count() > 0

    def _enviar_recordatorio_turno(self, turno: Turno) -> None:
        """
        Envía recordatorio individual de un turno.

        PATRÓN: Strategy Pattern
        - Usa EmailStrategy para enviar
        - Registra en tabla de notificaciones
        """
        if not turno.paciente or not turno.paciente.email:
            raise ValueError(f"Paciente del turno {turno.id} no tiene email")

        # Preparar mensaje
        asunto = f"Recordatorio: Turno Médico - {turno.fecha}"
        mensaje = self._generar_mensaje_recordatorio(turno)

        # Obtener configuración SMTP desde Flask
        smtp_config = {
            'server': current_app.config.get('MAIL_SERVER'),
            'port': current_app.config.get('MAIL_PORT'),
            'username': current_app.config.get('MAIL_USERNAME'),
            'password': current_app.config.get('MAIL_PASSWORD'),
            'use_tls': current_app.config.get('MAIL_USE_TLS')
        }

        # Crear strategy de email con configuración
        email_strategy = EmailStrategy(smtp_config)

        # Enviar email
        email_strategy.send(
            destinatario=turno.paciente.email,
            asunto=asunto,
            mensaje=mensaje
        )

        # Registrar notificación
        notificacion = Notificacion(
            turno_id=turno.id,
            tipo='email',
            destinatario=turno.paciente.email,
            mensaje=mensaje,
            estado='enviado'
        )
        db.session.add(notificacion)
        db.session.commit()

    def _generar_mensaje_recordatorio(self, turno: Turno) -> str:
        """
        Genera mensaje personalizado de recordatorio.

        PATRÓN: Template Method
        - Formato estándar de mensaje
        """
        return f"""
        Estimado/a {turno.paciente.nombre_completo},

        Le recordamos que tiene un turno médico programado:

        📅 Fecha: {turno.fecha.strftime('%d/%m/%Y')}
        🕐 Hora: {turno.hora.strftime('%H:%M')}
        👨‍⚕️ Médico: Dr/a. {turno.medico.nombre_completo}
        🏥 Ubicación: {turno.ubicacion.nombre if turno.ubicacion else 'No especificada'}

        Código de turno: {turno.codigo_turno}

        Si no puede asistir, por favor comuníquese con anticipación para cancelar el turno.

        Saludos cordiales,
        Sistema de Turnos Médicos
        """

    def enviar_recordatorio_manual(self, turno_id: int) -> bool:
        """
        Envía recordatorio manual de un turno específico.

        PATRÓN: Command Pattern (delegación de acción)

        Returns:
            bool: True si se envió correctamente
        """
        turno = Turno.query.get(turno_id)
        if not turno:
            raise ValueError(f"Turno {turno_id} no encontrado")

        if turno.estado != 'pendiente':
            raise ValueError(f"Solo se pueden enviar recordatorios de turnos pendientes")

        try:
            self._enviar_recordatorio_turno(turno)
            return True
        except Exception as e:
            raise ValueError(f"Error enviando recordatorio: {str(e)}")


# ==========================================
# SCHEDULER (Ejecución automática)
# ==========================================

"""
Para ejecutar recordatorios automáticamente, puedes usar:

1. Cron job (Linux/Mac):
   ```bash
   # Ejecutar todos los días a las 9:00 AM
   0 9 * * * cd /path/to/backend && venv/bin/python -c "from services.recordatorio_service import enviar_recordatorios_automaticos; enviar_recordatorios_automaticos()"
   ```

2. APScheduler (Python):
   ```python
   from apscheduler.schedulers.background import BackgroundScheduler

   scheduler = BackgroundScheduler()
   scheduler.add_job(
       func=enviar_recordatorios_automaticos,
       trigger="cron",
       hour=9,
       minute=0
   )
   scheduler.start()
   ```

3. Celery (producción):
   ```python
   @celery.task
   def enviar_recordatorios_task():
       service = RecordatorioService()
       service.enviar_recordatorios_del_dia(dias_anticipacion=1)
   ```
"""


def enviar_recordatorios_automaticos():
    """
    Función helper para ejecutar desde scheduler/cron.

    PATRÓN: Facade Pattern
    - Simplifica ejecución desde scripts externos
    """
    from app import create_app

    app = create_app()
    with app.app_context():
        service = RecordatorioService()

        # Enviar recordatorios para mañana
        count = service.enviar_recordatorios_del_dia(dias_anticipacion=1)

        print(f"Recordatorios enviados: {count}")
        return count
