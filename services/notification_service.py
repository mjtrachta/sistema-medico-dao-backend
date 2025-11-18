"""
PATRÓN: Observer Pattern + Strategy Pattern + Service Layer
==========================================================

Este servicio combina múltiples patrones:

1. OBSERVER PATTERN:
   - NotificationService actúa como Observer de TurnoService
   - Reacciona a eventos: turno_creado, turno_cancelado, etc.
   - Desacopla TurnoService del envío de notificaciones

2. STRATEGY PATTERN:
   - Usa NotificationStrategy para enviar mensajes
   - Puede cambiar canal de notificación (email, SMS, etc.)

3. SERVICE LAYER:
   - Encapsula lógica de notificaciones
   - Coordina estrategias y repository de notificaciones

FLUJO COMPLETO (COMBINACIÓN DE PATRONES):
-----------------------------------------
1. Usuario crea turno → TurnoService.crear_turno()
2. TurnoService notifica observers → _notify_observers('turno_creado', turno)
3. NotificationService (observer) recibe evento → update('turno_creado', turno)
4. NotificationService usa Strategy → EmailStrategy.send(...)
5. Se guarda registro → NotificacionRepository.create(...)

BENEFICIOS DE LA COMBINACIÓN:
-----------------------------
- TurnoService NO conoce cómo se envían notificaciones
- NotificationService NO conoce cómo se crean turnos
- Fácil agregar nuevos canales (nueva Strategy)
- Fácil agregar nuevos observadores
- Cada componente testeable independientemente
"""

from typing import Dict, Any
from models import Notificacion, Turno
from repositories.base_repository import BaseRepository
from strategies.notification_strategy import (
    NotificationStrategy,
    NotificationStrategyFactory
)
from datetime import datetime


class NotificationService:
    """
    Servicio de gestión de notificaciones.

    PATRONES APLICADOS:
    - Observer Pattern: Observa eventos de turnos
    - Strategy Pattern: Usa estrategias para enviar
    - Service Layer: Encapsula lógica de negocio

    Responsabilidades:
    - Reaccionar a eventos de turnos
    - Seleccionar estrategia de envío apropiada
    - Crear mensajes personalizados por tipo de evento
    - Registrar notificaciones enviadas
    """

    def __init__(self,
                 notificacion_repository: BaseRepository[Notificacion] = None,
                 default_strategy: str = 'email',
                 config: Dict[str, Any] = None):
        """
        Constructor con Dependency Injection.

        Args:
            notificacion_repository: Repository para guardar notificaciones
            default_strategy: Estrategia por defecto ('email', 'sms', etc.)
            config: Configuración de estrategias
        """
        # Repository inyectable
        self.notificacion_repository = notificacion_repository or BaseRepository(Notificacion)

        # Configuración de estrategias
        self.config = config or {}

        # Estrategia actual (Strategy Pattern)
        self.strategy = NotificationStrategyFactory.create(
            default_strategy,
            self.config.get(default_strategy, {})
        )

        # Registro de estrategias disponibles
        self._strategies_cache = {
            default_strategy: self.strategy
        }

    # ==========================================
    # OBSERVER PATTERN - MÉTODO UPDATE
    # ==========================================

    def update(self, event_type: str, turno: Turno):
        """
        Método update del Observer Pattern.

        Este método es llamado por TurnoService cuando ocurre un evento.

        OBSERVER PATTERN: Punto de entrada de notificaciones

        Args:
            event_type: Tipo de evento ('turno_creado', 'turno_cancelado', etc.)
            turno: Turno que disparó el evento
        """
        # Determinar destinatario y canal según evento
        # En este caso simple, siempre enviamos al paciente por email
        # En producción, esto podría configurarse por paciente

        if event_type == 'turno_creado':
            self._notificar_turno_creado(turno)

        elif event_type == 'turno_cancelado':
            self._notificar_turno_cancelado(turno)

        elif event_type == 'turno_confirmado':
            self._notificar_turno_confirmado(turno)

        elif event_type == 'recordatorio_turno':
            self._notificar_recordatorio(turno)

    # ==========================================
    # CREACIÓN DE MENSAJES POR TIPO DE EVENTO
    # ==========================================
    # PATRÓN: Template Method
    # Cada método sigue el mismo flujo:
    # 1. Crear asunto y mensaje
    # 2. Enviar con estrategia
    # 3. Registrar notificación

    def _notificar_turno_creado(self, turno: Turno):
        """
        Envía notificación cuando se crea un turno.

        TEMPLATE METHOD: Flujo estándar de notificación
        """
        # 1. Construir mensaje
        asunto = "Turno Médico Confirmado"
        mensaje = self._construir_mensaje_turno_creado(turno)

        # 2. Determinar destinatario
        destinatario = turno.paciente.email

        if not destinatario:
            print(f"Paciente {turno.paciente.nombre_completo} no tiene email")
            return

        # 3. Enviar usando estrategia actual
        exito = self.strategy.send(destinatario, asunto, mensaje, {
            'turno_id': turno.id,
            'codigo_turno': turno.codigo_turno
        })

        # 4. Registrar notificación (sin fallar si hay problemas de BD)
        try:
            self._registrar_notificacion(
                turno, destinatario, asunto, mensaje,
                'enviado' if exito else 'fallido'
            )
        except Exception as e:
            # Log del error pero no fallar el envío
            print(f"Error guardando notificación en BD: {e}")
            print("El email se envió correctamente, solo falló el registro en BD")

    def _notificar_turno_cancelado(self, turno: Turno):
        """Notifica cancelación de turno."""
        asunto = "Turno Médico Cancelado"
        mensaje = self._construir_mensaje_turno_cancelado(turno)
        destinatario = turno.paciente.email

        if destinatario:
            exito = self.strategy.send(destinatario, asunto, mensaje)
            try:
                self._registrar_notificacion(
                    turno, destinatario, asunto, mensaje,
                    'enviado' if exito else 'fallido'
                )
            except Exception as e:
                print(f"Error guardando notificación en BD: {e}")
                print("El email se envió correctamente, solo falló el registro en BD")

    def _notificar_turno_confirmado(self, turno: Turno):
        """Notifica confirmación de turno."""
        asunto = "Turno Médico Confirmado"
        mensaje = self._construir_mensaje_turno_confirmado(turno)
        destinatario = turno.paciente.email

        if destinatario:
            exito = self.strategy.send(destinatario, asunto, mensaje)
            try:
                self._registrar_notificacion(
                    turno, destinatario, asunto, mensaje,
                    'enviado' if exito else 'fallido'
                )
            except Exception as e:
                print(f"Error guardando notificación en BD: {e}")
                print("El email se envió correctamente, solo falló el registro en BD")

    def _notificar_recordatorio(self, turno: Turno):
        """Envía recordatorio de turno próximo."""
        asunto = "Recordatorio: Turno Médico Próximo"
        mensaje = self._construir_mensaje_recordatorio(turno)
        destinatario = turno.paciente.email

        if destinatario:
            exito = self.strategy.send(destinatario, asunto, mensaje)
            try:
                self._registrar_notificacion(
                    turno, destinatario, asunto, mensaje,
                    'enviado' if exito else 'fallido'
                )
            except Exception as e:
                print(f"Error guardando notificación en BD: {e}")
                print("El email se envió correctamente, solo falló el registro en BD")

    # ==========================================
    # CONSTRUCCIÓN DE MENSAJES
    # ==========================================
    # Estos métodos crean el contenido HTML de cada tipo de notificación

    def _construir_mensaje_turno_creado(self, turno: Turno) -> str:
        """
        Construye mensaje HTML para turno creado.

        BUILDER PATTERN (simplificado):
        - Construye mensaje paso a paso
        - Fácil modificar template
        """
        return f"""
        <p>Estimado/a <strong>{turno.paciente.nombre_completo}</strong>,</p>

        <p>Su turno médico ha sido confirmado con los siguientes datos:</p>

        <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <p><strong>Código de Turno:</strong> {turno.codigo_turno}</p>
            <p><strong>Médico:</strong> Dr./Dra. {turno.medico.nombre_completo}</p>
            <p><strong>Especialidad:</strong> {turno.medico.especialidad.nombre if turno.medico.especialidad else 'N/A'}</p>
            <p><strong>Fecha:</strong> {turno.fecha.strftime('%d/%m/%Y')}</p>
            <p><strong>Hora:</strong> {turno.hora.strftime('%H:%M')}</p>
            <p><strong>Ubicación:</strong> {turno.ubicacion.nombre}</p>
            <p><strong>Dirección:</strong> {turno.ubicacion.direccion}</p>
        </div>

        <p><strong>Importante:</strong></p>
        <ul>
            <li>Llegue 10 minutos antes de su turno</li>
            <li>Traiga su DNI y credencial de obra social</li>
            <li>Si necesita cancelar, hágalo con 24hs de anticipación</li>
        </ul>

        <p>Ante cualquier consulta, puede comunicarse al {turno.ubicacion.telefono}.</p>

        <p>Saludos cordiales,<br>
        <strong>Sistema de Turnos Médicos</strong></p>
        """

    def _construir_mensaje_turno_cancelado(self, turno: Turno) -> str:
        """Construye mensaje para turno cancelado."""
        return f"""
        <p>Estimado/a <strong>{turno.paciente.nombre_completo}</strong>,</p>

        <p>Le informamos que su turno médico ha sido <strong>cancelado</strong>:</p>

        <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <p><strong>Código de Turno:</strong> {turno.codigo_turno}</p>
            <p><strong>Médico:</strong> Dr./Dra. {turno.medico.nombre_completo}</p>
            <p><strong>Fecha/Hora:</strong> {turno.fecha.strftime('%d/%m/%Y')} {turno.hora.strftime('%H:%M')}</p>
        </div>

        <p>Si desea reagendar, puede comunicarse con nosotros o solicitar un nuevo turno a través del sistema.</p>

        <p>Saludos cordiales,<br>
        <strong>Sistema de Turnos Médicos</strong></p>
        """

    def _construir_mensaje_turno_confirmado(self, turno: Turno) -> str:
        """Construye mensaje para confirmación de turno."""
        return f"""
        <p>Estimado/a <strong>{turno.paciente.nombre_completo}</strong>,</p>

        <p>Su turno médico ha sido <strong>confirmado</strong>:</p>

        <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <p><strong>Código de Turno:</strong> {turno.codigo_turno}</p>
            <p><strong>Fecha/Hora:</strong> {turno.fecha.strftime('%d/%m/%Y')} {turno.hora.strftime('%H:%M')}</p>
            <p><strong>Médico:</strong> Dr./Dra. {turno.medico.nombre_completo}</p>
        </div>

        <p>Le esperamos en el horario indicado.</p>
        """

    def _construir_mensaje_recordatorio(self, turno: Turno) -> str:
        """Construye mensaje de recordatorio."""
        return f"""
        <p>Estimado/a <strong>{turno.paciente.nombre_completo}</strong>,</p>

        <p>Le recordamos que tiene un turno médico próximo:</p>

        <div style="background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <p><strong>Mañana</strong> - {turno.fecha.strftime('%d/%m/%Y')} a las {turno.hora.strftime('%H:%M')}</p>
            <p><strong>Médico:</strong> Dr./Dra. {turno.medico.nombre_completo}</p>
            <p><strong>Ubicación:</strong> {turno.ubicacion.nombre}</p>
        </div>

        <p>Recuerde llegar 10 minutos antes y traer su documentación.</p>
        """

    # ==========================================
    # REGISTRO DE NOTIFICACIONES
    # ==========================================

    def _registrar_notificacion(self, turno: Turno, destinatario: str,
                               asunto: str, mensaje: str, estado: str):
        """
        Registra la notificación en la base de datos.

        Útil para:
        - Auditoría
        - Reenvío de notificaciones fallidas
        - Estadísticas de envío
        """
        notificacion = Notificacion(
            turno_id=turno.id,
            tipo=self.strategy.get_tipo(),
            destinatario=destinatario,
            mensaje=f"{asunto}\n\n{mensaje}",
            estado=estado,
            enviado_en=datetime.now() if estado == 'enviado' else None
        )

        self.notificacion_repository.create(notificacion)

    # ==========================================
    # GESTIÓN DE ESTRATEGIAS (STRATEGY PATTERN)
    # ==========================================

    def set_strategy(self, strategy: NotificationStrategy):
        """
        Cambia la estrategia de notificación en runtime.

        STRATEGY PATTERN: Intercambiar algoritmo dinámicamente

        Ejemplo:
            service.set_strategy(EmailStrategy())
            service.set_strategy(SMSStrategy())
        """
        self.strategy = strategy

    def set_strategy_by_type(self, tipo: str):
        """
        Cambia estrategia por tipo.

        Args:
            tipo: 'email', 'sms', 'push', 'whatsapp'
        """
        # Usar cache de estrategias
        if tipo not in self._strategies_cache:
            self._strategies_cache[tipo] = NotificationStrategyFactory.create(
                tipo,
                self.config.get(tipo, {})
            )

        self.strategy = self._strategies_cache[tipo]

    # ==========================================
    # ENVÍO MANUAL DE NOTIFICACIONES
    # ==========================================

    def enviar_notificacion_manual(self, turno_id: int, destinatario: str,
                                   asunto: str, mensaje: str,
                                   tipo: str = None) -> bool:
        """
        Envía una notificación manual (no disparada por evento).

        Útil para:
        - Notificaciones administrativas
        - Reenvío de notificaciones
        - Comunicados generales

        Args:
            turno_id: ID del turno (opcional, puede ser None)
            destinatario: Email o teléfono
            asunto: Asunto del mensaje
            mensaje: Cuerpo del mensaje
            tipo: Tipo de estrategia a usar (si no se especifica, usa actual)

        Returns:
            True si se envió, False si falló
        """
        # Cambiar estrategia si se especifica tipo diferente
        if tipo and tipo != self.strategy.get_tipo():
            self.set_strategy_by_type(tipo)

        # Enviar
        exito = self.strategy.send(destinatario, asunto, mensaje)

        # Registrar (sin turno asociado si turno_id es None)
        notificacion = Notificacion(
            turno_id=turno_id,
            tipo=self.strategy.get_tipo(),
            destinatario=destinatario,
            mensaje=f"{asunto}\n\n{mensaje}",
            estado='enviado' if exito else 'fallido',
            enviado_en=datetime.now() if exito else None
        )

        self.notificacion_repository.create(notificacion)

        return exito
