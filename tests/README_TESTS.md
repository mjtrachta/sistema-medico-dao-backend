# Guía de Testing - Proyecto Turnos Médicos

## 🎯 Objetivo

Estos tests demuestran cómo los **patrones de diseño facilitan el testing**.

## 📁 Estructura de Tests

```
tests/
├── conftest.py              # Fixtures compartidos (Factory Pattern)
├── test_repositories.py     # Tests de Repository Pattern
├── test_services.py         # Tests de Service Layer + Observer
├── test_api.py              # Tests de integración (Facade)
└── README_TESTS.md          # Esta guía
```

## 🚀 Ejecutar Tests

### Instalar dependencias de testing

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Ejecutar todos los tests

```bash
# Todos los tests con cobertura
pytest

# Solo tests unitarios (rápidos)
pytest -m unit

# Solo tests de integración
pytest -m integration

# Test específico
pytest tests/test_repositories.py::TestPacienteRepository::test_create_paciente_genera_historia_clinica_automatica

# Con output detallado
pytest -v

# Ver cobertura en HTML
pytest --cov-report=html
# Abrir: htmlcov/index.html
```

## 📊 Tipos de Tests

### 1. Unit Tests (test_repositories.py, test_services.py)

**Características:**
- Testean un componente aislado
- Usan mocks para dependencias
- Muy rápidos (ms)
- No tocan BD real

**Ejemplo:**
```python
def test_crear_turno_valida_disponibilidad(mocker):
    # Mock del repository
    mock_repo = mocker.Mock()
    mock_repo.verificar_disponibilidad.return_value = False

    # Inyectar mock (Dependency Injection)
    service = TurnoService(turno_repository=mock_repo)

    # Test aislado
    with pytest.raises(ValueError):
        service.crear_turno(...)
```

### 2. Integration Tests (test_api.py)

**Características:**
- Testean flujo completo
- Usan BD de test (SQLite in-memory)
- Más lentos (segundos)
- Verifican integración

**Ejemplo:**
```python
def test_create_turno_con_horario_exitoso(client, paciente, medico):
    # Test HTTP completo
    response = client.post('/api/turnos', json={...})
    assert response.status_code == 201
```

## 🎨 Patrones Demostrados en Tests

### Repository Pattern

**Test que lo demuestra:** `test_repositories.py`

```python
def test_find_by_documento(app, paciente):
    repo = PacienteRepository()

    # Repository abstrae query SQL
    encontrado = repo.find_by_documento('DNI', '12345678')

    assert encontrado.nombre == 'Juan'
```

**Beneficio:** Tests NO tienen SQL, solo usan métodos del repository.

---

### Dependency Injection

**Test que lo demuestra:** `test_services.py`

```python
def test_crear_turno_valida_disponibilidad(mocker):
    # MOCK inyectado
    mock_repo = mocker.Mock()

    # Service acepta dependency injection
    service = TurnoService(turno_repository=mock_repo)

    # Test aislado, sin tocar BD
```

**Beneficio:** Fácil inyectar mocks, tests rápidos y aislados.

---

### Observer Pattern

**Test que lo demuestra:** `test_services.py`

```python
def test_crear_turno_notifica_observers(mocker):
    mock_observer = mocker.Mock()

    service.attach_observer(mock_observer)
    service.crear_turno(...)

    # Verificar que se notificó
    mock_observer.update.assert_called_once()
```

**Beneficio:** Verificar que eventos se disparan sin enviar emails reales.

---

### Specification Pattern

**Test que lo demuestra:** `test_repositories.py`

```python
def test_verificar_disponibilidad_sin_horario(app, medico):
    repo = TurnoRepository()

    # Specification encapsulada
    disponible = repo.verificar_disponibilidad_medico(...)

    assert disponible is False
```

**Beneficio:** Reglas de negocio complejas testeadas independientemente.

---

### Factory Pattern (Fixtures)

**Definido en:** `conftest.py`

```python
@pytest.fixture
def paciente(db_session):
    # Factory crea paciente de prueba
    paciente = Paciente(...)
    db_session.add(paciente)
    db_session.commit()
    return paciente

# Uso en test
def test_algo(paciente):
    # paciente ya está creado y listo
    assert paciente.nombre == 'Juan'
```

**Beneficio:** Reutilizar creación de objetos en todos los tests.

---

## 📈 Cobertura de Código

Ejecutar con cobertura:

```bash
pytest --cov=. --cov-report=html
```

Abrir reporte:
```bash
xdg-open htmlcov/index.html  # Linux
open htmlcov/index.html       # Mac
```

**Meta:** >80% de cobertura en:
- Repositories
- Services
- Controllers

## 🔧 Configuración (pytest.ini)

```ini
[pytest]
testpaths = tests
addopts = -v --cov=. --cov-report=html

markers =
    unit: tests unitarios
    integration: tests de integración
```

## 📝 Escribir Nuevos Tests

### Test de Repository

```python
def test_nuevo_metodo_repository(app):
    with app.app_context():
        repo = PacienteRepository()

        resultado = repo.nuevo_metodo()

        assert resultado is not None
```

### Test de Service (con mocks)

```python
def test_nuevo_metodo_service(mocker):
    mock_repo = mocker.Mock()
    mock_repo.metodo.return_value = 'valor'

    service = MiService(repository=mock_repo)

    resultado = service.nuevo_metodo()

    assert resultado == 'valor'
    mock_repo.metodo.assert_called_once()
```

### Test de API

```python
def test_nuevo_endpoint(client):
    response = client.post('/api/endpoint', json={...})

    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['campo'] == 'valor'
```

## 🎓 Para la Presentación Universitaria

**Puntos clave:**

1. **Sin patrones:** Tests difíciles, acoplados, lentos
2. **Con patrones:** Tests fáciles, aislados, rápidos

**Demostración:**

```bash
# Ejecutar todos los tests
pytest -v

# Mostrar cobertura
pytest --cov=. --cov-report=term-missing

# Mostrar que tests pasan rápidamente (ms)
pytest --durations=10
```

## 📚 Comparación: Con vs Sin Patrones

### SIN PATRONES

```python
# Test acoplado a BD y SQL
def test_crear_turno():
    conn = psycopg2.connect(...)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO turnos ...")
    # Test frágil, lento, difícil
```

**Problemas:**
- ❌ Lento (BD real)
- ❌ Acoplado a PostgreSQL
- ❌ Difícil aislar
- ❌ Setup complejo

### CON PATRONES

```python
# Test aislado con mocks
def test_crear_turno(mocker):
    mock_repo = mocker.Mock()
    service = TurnoService(turno_repository=mock_repo)
    # Test rápido, aislado, fácil
```

**Beneficios:**
- ✅ Rápido (in-memory)
- ✅ Desacoplado
- ✅ Aislado
- ✅ Setup simple (fixtures)

---

## 🚀 Comandos Útiles

```bash
# Ejecutar tests
pytest

# Solo repositorios
pytest tests/test_repositories.py

# Solo services
pytest tests/test_services.py

# Solo API
pytest tests/test_api.py

# Con cobertura
pytest --cov=.

# Verbose
pytest -v

# Mostrar print() en tests
pytest -s

# Test específico
pytest tests/test_services.py::TestTurnoService::test_crear_turno_valida_disponibilidad

# Último test que falló
pytest --lf

# Tests que modificaste
pytest --ff
```

## ✅ Checklist de Testing

Antes de presentar:

- [ ] Todos los tests pasan (`pytest`)
- [ ] Cobertura >80% (`pytest --cov=.`)
- [ ] Tests unitarios <1s cada uno
- [ ] Tests de integración <5s cada uno
- [ ] Sin warnings de pytest
- [ ] Documentación de patrones clara en tests

---

**Los tests demuestran que los patrones de diseño facilitan el desarrollo profesional!** 🎯
