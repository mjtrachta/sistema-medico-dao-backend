# Configuración en PyCharm

## Paso 1: Configurar el Intérprete de Python

1. **File → Settings** (o Ctrl+Alt+S)
2. **Project: backend → Python Interpreter**
3. Click en el ⚙️ (engranaje) → **Add**
4. Seleccionar **Existing Environment**
5. Buscar: `/home/hari/Proyecto-DAO/backend/venv/bin/python`
6. **OK** → **Apply** → **OK**

## Paso 2: Marcar directorios como Sources Root

1. Click derecho en la carpeta `backend`
2. **Mark Directory as → Sources Root**

## Paso 3: Configurar Variables de Entorno en PyCharm

1. **Run → Edit Configurations**
2. Click en el `+` → **Python**
3. Configurar:
   - **Name:** "Flask App"
   - **Script path:** `/home/hari/Proyecto-DAO/backend/app.py`
   - **Working directory:** `/home/hari/Proyecto-DAO/backend`
   - **Environment variables:** Click en 📁 y agregar:
     ```
     FLASK_ENV=development
     PYTHONUNBUFFERED=1
     ```
4. **Apply** → **OK**

## Paso 4: Instalar Dependencias

En la terminal de PyCharm (Alt+F12):

```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

O usar el script:
```bash
./setup.sh
```

## Paso 5: Ejecutar la Aplicación

### Opción 1: Desde PyCharm
- Click en el botón ▶️ (Run) o presiona Shift+F10

### Opción 2: Desde Terminal
```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar
python app.py
```

### Opción 3: Usar script
```bash
./run.sh
```

## Verificar que funciona

Abrir en el navegador:
- **Health Check:** http://localhost:5000/api/health

Debería responder:
```json
{
  "status": "ok",
  "message": "Sistema de Turnos Médicos - API funcionando",
  "database": "connected"
}
```

## Problemas Comunes

### Error: ModuleNotFoundError
**Solución:** Verificar que el intérprete de PyCharm esté configurado al venv correcto.

### Error: Connection refused (PostgreSQL)
**Solución:** Verificar que PostgreSQL esté corriendo:
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql  # Si no está corriendo
```

### Error: database "turnos_medicos_dao" does not exist
**Solución:** La base de datos debe estar creada previamente con el script SQL proporcionado.

### Error: psycopg2 not installed
**Solución:**
```bash
source venv/bin/activate
pip install psycopg2-binary
```

## Estructura de Archivos Importante

```
backend/
├── app.py              ← Punto de entrada (ejecutar este)
├── config/
│   └── config.py       ← Configuración de BD
├── models/             ← Modelos SQLAlchemy
├── repositories/       ← Repository Pattern
├── services/           ← Service Layer
├── routes/             ← Controllers (Endpoints)
├── .env                ← Variables de entorno
└── requirements.txt    ← Dependencias
```

## Tips para PyCharm

### Autocompletado de Imports
PyCharm puede no reconocer los imports automáticamente. Para solucionarlo:
1. **File → Settings → Project → Project Structure**
2. Marcar `backend` como **Sources**

### Debugging
1. Poner breakpoints en el código (click en el margen izquierdo)
2. Run → Debug 'Flask App' (Shift+F9)

### Base de Datos
PyCharm Professional tiene herramientas de BD:
1. **View → Tool Windows → Database**
2. **+ → Data Source → PostgreSQL**
3. Configurar:
   - Host: localhost
   - Port: 5432
   - Database: turnos_medicos_dao
   - User: postgres
   - Password: postgres123

### Terminal Integrada
- **Alt+F12** abre la terminal dentro de PyCharm
- Automáticamente activa el venv si está configurado
