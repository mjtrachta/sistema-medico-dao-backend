# Patrones de Diseño Implementados - Sistema de Turnos Médicos

## Índice de Patrones Utilizados

### 1. PATRONES CREACIONALES

#### 1.1 Factory Pattern (Fábrica)
- **Ubicación**: `app.py` - función `create_app()`
- **Propósito**: Crear instancias de la aplicación Flask con diferentes configuraciones
- **Justificación**: Permite crear múltiples configuraciones (desarrollo, producción, testing) sin modificar el código. Facilita testing y deployment.

#### 1.2 Singleton Pattern (Instancia Única)
- **Ubicación**: `models/database.py`, `schemas/__init__.py`
- **Propósito**: Garantizar una única instancia de conexión a BD y serialización
- **Justificación**: La conexión a BD debe ser única para mantener el pool de conexiones. Marshmallow debe tener una sola instancia para schemas consistentes.

#### 1.3 Builder Pattern (Constructor)
- **Ubicación**: `services/report_builder.py`
- **Propósito**: Construir reportes complejos paso a paso
- **Justificación**: Los reportes tienen múltiples configuraciones opcionales (filtros, agrupaciones, formatos). Builder permite construirlos de forma flexible.

---

### 2. PATRONES ESTRUCTURALES

#### 2.1 Repository Pattern (Repositorio)
- **Ubicación**: `repositories/`
- **Propósito**: Abstraer el acceso a datos, separando lógica de persistencia
- **Justificación**:
  - Separa la lógica de negocio del acceso a datos
  - Facilita testing (se pueden crear repositorios mock)
  - Centraliza queries complejas
  - Permite cambiar el ORM sin afectar la lógica de negocio

#### 2.2 Facade Pattern (Fachada)
- **Ubicación**: `controllers/` y `services/`
- **Propósito**: Proveer interfaz simplificada a subsistemas complejos
- **Justificación**:
  - Los controllers exponen API simple aunque internamente coordinen múltiples servicios
  - Ejemplo: crear turno implica validar horario, verificar disponibilidad, guardar y notificar

#### 2.3 DTO Pattern (Data Transfer Object)
- **Ubicación**: `schemas/` (Marshmallow schemas)
- **Propósito**: Transferir datos entre capas sin exponer modelos internos
- **Justificación**:
  - Separación entre modelo de BD y modelo de API
  - Validación de datos de entrada
  - Serialización/deserialización consistente

---

### 3. PATRONES COMPORTAMENTALES

#### 3.1 Strategy Pattern (Estrategia)
- **Ubicación**: `strategies/notification_strategies.py`
- **Propósito**: Definir familia de algoritmos (Email, SMS) intercambiables
- **Justificación**:
  - Permite agregar nuevos tipos de notificación sin modificar código existente
  - Cada estrategia encapsula su lógica de envío
  - Cumple con Open/Closed Principle

#### 3.2 Observer Pattern (Observador)
- **Ubicación**: `services/event_manager.py`
- **Propósito**: Notificar cambios de estado (turno creado/cancelado)
- **Justificación**:
  - Desacopla la creación de turnos de las notificaciones
  - Múltiples observadores pueden reaccionar a eventos
  - Facilita auditoría y logging

#### 3.3 Specification Pattern (Especificación)
- **Ubicación**: `validators/`
- **Propósito**: Encapsular reglas de negocio reutilizables
- **Justificación**:
  - Validaciones complejas (horarios disponibles, superposición de turnos)
  - Reglas combinables con operadores lógicos
  - Reutilización en queries y validaciones

#### 3.4 Template Method Pattern (Método Plantilla)
- **Ubicación**: `repositories/base_repository.py`
- **Propósito**: Definir esqueleto de operaciones CRUD
- **Justificación**:
  - Evita duplicación de código CRUD básico
  - Permite personalizar pasos específicos por entidad
  - Mantiene consistencia en operaciones

---

### 4. PATRONES ARQUITECTURALES

#### 4.1 Layered Architecture (Arquitectura en Capas)
```
Controllers (API Layer)
    ↓
Services (Business Logic Layer)
    ↓
Repositories (Data Access Layer)
    ↓
Models (Database Layer)
```
- **Justificación**:
  - Separación de responsabilidades clara
  - Cada capa tiene un propósito específico
  - Facilita mantenimiento y testing
  - Permite cambios en una capa sin afectar otras

#### 4.2 Dependency Injection (Inyección de Dependencias)
- **Ubicación**: Constructores de Services y Controllers
- **Propósito**: Invertir control de creación de dependencias
- **Justificación**:
  - Facilita testing (inyectar mocks)
  - Reduce acoplamiento
  - Mejora mantenibilidad

---

## Combinación de Patrones y Justificación

### Caso 1: Controller + Service + Repository
**Flujo**: `TurnoController` → `TurnoService` → `TurnoRepository`

**Combinación de Patrones**:
- **Facade** (Controller): API simplificada
- **Service Layer**: Lógica de negocio
- **Repository**: Acceso a datos

**Justificación de la combinación**:
- Controller no conoce detalles de BD
- Service no conoce detalles de HTTP
- Repository no conoce reglas de negocio
- Cada capa es testeable independientemente

### Caso 2: Service + Strategy + Observer
**Flujo**: Crear Turno → Validar → Guardar → Notificar

**Combinación de Patrones**:
- **Service Layer**: Orquesta el proceso
- **Strategy**: Elige canal de notificación
- **Observer**: Dispara notificación automática

**Justificación de la combinación**:
- Service coordina sin conocer implementación de notificación
- Strategy permite cambiar canal sin modificar Service
- Observer desacopla evento de acción

### Caso 3: Repository + Specification
**Flujo**: Buscar Turnos Disponibles

**Combinación de Patrones**:
- **Repository**: Ejecuta query
- **Specification**: Define criterios de búsqueda

**Justificación de la combinación**:
- Specifications son reutilizables
- Repository traduce specification a SQL
- Criterios complejos se componen con AND/OR

---

## Beneficios de la Arquitectura Implementada

1. **Mantenibilidad**: Código organizado y responsabilidades claras
2. **Testabilidad**: Cada componente es testeable en aislamiento
3. **Escalabilidad**: Fácil agregar nuevas features
4. **Flexibilidad**: Cambios en una capa no afectan otras
5. **Reutilización**: Componentes reutilizables (repositories, validators)
6. **Principios SOLID**:
   - **S**ingle Responsibility: Cada clase una responsabilidad
   - **O**pen/Closed: Abierto a extensión, cerrado a modificación
   - **L**iskov Substitution: Interfaces intercambiables
   - **I**nterface Segregation: Interfaces específicas
   - **D**ependency Inversion: Depender de abstracciones

---

## Decisiones de Diseño Clave

### ¿Por qué Repository Pattern?
- **Alternativa descartada**: Acceso directo a modelos desde controllers
- **Razón**: Acopla controllers a SQLAlchemy, dificulta testing

### ¿Por qué Service Layer?
- **Alternativa descartada**: Lógica en controllers o models
- **Razón**: Controllers muy gordos o models anémicos

### ¿Por qué Strategy para Notificaciones?
- **Alternativa descartada**: If/else para cada tipo
- **Razón**: Viola Open/Closed, difícil agregar nuevos tipos

### ¿Por qué DTO con Marshmallow?
- **Alternativa descartada**: Exponer modelos SQLAlchemy directamente
- **Razón**: Acopla API a estructura de BD, problemas de seguridad
