"""
Tests de Reportes
=================

Tests que demuestran:
1. Service Layer Pattern
2. Query Object Pattern
3. Aggregate Pattern (SQL)
"""

import pytest
from datetime import date, time
from models import Turno, Medico, Especialidad, Paciente, HistoriaClinica, Ubicacion, HorarioMedico
from services.reporte_service import ReporteService


class TestReporteService:
    """Tests de Service de Reportes."""

    def test_turnos_por_medico(self, app, medico, paciente, ubicacion):
        """
        Test: Reporte de turnos por médico en período.

        PATRÓN: Query Object Pattern
        """
        with app.app_context():
            # Crear turnos
            turno1 = Turno(
                codigo_turno='T-TEST-001',
                paciente_id=paciente.id,
                medico_id=medico.id,
                ubicacion_id=ubicacion.id,
                fecha=date(2025, 12, 15),
                hora=time(10, 0),
                estado='completado'
            )
            turno2 = Turno(
                codigo_turno='T-TEST-002',
                paciente_id=paciente.id,
                medico_id=medico.id,
                ubicacion_id=ubicacion.id,
                fecha=date(2025, 12, 16),
                hora=time(11, 0),
                estado='cancelado'
            )

            from models.database import db
            db.session.add(turno1)
            db.session.add(turno2)
            db.session.commit()

            service = ReporteService()

            # Generar reporte
            reporte = service.turnos_por_medico(
                medico_id=medico.id,
                fecha_inicio=date(2025, 12, 1),
                fecha_fin=date(2025, 12, 31)
            )

            assert reporte['medico']['id'] == medico.id
            assert reporte['estadisticas']['total'] == 2
            assert reporte['estadisticas']['completados'] == 1
            assert reporte['estadisticas']['cancelados'] == 1
            assert len(reporte['turnos']) == 2

    def test_turnos_por_medico_no_existe_falla(self, app):
        """Test: Falla si médico no existe."""
        with app.app_context():
            service = ReporteService()

            with pytest.raises(ValueError, match='no encontrado'):
                service.turnos_por_medico(
                    medico_id=999,
                    fecha_inicio=date(2025, 12, 1),
                    fecha_fin=date(2025, 12, 31)
                )

    def test_turnos_por_especialidad(self, app, db_session, especialidad):
        """
        Test: Reporte de turnos por especialidad.

        PATRÓN: Aggregate Pattern
        """
        with app.app_context():
            # Crear médico con especialidad
            medico = Medico(
                nombre='Dr. Test',
                apellido='Prueba',
                matricula='MN-TEST',
                especialidad_id=especialidad.id
            )
            db_session.add(medico)
            db_session.commit()

            # Crear paciente
            from models import Paciente
            paciente = Paciente(
                nombre='Paciente',
                apellido='Test',
                tipo_documento='DNI',
                nro_documento='99999999',
                nro_historia_clinica='HC-TEST',
                fecha_nacimiento=date(1990, 1, 1)
            )
            db_session.add(paciente)
            db_session.commit()

            # Crear ubicación
            ubicacion = Ubicacion(
                nombre='Consultorio Test'
            )
            db_session.add(ubicacion)
            db_session.commit()

            # Crear turnos
            turno = Turno(
                codigo_turno='T-TEST-003',
                paciente_id=paciente.id,
                medico_id=medico.id,
                ubicacion_id=ubicacion.id,
                fecha=date.today(),
                hora=time(10, 0),
                estado='completado'
            )
            db_session.add(turno)
            db_session.commit()

            service = ReporteService()

            # Generar reporte
            reporte = service.turnos_por_especialidad(
                especialidad_id=especialidad.id,
                fecha_inicio=date.today(),
                fecha_fin=date.today()
            )

            assert reporte['especialidad_id'] == especialidad.id
            assert reporte['total_turnos'] >= 1
            assert len(reporte['medicos_turnos']) >= 1

    def test_pacientes_atendidos(self, app, db_session, paciente, medico, ubicacion):
        """
        Test: Reporte de pacientes atendidos.

        PATRÓN: Query Object + Specification Pattern
        """
        with app.app_context():
            # Crear turno completado
            turno = Turno(
                codigo_turno='T-TEST-004',
                paciente_id=paciente.id,
                medico_id=medico.id,
                ubicacion_id=ubicacion.id,
                fecha=date.today(),
                hora=time(10, 0),
                estado='completado'
            )
            db_session.add(turno)
            db_session.commit()

            # Crear historia clínica
            hc = HistoriaClinica(
                turno_id=turno.id,
                paciente_id=paciente.id,
                medico_id=medico.id,
                fecha_consulta=date.today(),
                diagnostico='Diagnóstico de prueba'
            )
            db_session.add(hc)
            db_session.commit()

            service = ReporteService()

            # Generar reporte
            reporte = service.pacientes_atendidos(
                fecha_inicio=date.today(),
                fecha_fin=date.today()
            )

            assert reporte['total_pacientes'] >= 1
            assert len(reporte['pacientes']) >= 1

    def test_pacientes_atendidos_filtro_medico(self, app, db_session, paciente, medico, ubicacion):
        """Test: Filtra pacientes atendidos por médico."""
        with app.app_context():
            # Crear turno completado
            turno = Turno(
                codigo_turno='T-TEST-005',
                paciente_id=paciente.id,
                medico_id=medico.id,
                ubicacion_id=ubicacion.id,
                fecha=date.today(),
                hora=time(10, 0),
                estado='completado'
            )
            db_session.add(turno)
            db_session.commit()

            # Crear historia clínica
            hc = HistoriaClinica(
                turno_id=turno.id,
                paciente_id=paciente.id,
                medico_id=medico.id,
                fecha_consulta=date.today(),
                diagnostico='Diagnóstico de prueba'
            )
            db_session.add(hc)
            db_session.commit()

            service = ReporteService()

            # Generar reporte filtrado
            reporte = service.pacientes_atendidos(
                fecha_inicio=date.today(),
                fecha_fin=date.today(),
                medico_id=medico.id
            )

            assert reporte['filtros']['medico_id'] == medico.id
            assert reporte['total_pacientes'] >= 1

    def test_estadisticas_asistencia(self, app, db_session, paciente, medico, ubicacion):
        """
        Test: Estadísticas de asistencia vs inasistencias.

        PATRÓN: Aggregate Pattern
        - Datos procesados para gráficos
        """
        with app.app_context():
            # Crear turnos con diferentes estados
            turno1 = Turno(
                codigo_turno='T-TEST-006',
                paciente_id=paciente.id,
                medico_id=medico.id,
                ubicacion_id=ubicacion.id,
                fecha=date.today(),
                hora=time(10, 0),
                estado='completado'
            )
            turno2 = Turno(
                codigo_turno='T-TEST-007',
                paciente_id=paciente.id,
                medico_id=medico.id,
                ubicacion_id=ubicacion.id,
                fecha=date.today(),
                hora=time(11, 0),
                estado='cancelado'
            )
            turno3 = Turno(
                codigo_turno='T-TEST-008',
                paciente_id=paciente.id,
                medico_id=medico.id,
                ubicacion_id=ubicacion.id,
                fecha=date.today(),
                hora=time(12, 0),
                estado='pendiente'
            )

            db_session.add_all([turno1, turno2, turno3])
            db_session.commit()

            service = ReporteService()

            # Generar reporte
            reporte = service.estadisticas_asistencia(
                fecha_inicio=date.today(),
                fecha_fin=date.today()
            )

            assert reporte['resumen']['total_turnos'] >= 3
            assert reporte['resumen']['completados'] >= 1
            assert reporte['resumen']['cancelados'] >= 1
            assert reporte['resumen']['pendientes'] >= 1
            assert reporte['resumen']['tasa_asistencia'] >= 0
            assert reporte['resumen']['tasa_cancelacion'] >= 0

    def test_estadisticas_asistencia_sin_datos(self, app):
        """Test: Reporte sin datos retorna estructura vacía."""
        with app.app_context():
            service = ReporteService()

            reporte = service.estadisticas_asistencia(
                fecha_inicio=date(2020, 1, 1),
                fecha_fin=date(2020, 1, 2)
            )

            assert reporte['resumen']['total_turnos'] == 0
            assert reporte['resumen']['tasa_asistencia'] == 0.0
            assert len(reporte['por_mes']) == 0

    def test_estadisticas_asistencia_filtro_medico(self, app, db_session, paciente, medico, ubicacion):
        """Test: Filtra estadísticas por médico."""
        with app.app_context():
            # Crear turno
            turno = Turno(
                codigo_turno='T-TEST-009',
                paciente_id=paciente.id,
                medico_id=medico.id,
                ubicacion_id=ubicacion.id,
                fecha=date.today(),
                hora=time(10, 0),
                estado='completado'
            )
            db_session.add(turno)
            db_session.commit()

            service = ReporteService()

            # Generar reporte filtrado
            reporte = service.estadisticas_asistencia(
                fecha_inicio=date.today(),
                fecha_fin=date.today(),
                medico_id=medico.id
            )

            assert reporte['resumen']['total_turnos'] >= 1
