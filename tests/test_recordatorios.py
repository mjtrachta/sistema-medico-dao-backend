"""
Tests de Recordatorios Automáticos
===================================

Tests que demuestran:
1. Observer Pattern
2. Strategy Pattern
3. Scheduler Pattern
"""

import pytest
from datetime import date, time, timedelta
from models import Turno, Notificacion
from services.recordatorio_service import RecordatorioService


class TestRecordatorioService:
    """Tests del Service de Recordatorios."""

    def test_enviar_recordatorio_manual(self, app, db_session, turno):
        """
        Test: Envía recordatorio manual de un turno.

        PATRÓN: Observer Pattern + Strategy Pattern
        - Envía email REAL a Ethereal Email
        """
        with app.app_context():
            service = RecordatorioService()

            # Turno debe estar pendiente
            turno.estado = 'pendiente'
            db_session.commit()

            # Enviar recordatorio (email real)
            result = service.enviar_recordatorio_manual(turno.id)

            assert result is True

            # Verificar que se creó la notificación
            from models import Notificacion
            notif = Notificacion.query.filter_by(turno_id=turno.id).first()
            assert notif is not None
            assert notif.estado == 'enviado'

    def test_enviar_recordatorio_turno_no_existe_falla(self, app):
        """Test: Falla si turno no existe."""
        with app.app_context():
            service = RecordatorioService()

            with pytest.raises(ValueError, match='no encontrado'):
                service.enviar_recordatorio_manual(999)

    def test_enviar_recordatorio_turno_no_pendiente_falla(self, app, db_session, paciente, medico, ubicacion):
        """Test: Solo permite enviar recordatorios de turnos pendientes."""
        with app.app_context():
            # Crear turno completado directamente
            turno_completado = Turno(
                codigo_turno='T-COMPLETADO',
                paciente_id=paciente.id,
                medico_id=medico.id,
                ubicacion_id=ubicacion.id,
                fecha=date.today() + timedelta(days=1),
                hora=time(10, 0),
                estado='completado',  # Estado completado desde el inicio
                motivo_consulta='Test'
            )
            db_session.add(turno_completado)
            db_session.commit()

            service = RecordatorioService()

            # La excepción debe contener "pendientes" en el mensaje
            with pytest.raises(ValueError) as exc_info:
                service.enviar_recordatorio_manual(turno_completado.id)
            assert 'pendientes' in str(exc_info.value).lower()

    def test_enviar_recordatorio_sin_email_falla(self, app, db_session, medico, ubicacion):
        """Test: Falla si paciente no tiene email."""
        with app.app_context():
            # Crear paciente SIN email
            from models import Paciente
            paciente_sin_email = Paciente(
                nombre='Sin',
                apellido='Email',
                tipo_documento='DNI',
                nro_documento='99999999',
                nro_historia_clinica='HC-NO-EMAIL',
                fecha_nacimiento=date(1990, 1, 1),
                genero='masculino',
                email=None,  # Sin email
                telefono='123456789'
            )
            db_session.add(paciente_sin_email)
            db_session.commit()

            # Crear turno con paciente sin email
            turno = Turno(
                codigo_turno='T-NO-EMAIL',
                paciente_id=paciente_sin_email.id,
                medico_id=medico.id,
                ubicacion_id=ubicacion.id,
                fecha=date.today() + timedelta(days=1),
                hora=time(10, 0),
                estado='pendiente'
            )
            db_session.add(turno)
            db_session.commit()

            service = RecordatorioService()

            # Debe lanzar ValueError porque no tiene email
            with pytest.raises(ValueError, match='email'):
                service.enviar_recordatorio_manual(turno.id)

    def test_enviar_recordatorios_del_dia(self, app, db_session, paciente, medico, ubicacion):
        """
        Test: Envía recordatorios de turnos del día siguiente.

        PATRÓN: Scheduler Pattern
        - Envía emails REALES a Ethereal
        """
        with app.app_context():
            # Crear turno para mañana
            turno_manana = Turno(
                codigo_turno='T-MANANA',
                paciente_id=paciente.id,
                medico_id=medico.id,
                ubicacion_id=ubicacion.id,
                fecha=date.today() + timedelta(days=1),
                hora=time(10, 0),
                estado='pendiente'
            )
            db_session.add(turno_manana)

            # Crear turno para pasado mañana (no debe enviar)
            turno_pasado = Turno(
                codigo_turno='T-PASADO',
                paciente_id=paciente.id,
                medico_id=medico.id,
                ubicacion_id=ubicacion.id,
                fecha=date.today() + timedelta(days=2),
                hora=time(11, 0),
                estado='pendiente'
            )
            db_session.add(turno_pasado)

            db_session.commit()

            service = RecordatorioService()

            # Enviar recordatorios para mañana (1 día de anticipación)
            count = service.enviar_recordatorios_del_dia(dias_anticipacion=1)

            # Debe haber enviado al menos 1 recordatorio
            assert count >= 1

            # Verificar que se creó notificación
            from models import Notificacion
            notif = Notificacion.query.filter_by(turno_id=turno_manana.id).first()
            assert notif is not None

    def test_no_envia_recordatorio_duplicado(self, app, db_session, turno):
        """
        Test: No envía recordatorio si ya se envió uno.

        PATRÓN: Specification Pattern (verificación)
        """
        with app.app_context():
            # Turno pendiente para mañana
            turno.estado = 'pendiente'
            turno.fecha = date.today() + timedelta(days=1)
            db_session.commit()

            # Crear notificación previa (recordatorio ya enviado)
            notif = Notificacion(
                turno_id=turno.id,
                tipo='email',
                destinatario=turno.paciente.email,
                mensaje='Recordatorio: ...',
                estado='enviado'
            )
            db_session.add(notif)
            db_session.commit()

            service = RecordatorioService()

            # Contar notificaciones antes
            count_before = Notificacion.query.filter_by(turno_id=turno.id).count()
            assert count_before == 1  # Solo la que creamos

            # Intentar enviar recordatorios
            service.enviar_recordatorios_del_dia(dias_anticipacion=1)

            # Contar notificaciones después - debe seguir siendo 1 (no duplica)
            count_after = Notificacion.query.filter_by(turno_id=turno.id).count()
            assert count_after == 1  # No creó duplicado

    def test_generar_mensaje_recordatorio(self, app, db_session, turno):
        """
        Test: Genera mensaje personalizado.

        PATRÓN: Template Method Pattern
        """
        with app.app_context():
            turno.fecha = date(2025, 12, 15)
            turno.hora = time(10, 30)
            db_session.commit()

            service = RecordatorioService()

            mensaje = service._generar_mensaje_recordatorio(turno)

            assert turno.paciente.nombre_completo in mensaje
            assert '15/12/2025' in mensaje
            assert '10:30' in mensaje
            assert turno.medico.nombre_completo in mensaje
            assert turno.codigo_turno in mensaje

    def test_ya_tiene_recordatorio(self, app, db_session, turno):
        """Test: Verifica si ya existe recordatorio."""
        with app.app_context():
            service = RecordatorioService()

            # Al principio no tiene
            assert service._ya_tiene_recordatorio(turno.id) is False

            # Agregar notificación
            notif = Notificacion(
                turno_id=turno.id,
                tipo='email',
                destinatario='test@test.com',
                mensaje='Recordatorio: test',
                estado='enviado'
            )
            db_session.add(notif)
            db_session.commit()

            # Ahora sí tiene
            assert service._ya_tiene_recordatorio(turno.id) is True
