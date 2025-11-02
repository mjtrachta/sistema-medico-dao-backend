"""
PATRÓN: Service Layer + Observer Pattern + Specification Pattern
================================================================

Este servicio combina múltiples patrones:

1. SERVICE LAYER:
   - Encapsula lógica de negocio de turnos
   - Orquesta repositories, validators y notificaciones

2. OBSERVER PATTERN:
   - Notifica eventos (turno creado, cancelado, etc.)
   - Desacopla creación de turno de envío de notificaciones

3. SPECIFICATION PATTERN:
   - Validaciones complejas encapsuladas
   - Reutilizables y combinables

4. FACADE PATTERN:
   - Simplifica operaciones complejas
   - API simple aunque internamente coordine múltiples componentes

JUSTIFICACIÓN DE COMBINACIÓN:
-----------------------------
¿Por qué combinar estos patrones?

- Service Layer: Necesitamos lógica de negocio centralizada
- Observer: Crear turno debe disparar notificación, pero sin acoplar
- Specification: Validaciones complejas (horarios, superposición)
- Facade: API simple para controllers (crear turno en un solo método)

Ejemplo de flujo:
    Controller → TurnoService.crear_turno() → [
        1. Validar datos (Specification)
        2. Verificar disponibilidad (Repository)
        3. Guardar turno (Repository)
        4. Notificar (Observer)
    ]
"""

from typing import List, Optional
from datetime import date, time
from models import Turno
from repositories.turno_repository import TurnoRepository
from repositories.paciente_repository import PacienteRepository
from repositories import BaseRepository
from services.base_service import BaseService


class TurnoService(BaseService[Turno]):
    """
    Servicio de gestión de turnos.

    PATRÓN PRINCIPAL: Service Layer

    Responsabilidades:
    - CRUD de turnos con validaciones
    - Gestión de disponibilidad
    - Coordinación de notificaciones
    - Generación de reportes
    """

    def __init__(self,
                 turno_repository: TurnoRepository = None,
                 paciente_repository: PacienteRepository = None):
        """
        Constructor con Dependency Injection.

        PATRÓN: Dependency Injection
        - Repositories se inyectan (facilita testing)
        - Si no se pasan, se crean por defecto

        Args:
            turno_repository: Repositorio de turnos (inyectable)
            paciente_repository: Repositorio de pacientes (inyectable)
        """
        # Inyectar o crear repositories
        self.turno_repository = turno_repository or TurnoRepository()
        self.paciente_repository = paciente_repository or PacienteRepository()

        # Llamar constructor padre
        super().__init__(self.turno_repository)

        # Lista de observadores (Observer Pattern)
        self._observers = []

    # ==========================================
    # OBSERVER PATTERN - GESTIÓN DE EVENTOS
    # ==========================================

    def attach_observer(self, observer):
        """
        Agrega un observador.

        OBSERVER PATTERN: Permite suscribirse a eventos
        Ejemplo: NotificacionService se suscribe para enviar emails
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def detach_observer(self, observer):
        """Remueve un observador."""
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self, event_type: str, turno: Turno):
        """
        Notifica a todos los observadores.

        OBSERVER PATTERN: Desacopla eventos de acciones

        Args:
            event_type: Tipo de evento (turno_creado, turno_cancelado, etc.)
            turno: Turno que disparó el evento
        """
        for observer in self._observers:
            observer.update(event_type, turno)

    # ==========================================
    # LÓGICA DE NEGOCIO - OPERACIONES CRUD
    # ==========================================

    def crear_turno(self, paciente_id: int, medico_id: int,
                   ubicacion_id: int, fecha: date, hora: time,
                   duracion_min: int = 30, motivo_consulta: str = None,
                   usuario_id: int = None) -> Turno:
        """
        Crea un nuevo turno con todas las validaciones.

        PATRÓN: Facade Pattern
        - API simple que internamente ejecuta operación compleja
        - Coordina: validación → creación → notificación

        PATRÓN: Transaction Script
        - Secuencia de pasos para completar la operación

        Args:
            paciente_id: ID del paciente
            medico_id: ID del médico
            ubicacion_id: ID de la ubicación
            fecha: Fecha del turno
            hora: Hora del turno
            duracion_min: Duración en minutos
            motivo_consulta: Motivo de la consulta
            usuario_id: ID del usuario que crea el turno

        Returns:
            Turno creado

        Raises:
            ValueError: Si las validaciones fallan
        """
        # 1. VALIDACIONES (Specification Pattern encapsulado en Repository)

        # Validar que el paciente existe
        paciente = self.paciente_repository.find_by_id(paciente_id)
        if not paciente:
            raise ValueError(f"Paciente con ID {paciente_id} no encontrado")

        if not paciente.activo:
            raise ValueError("El paciente está inactivo")

        # Validar disponibilidad del médico
        # Esta validación encapsula reglas de negocio complejas
        disponible = self.turno_repository.verificar_disponibilidad_medico(
            medico_id, fecha, hora, duracion_min
        )

        if not disponible:
            raise ValueError(
                "El horario no está disponible. "
                "Verifique que el médico atienda ese día/hora "
                "y que no haya superposición con otros turnos."
            )

        # 2. CREAR TURNO
        turno = Turno(
            paciente_id=paciente_id,
            medico_id=medico_id,
            ubicacion_id=ubicacion_id,
            fecha=fecha,
            hora=hora,
            duracion_min=duracion_min,
            motivo_consulta=motivo_consulta,
            estado='pendiente',
            creado_por_usuario_id=usuario_id
        )

        # El repository se encarga de generar código y validar
        turno_creado = self.turno_repository.create(turno)

        # 3. NOTIFICAR OBSERVADORES (Observer Pattern)
        # Los observadores decidirán qué hacer (enviar email, SMS, etc.)
        self._notify_observers('turno_creado', turno_creado)

        return turno_creado

    def cancelar_turno(self, turno_id: int, usuario_id: int = None) -> Turno:
        """
        Cancela un turno.

        PATRÓN: State Pattern (implícito en estado)
        - El turno cambia de estado
        - Diferentes estados permiten diferentes operaciones

        Args:
            turno_id: ID del turno a cancelar
            usuario_id: ID del usuario que cancela

        Returns:
            Turno cancelado

        Raises:
            ValueError: Si el turno no se puede cancelar
        """
        # Obtener turno
        turno = self.turno_repository.find_by_id(turno_id)
        if not turno:
            raise ValueError(f"Turno con ID {turno_id} no encontrado")

        # Validar que se pueda cancelar
        # SPECIFICATION: Regla de negocio - solo ciertos estados permiten cancelación
        if turno.estado in ['completado', 'cancelado']:
            raise ValueError(f"No se puede cancelar un turno en estado {turno.estado}")

        # Cambiar estado
        turno.estado = 'cancelado'
        turno_actualizado = self.turno_repository.update(turno)

        # Notificar cancelación
        self._notify_observers('turno_cancelado', turno_actualizado)

        return turno_actualizado

    def confirmar_turno(self, turno_id: int) -> Turno:
        """
        Confirma un turno (cambia estado a confirmado).

        State Pattern: Transición de estado pendiente → confirmado
        """
        turno = self.turno_repository.find_by_id(turno_id)
        if not turno:
            raise ValueError(f"Turno con ID {turno_id} no encontrado")

        if turno.estado != 'pendiente':
            raise ValueError("Solo se pueden confirmar turnos pendientes")

        turno.estado = 'confirmado'
        turno_actualizado = self.turno_repository.update(turno)

        self._notify_observers('turno_confirmado', turno_actualizado)

        return turno_actualizado

    def marcar_completado(self, turno_id: int) -> Turno:
        """
        Marca un turno como completado.

        Se ejecuta cuando el paciente asiste a la consulta.
        """
        turno = self.turno_repository.find_by_id(turno_id)
        if not turno:
            raise ValueError(f"Turno con ID {turno_id} no encontrado")

        if turno.estado not in ['pendiente', 'confirmado']:
            raise ValueError("Solo se pueden completar turnos pendientes o confirmados")

        turno.estado = 'completado'
        return self.turno_repository.update(turno)

    def marcar_ausente(self, turno_id: int) -> Turno:
        """
        Marca un turno como ausente (paciente no asistió).

        Importante para estadísticas de ausentismo.
        """
        turno = self.turno_repository.find_by_id(turno_id)
        if not turno:
            raise ValueError(f"Turno con ID {turno_id} no encontrado")

        if turno.estado not in ['pendiente', 'confirmado']:
            raise ValueError("Solo se pueden marcar como ausentes turnos pendientes o confirmados")

        turno.estado = 'ausente'
        return self.turno_repository.update(turno)

    # ==========================================
    # CONSULTAS Y BÚSQUEDAS
    # ==========================================

    def buscar_turnos_paciente(self, paciente_id: int,
                               desde: date = None,
                               hasta: date = None) -> List[Turno]:
        """
        Busca turnos de un paciente.

        Facade: Simplifica llamada al repository
        """
        return self.turno_repository.find_by_paciente(
            paciente_id, desde, hasta
        )

    def buscar_turnos_medico(self, medico_id: int,
                            desde: date = None,
                            hasta: date = None) -> List[Turno]:
        """Busca turnos de un médico."""
        return self.turno_repository.find_by_medico(
            medico_id, desde, hasta
        )

    def obtener_horarios_disponibles(self, medico_id: int,
                                     fecha: date,
                                     duracion_min: int = 30) -> List[time]:
        """
        Obtiene horarios disponibles de un médico en una fecha.

        Facade: Simplifica consulta compleja del repository
        """
        return self.turno_repository.get_horarios_disponibles(
            medico_id, fecha, duracion_min
        )

    # ==========================================
    # REPORTES Y ESTADÍSTICAS
    # ==========================================
    # Estos métodos encapsulan lógica de reportes
    # Builder Pattern se usará para reportes complejos

    def obtener_estadisticas_periodo(self, fecha_desde: date,
                                     fecha_hasta: date) -> dict:
        """
        Obtiene estadísticas de turnos en un período.

        Retorna:
        - Turnos por estado
        - Turnos por especialidad
        - Tasa de ausentismo
        """
        return {
            'turnos_por_estado': self.turno_repository.get_turnos_por_estado(
                fecha_desde, fecha_hasta
            ),
            'turnos_por_especialidad': self.turno_repository.get_turnos_por_especialidad(
                fecha_desde, fecha_hasta
            ),
            'tasa_ausentismo': self.turno_repository.get_tasa_ausentismo(
                fecha_desde, fecha_hasta
            )
        }

    def obtener_turnos_proximos(self, paciente_id: int, dias: int = 30) -> List[Turno]:
        """
        Obtiene turnos próximos de un paciente.

        Útil para recordatorios.
        """
        from datetime import datetime, timedelta

        hoy = datetime.now().date()
        hasta = hoy + timedelta(days=dias)

        return self.turno_repository.find_by_paciente(
            paciente_id,
            desde=hoy,
            hasta=hasta,
            estados=['pendiente', 'confirmado']
        )

    # ==========================================
    # HOOKS DEL BASE SERVICE (TEMPLATE METHOD)
    # ==========================================

    def _after_create(self, turno: Turno):
        """
        Hook ejecutado después de crear turno.

        Template Method: Sobrescrito del BaseService
        Aquí NO enviamos notificación directamente,
        usamos Observer Pattern para desacoplar.
        """
        # Los observers ya fueron notificados en crear_turno()
        pass

    def _validate_delete(self, turno: Turno):
        """
        Hook: Validación antes de eliminar turno.

        REGLA DE NEGOCIO: No permitir eliminar turnos completados
        (solo cancelar)
        """
        if turno.estado == 'completado':
            raise ValueError("No se pueden eliminar turnos completados. Use cancelar en su lugar.")
