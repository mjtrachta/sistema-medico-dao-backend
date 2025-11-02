# Sistema Médico DAO - Backend

API REST desarrollada con Flask para gestión de turnos médicos, historias clínicas y recetas.

## Tecnologías

- **Python 3.10+**
- **Flask** - Framework web
- **SQLAlchemy** - ORM para base de datos
- **Flask-JWT-Extended** - Autenticación JWT
- **PostgreSQL** - Base de datos
- **Marshmallow** - Serialización

## Patrones de Diseño Implementados

- **Repository Pattern** - Capa de acceso a datos
- **Service Layer Pattern** - Lógica de negocio
- **Facade Pattern** - Simplificación de interfaces
- **Strategy Pattern** - Validaciones flexibles
- **Factory Pattern** - Creación de objetos

## Características Principales

### Gestión de Usuarios
- Autenticación JWT con roles (admin, médico, paciente, recepcionista)
- Registro y login seguros

### Gestión de Turnos
- Crear, ver y gestionar turnos médicos
- Atención de turnos por médicos
- Filtrado por médico, paciente, fecha y estado

### Historias Clínicas
- Creación desde turnos completados (solo médicos)
- Visualización según permisos por rol
- Preservación permanente de datos

### Recetas Médicas
- Emisión por médicos con matrícula profesional
- Gestión de medicamentos y posología
- Validación de fechas de vencimiento

### Horarios y Ubicaciones
- Gestión de horarios de médicos por ubicación
- Validación automática de superposición de horarios
- Soft delete de médicos preservando datos de pacientes

### Reportes (Admin)
- Dashboard con estadísticas
- Reportes por médico, paciente y período

## Instalación

1. **Clonar el repositorio:**
```bash
git clone <repository-url>
cd backend
```

2. **Crear entorno virtual:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate  # Windows
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

5. **Inicializar base de datos:**
```bash
# Crear base de datos PostgreSQL
# Luego ejecutar:
python -c "from models.database import db; from app import create_app; app = create_app(); app.app_context().push(); db.create_all()"
```

6. **Crear usuarios de prueba:**
```bash
python crear_usuarios_medicos.py
```

## Ejecutar

```bash
python app.py
```

El servidor estará disponible en `http://localhost:5000`

## Estructura del Proyecto

```
backend/
├── app.py                  # Punto de entrada
├── config/                 # Configuración
├── models/                 # Modelos de datos (SQLAlchemy)
├── repositories/           # Capa de acceso a datos
├── services/              # Lógica de negocio
├── routes/                # Endpoints REST
├── schemas/               # Schemas de validación (Marshmallow)
├── validators/            # Validadores personalizados
├── strategies/            # Estrategias de validación
└── tests/                 # Tests unitarios
```

## API Endpoints

### Autenticación
- `POST /api/auth/register` - Registro de usuario
- `POST /api/auth/login` - Login

### Turnos
- `GET /api/turnos` - Listar turnos
- `POST /api/turnos` - Crear turno
- `PUT /api/turnos/{id}` - Actualizar turno
- `PUT /api/turnos/{id}/estado` - Cambiar estado

### Horarios
- `GET /api/horarios` - Listar horarios
- `POST /api/horarios` - Crear horario (validación de superposición)
- `PUT /api/horarios/{id}` - Actualizar horario
- `DELETE /api/horarios/{id}` - Desactivar horario

### Ubicaciones
- `GET /api/ubicaciones` - Listar ubicaciones
- `POST /api/ubicaciones` - Crear ubicación (admin)
- `PUT /api/ubicaciones/{id}` - Actualizar ubicación
- `DELETE /api/ubicaciones/{id}` - Desactivar ubicación

### Historias Clínicas
- `GET /api/historias-clinicas` - Listar según rol
- `POST /api/historias-clinicas` - Crear (solo médicos)
- `PUT /api/historias-clinicas/{id}` - Actualizar (solo médico creador)

### Recetas
- `GET /api/recetas` - Listar según rol
- `POST /api/recetas` - Crear (solo médicos)

## Validaciones de Negocio

- ✅ No superposición de horarios para el mismo médico
- ✅ Validación de matrícula profesional para actos médicos
- ✅ Preservación de datos al desactivar médicos
- ✅ Validación de fechas y rangos horarios
- ✅ Control de acceso por roles

## Testing

```bash
pytest
```

## Licencia

Proyecto académico - DAO

## Autor

Sistema desarrollado para gestión médica integral
