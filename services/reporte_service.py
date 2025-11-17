"""
Servicio de Reportes
====================

PATRÓN: Service Layer + Strategy Pattern
- Encapsula lógica de generación de reportes
"""

from typing import List, Dict, Optional
from datetime import date, datetime
from sqlalchemy import func, and_
from models import Turno, Medico, Especialidad, Paciente, HistoriaClinica
from models.database import db


class ReporteService:
    """
    Servicio para generar reportes estadísticos.

    PATRÓN: Service Layer
    - Encapsula queries complejas
    - Retorna datos procesados listos para visualización
    """

    def turnos_por_medico(
        self,
        medico_id: int,
        fecha_inicio: date,
        fecha_fin: date
    ) -> Dict:
        """
        Reporte: Turnos de un médico en un período.

        PATRÓN: Query Object Pattern
        - Encapsula consulta compleja

        Returns:
            {
                'medico': {...},
                'periodo': {'inicio': ..., 'fin': ...},
                'turnos': [...],
                'estadisticas': {
                    'total': int,
                    'completados': int,
                    'cancelados': int,
                    'pendientes': int
                }
            }
        """
        # Obtener médico
        medico = Medico.query.get(medico_id)
        if not medico:
            raise ValueError(f"Médico {medico_id} no encontrado")

        # Consultar turnos del período
        turnos = Turno.query.filter(
            and_(
                Turno.medico_id == medico_id,
                Turno.fecha >= fecha_inicio,
                Turno.fecha <= fecha_fin
            )
        ).order_by(Turno.fecha, Turno.hora).all()

        # Calcular estadísticas
        total = len(turnos)
        completados = sum(1 for t in turnos if t.estado == 'completado')
        cancelados = sum(1 for t in turnos if t.estado == 'cancelado')
        pendientes = sum(1 for t in turnos if t.estado == 'pendiente')
        confirmados = sum(1 for t in turnos if t.estado == 'confirmado')
        ausentes = sum(1 for t in turnos if t.estado == 'ausente')

        # Serializar turnos
        turnos_data = []
        for t in turnos:
            turnos_data.append({
                'id': t.id,
                'codigo_turno': t.codigo_turno,
                'fecha': t.fecha.isoformat(),
                'hora': t.hora.strftime('%H:%M'),
                'estado': t.estado,
                'paciente': {
                    'id': t.paciente.id,
                    'nombre_completo': t.paciente.nombre_completo
                } if t.paciente else None,
                'motivo_consulta': t.motivo_consulta
            })

        return {
            'medico_id': medico.id,
            'medico_nombre': medico.nombre_completo,
            'fecha_inicio': fecha_inicio.isoformat(),
            'fecha_fin': fecha_fin.isoformat(),
            'total_turnos': total,
            'confirmados': confirmados,
            'completados': completados,
            'cancelados': cancelados,
            'ausentes': ausentes,
            'medico': {
                'id': medico.id,
                'nombre_completo': medico.nombre_completo,
                'matricula': medico.matricula
            },
            'periodo': {
                'inicio': fecha_inicio.isoformat(),
                'fin': fecha_fin.isoformat()
            },
            'turnos': turnos_data,
            'estadisticas': {
                'total': total,
                'completados': completados,
                'cancelados': cancelados,
                'pendientes': pendientes,
                'confirmados': confirmados,
                'ausentes': ausentes
            }
        }

    def turnos_por_especialidad(
        self,
        especialidad_id: int,
        fecha_inicio: date,
        fecha_fin: date
    ) -> Dict:
        """
        Reporte: Cantidad de turnos por especialidad con detalle de médicos.

        PATRÓN: Aggregate Pattern
        - Usa SQL aggregates para estadísticas

        Returns:
            {
                'especialidad_id': int,
                'especialidad_nombre': str,
                'total_turnos': int,
                'total_medicos': int,
                'medicos_turnos': [...]
            }
        """
        # Obtener especialidad
        especialidad = Especialidad.query.get(especialidad_id)
        if not especialidad:
            raise ValueError(f"Especialidad {especialidad_id} no encontrada")

        # Query para obtener turnos por médico de la especialidad
        from sqlalchemy import case
        query = db.session.query(
            Medico.id,
            Medico.nombre,
            Medico.apellido,
            func.count(Turno.id).label('total')
        ).join(
            Turno, Medico.id == Turno.medico_id
        ).filter(
            and_(
                Medico.especialidad_id == especialidad_id,
                Turno.fecha >= fecha_inicio,
                Turno.fecha <= fecha_fin
            )
        ).group_by(
            Medico.id,
            Medico.nombre,
            Medico.apellido
        ).order_by(func.count(Turno.id).desc())

        results = query.all()

        # Formatear resultados
        medicos_turnos = []
        total_turnos = 0
        for r in results:
            medicos_turnos.append({
                'medico_id': r.id,
                'medico_nombre': f"{r.nombre} {r.apellido}",
                'total': r.total or 0
            })
            total_turnos += (r.total or 0)

        return {
            'especialidad_id': especialidad.id,
            'especialidad_nombre': especialidad.nombre,
            'fecha_inicio': fecha_inicio.isoformat(),
            'fecha_fin': fecha_fin.isoformat(),
            'total_turnos': total_turnos,
            'total_medicos': len(medicos_turnos),
            'medicos_turnos': medicos_turnos,
            'especialidad': {
                'id': especialidad.id,
                'nombre': especialidad.nombre
            }
        }

    def pacientes_atendidos(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        medico_id: int = None,
        especialidad_id: int = None
    ) -> Dict:
        """
        Reporte: Pacientes atendidos en un rango de fechas.

        PATRÓN: Query Object + Specification Pattern

        Returns:
            {
                'periodo': {...},
                'filtros': {...},
                'total_pacientes': int,
                'pacientes': [...]
            }
        """
        # Query base de historias clínicas (turnos completados)
        query = db.session.query(
            Paciente.id,
            Paciente.nombre,
            Paciente.apellido,
            Paciente.nro_historia_clinica,
            func.count(HistoriaClinica.id).label('consultas'),
            func.max(HistoriaClinica.fecha_consulta).label('ultima_consulta')
        ).join(
            HistoriaClinica, Paciente.id == HistoriaClinica.paciente_id
        ).filter(
            and_(
                HistoriaClinica.fecha_consulta >= fecha_inicio,
                HistoriaClinica.fecha_consulta <= fecha_fin
            )
        )

        # Aplicar filtros opcionales
        if medico_id:
            query = query.filter(HistoriaClinica.medico_id == medico_id)
        if especialidad_id:
            query = query.join(Medico, HistoriaClinica.medico_id == Medico.id)\
                         .filter(Medico.especialidad_id == especialidad_id)

        # Agrupar por paciente
        query = query.group_by(
            Paciente.id,
            Paciente.nombre,
            Paciente.apellido,
            Paciente.nro_historia_clinica
        ).order_by(func.count(HistoriaClinica.id).desc())

        results = query.all()

        # Formatear
        pacientes = []
        for r in results:
            pacientes.append({
                'paciente_id': r.id,
                'id': r.id,
                'paciente_nombre': f'{r.nombre} {r.apellido}',
                'nombre_completo': f'{r.nombre} {r.apellido}',
                'nro_historia_clinica': r.nro_historia_clinica,
                'total_consultas': r.consultas,
                'consultas': r.consultas,
                'ultima_consulta': r.ultima_consulta.isoformat() if r.ultima_consulta else None
            })

        return {
            'fecha_inicio': fecha_inicio.isoformat(),
            'fecha_fin': fecha_fin.isoformat(),
            'periodo': {
                'inicio': fecha_inicio.isoformat(),
                'fin': fecha_fin.isoformat()
            },
            'filtros': {
                'medico_id': medico_id,
                'especialidad_id': especialidad_id
            },
            'total_pacientes': len(pacientes),
            'pacientes': pacientes
        }

    def estadisticas_asistencia(
        self,
        fecha_inicio: date = None,
        fecha_fin: date = None,
        medico_id: int = None
    ) -> Dict:
        """
        Reporte estadístico: Asistencia vs Inasistencias.

        PATRÓN: Aggregate Pattern
        - Datos procesados para gráficos

        Returns:
            {
                'periodo': {...},
                'resumen': {
                    'total_turnos': int,
                    'completados': int,
                    'cancelados': int,
                    'pendientes': int,
                    'tasa_asistencia': float,
                    'tasa_cancelacion': float
                },
                'por_mes': [...]  # Para gráfico temporal
            }
        """
        # Query base
        query = Turno.query

        # Filtros
        conditions = []
        if fecha_inicio:
            conditions.append(Turno.fecha >= fecha_inicio)
        if fecha_fin:
            conditions.append(Turno.fecha <= fecha_fin)
        if medico_id:
            conditions.append(Turno.medico_id == medico_id)

        if conditions:
            query = query.filter(and_(*conditions))

        # Obtener todos los turnos
        turnos = query.all()
        total = len(turnos)

        if total == 0:
            return {
                'fecha_inicio': fecha_inicio.isoformat() if fecha_inicio else None,
                'fecha_fin': fecha_fin.isoformat() if fecha_fin else None,
                'total_turnos': 0,
                'completados': 0,
                'cancelados': 0,
                'ausentes': 0,
                'porcentaje_completados': 0.0,
                'porcentaje_cancelados': 0.0,
                'porcentaje_ausentes': 0.0,
                'periodo': {
                    'inicio': fecha_inicio.isoformat() if fecha_inicio else None,
                    'fin': fecha_fin.isoformat() if fecha_fin else None
                },
                'resumen': {
                    'total_turnos': 0,
                    'completados': 0,
                    'cancelados': 0,
                    'pendientes': 0,
                    'tasa_asistencia': 0.0,
                    'tasa_cancelacion': 0.0
                },
                'por_mes': []
            }

        # Calcular totales
        completados = sum(1 for t in turnos if t.estado == 'completado')
        cancelados = sum(1 for t in turnos if t.estado == 'cancelado')
        pendientes = sum(1 for t in turnos if t.estado == 'pendiente')
        ausentes = sum(1 for t in turnos if t.estado == 'ausente')

        # Calcular tasas (solo sobre turnos NO pendientes)
        turnos_finalizados = completados + cancelados + ausentes
        tasa_asistencia = (completados / turnos_finalizados * 100) if turnos_finalizados > 0 else 0
        tasa_cancelacion = (cancelados / turnos_finalizados * 100) if turnos_finalizados > 0 else 0
        tasa_ausencia = (ausentes / turnos_finalizados * 100) if turnos_finalizados > 0 else 0

        # Agrupar por mes para gráfico
        por_mes = {}
        for t in turnos:
            mes_key = f"{t.fecha.year}-{t.fecha.month:02d}"
            if mes_key not in por_mes:
                por_mes[mes_key] = {'completados': 0, 'cancelados': 0, 'pendientes': 0}

            if t.estado == 'completado':
                por_mes[mes_key]['completados'] += 1
            elif t.estado == 'cancelado':
                por_mes[mes_key]['cancelados'] += 1
            elif t.estado == 'pendiente':
                por_mes[mes_key]['pendientes'] += 1

        # Formatear por_mes
        por_mes_lista = []
        for mes, datos in sorted(por_mes.items()):
            por_mes_lista.append({
                'mes': mes,
                **datos
            })

        return {
            'fecha_inicio': fecha_inicio.isoformat() if fecha_inicio else None,
            'fecha_fin': fecha_fin.isoformat() if fecha_fin else None,
            'total_turnos': total,
            'completados': completados,
            'cancelados': cancelados,
            'ausentes': ausentes,
            'porcentaje_completados': round(tasa_asistencia, 2),
            'porcentaje_cancelados': round(tasa_cancelacion, 2),
            'porcentaje_ausentes': round(tasa_ausencia, 2),
            'periodo': {
                'inicio': fecha_inicio.isoformat() if fecha_inicio else None,
                'fin': fecha_fin.isoformat() if fecha_fin else None
            },
            'resumen': {
                'total_turnos': total,
                'completados': completados,
                'cancelados': cancelados,
                'pendientes': pendientes,
                'tasa_asistencia': round(tasa_asistencia, 2),
                'tasa_cancelacion': round(tasa_cancelacion, 2)
            },
            'por_mes': por_mes_lista
        }
