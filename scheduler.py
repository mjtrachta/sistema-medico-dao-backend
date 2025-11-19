"""
Configuración de Tareas Programadas
====================================

PATRÓN: Scheduler Pattern
- Ejecuta tareas automáticamente en horarios específicos
- Envío de recordatorios de turnos
- Limpieza de datos obsoletos
- Generación de reportes periódicos

APScheduler:
- BackgroundScheduler: Ejecuta en segundo plano sin bloquear Flask
- CronTrigger: Define horarios de ejecución (estilo cron)
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask
import logging

# Configurar logging para el scheduler
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.INFO)

# Instancia global del scheduler
scheduler = BackgroundScheduler()


def enviar_recordatorios_job():
    """
    Job que envía recordatorios de turnos del día siguiente.

    Se ejecuta diariamente a las 9:00 AM.
    Envía emails a pacientes con turnos programados para mañana.
    """
    from services.recordatorio_service import RecordatorioService
    from app import create_app

    # Crear contexto de aplicación para acceder a la base de datos
    app = create_app()
    with app.app_context():
        try:
            service = RecordatorioService()
            count = service.enviar_recordatorios_del_dia(dias_anticipacion=1)
            print(f"✅ Recordatorios enviados: {count}")
            return count
        except Exception as e:
            print(f"❌ Error enviando recordatorios: {e}")
            raise


def limpiar_notificaciones_antiguas_job():
    """
    Job que limpia notificaciones antiguas.

    Se ejecuta semanalmente los domingos a las 2:00 AM.
    Elimina notificaciones más antiguas de 90 días.
    """
    from models import Notificacion
    from models.database import db
    from datetime import datetime, timedelta
    from app import create_app

    app = create_app()
    with app.app_context():
        try:
            fecha_limite = datetime.now() - timedelta(days=90)

            count = Notificacion.query.filter(
                Notificacion.enviado_en < fecha_limite
            ).delete()

            db.session.commit()
            print(f"✅ Notificaciones antiguas eliminadas: {count}")
            return count
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error limpiando notificaciones: {e}")
            raise


def init_scheduler(app: Flask):
    """
    Inicializa y configura el scheduler con la aplicación Flask.

    Args:
        app: Instancia de Flask

    Jobs configurados:
    - enviar_recordatorios: Diario a las 9:00 AM
    - limpiar_notificaciones: Semanal, domingos a las 2:00 AM
    """
    # Verificar si el scheduler está habilitado en config
    if not app.config.get('SCHEDULER_ENABLED', True):
        print("⚠️ Scheduler deshabilitado por configuración")
        return

    # Verificar si ya está corriendo (evitar duplicados)
    if scheduler.running:
        print("⚠️ Scheduler ya está corriendo")
        return

    # ==========================================
    # JOB 1: Recordatorios de Turnos
    # ==========================================
    # Se ejecuta todos los días a las 9:00 AM
    scheduler.add_job(
        func=enviar_recordatorios_job,
        trigger=CronTrigger(hour=9, minute=0),
        id='enviar_recordatorios',
        name='Envío de recordatorios de turnos',
        replace_existing=True,
        misfire_grace_time=3600  # 1 hora de gracia si el servidor estaba apagado
    )

    # ==========================================
    # JOB 2: Limpieza de Notificaciones Antiguas
    # ==========================================
    # Se ejecuta los domingos a las 2:00 AM
    scheduler.add_job(
        func=limpiar_notificaciones_antiguas_job,
        trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
        id='limpiar_notificaciones',
        name='Limpieza de notificaciones antiguas',
        replace_existing=True,
        misfire_grace_time=7200  # 2 horas de gracia
    )

    # Iniciar el scheduler
    scheduler.start()

    print("=" * 60)
    print("📅 SCHEDULER INICIADO")
    print("=" * 60)
    print("Jobs configurados:")
    for job in scheduler.get_jobs():
        print(f"  • {job.name}")
        print(f"    ID: {job.id}")
        print(f"    Próxima ejecución: {job.next_run_time}")
        print()
    print("=" * 60)

    # Registrar shutdown cuando Flask se cierre
    import atexit
    atexit.register(lambda: shutdown_scheduler())


def shutdown_scheduler():
    """
    Detiene el scheduler de forma segura.

    Se llama automáticamente cuando la aplicación Flask se cierra.
    """
    if scheduler.running:
        scheduler.shutdown()
        print("🛑 Scheduler detenido correctamente")


def trigger_job_now(job_id: str):
    """
    Ejecuta un job manualmente de forma inmediata.

    Útil para testing o ejecución manual desde admin.

    Args:
        job_id: ID del job ('enviar_recordatorios' o 'limpiar_notificaciones')

    Returns:
        bool: True si se ejecutó correctamente

    Example:
        from scheduler import trigger_job_now
        trigger_job_now('enviar_recordatorios')
    """
    try:
        job = scheduler.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} no encontrado")

        print(f"🚀 Ejecutando job '{job.name}' manualmente...")
        job.func()
        return True
    except Exception as e:
        print(f"❌ Error ejecutando job: {e}")
        return False


# ==========================================
# FUNCIONES DE UTILIDAD
# ==========================================

def list_jobs():
    """
    Lista todos los jobs configurados.

    Returns:
        list: Lista de diccionarios con información de jobs
    """
    return [
        {
            'id': job.id,
            'name': job.name,
            'next_run': str(job.next_run_time),
            'trigger': str(job.trigger)
        }
        for job in scheduler.get_jobs()
    ]


def pause_job(job_id: str):
    """Pausa un job específico."""
    scheduler.pause_job(job_id)
    print(f"⏸️ Job '{job_id}' pausado")


def resume_job(job_id: str):
    """Reanuda un job pausado."""
    scheduler.resume_job(job_id)
    print(f"▶️ Job '{job_id}' reanudado")


def remove_job(job_id: str):
    """Elimina un job del scheduler."""
    scheduler.remove_job(job_id)
    print(f"🗑️ Job '{job_id}' eliminado")
