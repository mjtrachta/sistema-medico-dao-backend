# Solución de Problemas - Troubleshooting

## 🚨 Errores Comunes y Soluciones

### 1. ModuleNotFoundError: No module named 'X'

**Error:**
```
ModuleNotFoundError: No module named 'flask'
ModuleNotFoundError: No module named 'psycopg2'
```

**Causa:** Dependencias no instaladas o entorno virtual no activado.

**Solución:**
```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
pip list | grep -i flask
```

---

### 2. Connection Refused (PostgreSQL)

**Error:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
```

**Causa:** PostgreSQL no está corriendo.

**Solución:**
```bash
# Verificar estado
sudo systemctl status postgresql

# Iniciar PostgreSQL
sudo systemctl start postgresql

# Habilitar inicio automático
sudo systemctl enable postgresql
```

---

### 3. Database Does Not Exist

**Error:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL:  database "turnos_medicos_dao" does not exist
```

**Causa:** La base de datos no fue creada.

**Solución:**
```bash
# Conectar a PostgreSQL como postgres
sudo -u postgres psql

# Verificar si existe la BD
\l

# Si no existe, crearla (desde psql)
CREATE DATABASE turnos_medicos_dao WITH OWNER postgres ENCODING 'UTF8';

# Salir
\q

# Ejecutar el script SQL de creación de tablas
sudo -u postgres psql -d turnos_medicos_dao -f /path/to/script.sql
```

---

### 4. Authentication Failed (PostgreSQL)

**Error:**
```
psycopg2.OperationalError: FATAL:  password authentication failed for user "postgres"
```

**Causa:** Contraseña incorrecta en `.env`.

**Solución:**

**Opción 1:** Cambiar contraseña de postgres
```bash
sudo -u postgres psql
ALTER USER postgres PASSWORD 'postgres123';
\q
```

**Opción 2:** Usar peer authentication
Editar archivo `.env`:
```env
DB_USER=tu_usuario_linux
DB_PASSWORD=  # dejar vacío
```

---

### 5. ImportError: cannot import name 'X' from 'Y'

**Error:**
```
ImportError: cannot import name 'turno_schema' from 'schemas'
```

**Causa:** Importación circular o módulo no encontrado.

**Solución:**
```python
# En lugar de importar desde __init__
from schemas.turno_schema import turno_schema

# NO desde:
# from schemas import turno_schema
```

---

### 6. SQLAlchemy No Foreign Key Constraint

**Error:**
```
sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column 'turnos.paciente_id' could not find table 'pacientes'
```

**Causa:** Tablas no creadas en orden correcto o no existen.

**Solución:**
```bash
# Verificar que todas las tablas existen
sudo -u postgres psql -d turnos_medicos_dao -c "\dt"

# Debe mostrar 13 tablas
# Si no, ejecutar el script SQL de creación
```

---

### 7. CORS Error (desde frontend)

**Error en navegador:**
```
Access to XMLHttpRequest at 'http://localhost:5000/api/turnos' from origin 'http://localhost:4200' has been blocked by CORS policy
```

**Causa:** CORS no configurado correctamente.

**Solución:**
Ya está configurado en `app.py`. Verificar que el backend esté corriendo en puerto 5000:
```bash
curl http://localhost:5000/api/health
```

---

### 8. Email Notification Failed

**Error:**
```
smtplib.SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```

**Causa:** Credenciales de email incorrectas o no configuradas.

**Solución (Gmail):**
1. Ir a https://myaccount.google.com/security
2. Habilitar "Verificación en 2 pasos"
3. Ir a "Contraseñas de aplicaciones"
4. Generar contraseña para "Correo"
5. Copiar contraseña en `.env`:
```env
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-contraseña-de-aplicacion-aqui
```

**Nota:** NO usar la contraseña normal de Gmail.

---

### 9. Port Already in Use

**Error:**
```
OSError: [Errno 98] Address already in use
```

**Causa:** Otra aplicación usando puerto 5000.

**Solución:**
```bash
# Encontrar proceso usando puerto 5000
sudo lsof -i :5000

# Matar proceso
kill -9 [PID]

# O cambiar puerto en app.py:
# app.run(debug=True, host='0.0.0.0', port=5001)
```

---

### 10. PyCharm No Reconoce Imports

**Error:** Subrayado rojo en imports aunque funcionan.

**Solución:**
1. **File → Settings → Project → Project Structure**
2. Marcar `backend` como **Sources Root**
3. **File → Invalidate Caches → Invalidate and Restart**

---

## 🔍 Comandos de Diagnóstico

### Verificar Python
```bash
python3 --version
which python3
```

### Verificar PostgreSQL
```bash
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"
```

### Verificar Base de Datos
```bash
sudo -u postgres psql -d turnos_medicos_dao -c "\dt"  # Listar tablas
sudo -u postgres psql -d turnos_medicos_dao -c "SELECT COUNT(*) FROM especialidades;"
```

### Verificar Conexión Flask
```bash
# Health check
curl http://localhost:5000/api/health

# Con formato JSON
curl http://localhost:5000/api/health | python3 -m json.tool
```

### Verificar Dependencias Python
```bash
source venv/bin/activate
pip list
pip check
```

---

## 📝 Logs y Debug

### Ver logs de PostgreSQL
```bash
sudo tail -f /var/log/postgresql/postgresql-16-main.log
```

### Debug de Flask
En `app.py`, el modo debug ya está activado:
```python
app.run(debug=True, ...)
```

Esto muestra:
- Stack traces completos
- Auto-reload al modificar código
- Debugger interactivo en errores

---

## 🆘 Si nada funciona

### Reset completo:

```bash
# 1. Eliminar entorno virtual
rm -rf venv

# 2. Recrear desde cero
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Verificar BD
sudo -u postgres psql -d turnos_medicos_dao -c "\dt"

# 4. Ejecutar
python app.py
```

---

## 📞 Contacto

Si el problema persiste:
1. Revisar logs completos de error
2. Buscar el error en Google
3. Consultar documentación:
   - Flask: https://flask.palletsprojects.com/
   - SQLAlchemy: https://docs.sqlalchemy.org/
   - PostgreSQL: https://www.postgresql.org/docs/
