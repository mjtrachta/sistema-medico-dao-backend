# Ejemplo de Uso de Patrones de Diseño
## Sistema de Turnos Médicos

Este documento muestra cómo los patrones de diseño se combinan en un flujo completo de creación de turno.

## Flujo Completo: Crear un Turno

### 1. Request HTTP (Usuario)
```
POST /api/turnos
{
    "paciente_id": 1,
    "medico_id": 5,
    "ubicacion_id": 1,
    "fecha": "2024-12-15",
    "hora": "14:30",
    "duracion_min": 30,
    "motivo_consulta": "Control"
}
```

### 2. CONTROLLER (Facade Pattern)
**Archivo**: `controllers/turno_controller.py`

```python
class TurnoController:
    """
    PATRÓN: Facade Pattern
    - Provee interfaz simple al cliente
    - Internamente coordina múltiples servicios
    """

    def __init__(self):
        # Dependency Injection: Inyectar dependencias
        self.turno_service = TurnoService()
        self.notification_service = NotificationService()

        # Observer Pattern: Suscribir notification service
        self.turno_service.attach_observer(self.notification_service)

    def create(self, request_data):
        """
        Facade: Un solo método hace todo el trabajo.

        Internamente:
        1. Valida datos (DTO Pattern)
        2. Llama al servicio
        3. El servicio coordina repository + observers
        4. Retorna respuesta serializada
        """
        # DTO Pattern: Marshmallow valida y deserializa
        turno = turno_schema.load(request_data)

        # Service Layer: Lógica de negocio
        turno_creado = self.turno_service.crear_turno(
            paciente_id=turno.paciente_id,
            medico_id=turno.medico_id,
            # ... resto de parámetros
        )

        # DTO Pattern: Serializar respuesta
        return turno_schema.dump(turno_creado)
```

**FACADE**: El controller simplifica la operación compleja en `create()`.

---

### 3. SERVICE LAYER
**Archivo**: `services/turno_service.py`

```python
class TurnoService:
    """
    PATRÓN: Service Layer + Observer Pattern
    """

    def crear_turno(self, paciente_id, medico_id, ...):
        # STEP 1: Validación (Specification Pattern en Repository)
        disponible = self.turno_repository.verificar_disponibilidad_medico(
            medico_id, fecha, hora, duracion_min
        )

        if not disponible:
            raise ValueError("Horario no disponible")

        # STEP 2: Crear entidad
        turno = Turno(
            paciente_id=paciente_id,
            medico_id=medico_id,
            # ...
        )

        # STEP 3: Persistir (Repository Pattern)
        turno_creado = self.turno_repository.create(turno)

        # STEP 4: Notificar observers (Observer Pattern)
        self._notify_observers('turno_creado', turno_creado)
        #  └─→ Aquí se dispara NotificationService

        return turno_creado
```

**Patrones combinados**:
- **Service Layer**: Orquesta la operación
- **Repository Pattern**: Delega persistencia
- **Observer Pattern**: Notifica sin acoplamiento

---

### 4. REPOSITORY LAYER
**Archivo**: `repositories/turno_repository.py`

```python
class TurnoRepository(BaseRepository[Turno]):
    """
    PATRÓN: Repository + Specification Pattern
    """

    def verificar_disponibilidad_medico(self, medico_id, fecha, hora, duracion):
        """
        SPECIFICATION PATTERN: Encapsula regla de negocio compleja

        Reglas:
        1. Médico tiene horario ese día
        2. No hay superposición con otros turnos
        """

        # Specification 1: Tiene horario
        if not self._tiene_horario_atencion(...):
            return False

        # Specification 2: No hay superposición
        if self._existe_superposicion(...):
            return False

        return True

    def create(self, turno):
        """
        TEMPLATE METHOD PATTERN (heredado de BaseRepository)

        Flujo:
        1. _before_create() → Genera código de turno
        2. db.session.add() → Guarda en BD
        3. _after_create() → Hook para auditoría
        """
        # Hook del Template Method
        self._before_create(turno)

        # Persistencia
        db.session.add(turno)
        db.session.commit()

        return turno
```

**Patrones combinados**:
- **Repository**: Abstrae acceso a datos
- **Specification**: Valida reglas complejas
- **Template Method**: Evita duplicar código CRUD

---

### 5. OBSERVER PATTERN (Notificaciones)
**Archivo**: `services/notification_service.py`

```python
class NotificationService:
    """
    PATRÓN: Observer + Strategy Pattern
    """

    def update(self, event_type, turno):
        """
        OBSERVER: Método llamado cuando ocurre evento

        TurnoService llama: _notify_observers('turno_creado', turno)
        Esto ejecuta: notification_service.update('turno_creado', turno)
        """

        if event_type == 'turno_creado':
            self._notificar_turno_creado(turno)

    def _notificar_turno_creado(self, turno):
        """
        Usa STRATEGY PATTERN para enviar notificación
        """
        asunto = "Turno Confirmado"
        mensaje = self._construir_mensaje(turno)
        destinatario = turno.paciente.email

        # STRATEGY PATTERN: Delega envío a estrategia
        self.strategy.send(destinatario, asunto, mensaje)
        #  └─→ Puede ser EmailStrategy, SMSStrategy, etc.
```

**OBSERVER**: Desacopla evento de acción

---

### 6. STRATEGY PATTERN (Envío)
**Archivo**: `strategies/notification_strategy.py`

```python
class EmailStrategy(NotificationStrategy):
    """
    STRATEGY PATTERN: Implementación específica
    """

    def send(self, destinatario, asunto, mensaje):
        """
        Algoritmo de envío de email
        """
        # Conectar SMTP
        # Formatear HTML
        # Enviar
        # Retornar resultado
```

**STRATEGY**: Intercambiable con SMSStrategy, WhatsAppStrategy, etc.

---

## Diagrama de Flujo Completo

```
┌─────────────┐
│   USUARIO   │
└──────┬──────┘
       │ POST /api/turnos
       ▼
┌─────────────────────────────────────┐
│  CONTROLLER (Facade Pattern)        │
│  - Simplifica operación compleja    │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  SERVICE (Service Layer)            │
│  1. Validar disponibilidad          │
│  2. Crear turno (Repository)        │
│  3. Notificar observers             │
└──────┬────────────────┬─────────────┘
       │                │
       ▼                ▼
┌──────────────┐  ┌────────────────────┐
│ REPOSITORY   │  │ NOTIFICATION       │
│ (Repository  │  │ (Observer)         │
│  Pattern)    │  │                    │
│              │  │  ┌──────────────┐  │
│ - Query DB   │  │  │  STRATEGY    │  │
│ - Validate   │  │  │  (Strategy)  │  │
│ - Save       │  │  │              │  │
└──────┬───────┘  │  │ EmailStrategy│  │
       │          │  │ SMSStrategy  │  │
       ▼          │  └──────┬───────┘  │
  ┌─────────┐    │         │          │
  │DATABASE │    │         ▼          │
  └─────────┘    │    ┌────────┐     │
                 │    │ SMTP/  │     │
                 │    │ SMS    │     │
                 │    └────────┘     │
                 └────────────────────┘
```

---

## Justificación de Cada Patrón en el Flujo

### ¿Por qué Facade en Controller?
**Sin Facade:**
```python
# Cliente debe conocer múltiples servicios
service1.validar()
service2.crear()
service3.notificar()
```

**Con Facade:**
```python
# Una sola llamada hace todo
controller.create(data)
```

### ¿Por qué Service Layer?
**Sin Service Layer:**
- Controllers gordos con lógica de negocio
- O Models gordos (Fat Models)
- Difícil reutilizar lógica

**Con Service Layer:**
- Lógica centralizada
- Reutilizable desde API, CLI, tests

### ¿Por qué Repository?
**Sin Repository:**
```python
# Service acoplado a SQLAlchemy
turno = Turno(...)
db.session.add(turno)
db.session.commit()
```

**Con Repository:**
```python
# Service desacoplado, fácil testear
repository.create(turno)
# En tests: mock_repository.create(turno)
```

### ¿Por qué Observer?
**Sin Observer:**
```python
# Acoplamiento directo
def crear_turno():
    turno = repository.create(...)
    notification_service.send(...)  # ¡Acoplado!
```

**Con Observer:**
```python
# Desacoplado
def crear_turno():
    turno = repository.create(...)
    _notify_observers('turno_creado', turno)
    # Los observers se suscriben, no hay acoplamiento
```

### ¿Por qué Strategy?
**Sin Strategy:**
```python
def send_notification(tipo, ...):
    if tipo == 'email':
        # código email
    elif tipo == 'sms':
        # código sms
    # Viola Open/Closed
```

**Con Strategy:**
```python
# Agregar WhatsAppStrategy NO modifica código existente
strategy = WhatsAppStrategy()
notification_service.set_strategy(strategy)
```

---

## Principios SOLID Aplicados

1. **Single Responsibility**
   - Controller: Maneja HTTP
   - Service: Lógica de negocio
   - Repository: Acceso a datos

2. **Open/Closed**
   - Strategy Pattern: Agregar nueva estrategia sin modificar existentes
   - Observer Pattern: Agregar nuevos observers sin modificar TurnoService

3. **Liskov Substitution**
   - EmailStrategy y SMSStrategy son intercambiables
   - Cualquier Repository puede reemplazar a otro

4. **Interface Segregation**
   - NotificationStrategy define solo send()
   - No obliga a implementar métodos innecesarios

5. **Dependency Inversion**
   - Services dependen de abstracciones (Repository, Strategy)
   - No dependen de implementaciones concretas

---

## Testing Facilitado por Patrones

```python
# Test de TurnoService sin tocar BD
def test_crear_turno():
    # MOCK del repository (gracias a DI)
    mock_repo = Mock(TurnoRepository)
    mock_repo.verificar_disponibilidad_medico.return_value = True

    # Inyectar mock
    service = TurnoService(turno_repository=mock_repo)

    # Test aislado
    turno = service.crear_turno(...)

    # Verificar que se llamó al repository
    mock_repo.create.assert_called_once()
```

**Sin patrones**: Testing difícil, acoplado a BD

**Con patrones**: Testing fácil, componentes aislados
