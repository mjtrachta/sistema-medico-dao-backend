# 🚀 GUÍA COMPLETA PARA PROBAR NOTIFICACIONES
# =====================================================

## 📧 CONFIGURACIÓN PREVIA

### 1. Configurar Gmail (Opción Recomendada):
1. Ve a tu cuenta de Google → Seguridad
2. Habilita "Verificación en 2 pasos"
3. Ve a "Contraseñas de aplicaciones"
4. Genera una contraseña para "Correo"
5. Usa esa contraseña en el .env

### 2. Editar archivo .env:
Reemplaza estas líneas en tu archivo .env:

```
SMTP_USERNAME=tu-email@gmail.com
SMTP_PASSWORD=la-contraseña-de-aplicacion-generada
```

### 3. Reiniciar el backend:
Después de cambiar el .env, reinicia el servidor Flask.

---

## 🧪 MÉTODOS PARA PROBAR

### MÉTODO 1: Testing Directo (SIN JWT) - MÁS FÁCIL
Endpoint especial creado para testing: `/api/testing/notificacion`

### MÉTODO 2: Testing con JWT Token
Usar el endpoint original con autenticación.

---

## 📮 REQUESTS PARA POSTMAN - NO GUARDAN EN LA BASE DE DATOS - NO JWT

### 🔸 MÉTODO 1 - Test Directo de Notificación (SIN JWT)

**URL:** `POST http://localhost:5000/api/testing/notificacion`
**Body (JSON):**
```json
{
    "destinatario": "tu-email-personal@gmail.com",
    "tipo": "turno_creado",
    "strategy": "email"
}
```

**Opciones de tipo:**
- `turno_creado` - Notificación de turno creado
- `turno_cancelado` - Notificación de turno cancelado  
- `recordatorio` - Recordatorio de turno

---

### 🔸 MÉTODO 2 - Crear Turno Completo (SIN JWT)

**URL:** `POST http://localhost:5000/api/testing/crear-turno`
**Body (JSON):**
```json
{
    "medico_id": 1,
    "ubicacion_id": 1,
    "fecha": "2024-12-25",
    "hora": "14:30",
    "duracion_min": 30,
    "motivo_consulta": "Prueba endpoint simplificado",
    "email_paciente": "maximofloresstampone2@gmail.com"
}
```

**IMPORTANTE:** 
- Reemplaza `tu-email-personal@gmail.com` con tu email real
- Asegúrate de que `medico_id` y `ubicacion_id` existan en tu BD
- Usa una fecha futura

---

## 🔍 QUÉ VERIFICAR

### ✅ Si Todo Funciona Bien:

1. **Respuesta HTTP 200/201** con JSON de éxito
2. **Email llega a tu bandeja** (puede ir a spam inicialmente)
3. **Logs en terminal** del backend muestran el envío
4. **En la base de datos** se crea registro en tabla `notificaciones`

---
## 🎯 RECOMENDACIÓN

**Empieza con MÉTODO 1** (testing directo) porque:
- ✅ No necesita JWT
- ✅ Más simple de configurar
- ✅ Te permite enfocar solo en las notificaciones
- ✅ Feedback inmediato

Una vez que funcione el email, puedes probar los otros métodos.


## 📊 VERIFICAR EN LOGS

Mientras haces las pruebas, mantén el terminal del backend abierto para ver:
- Conexión SMTP exitosa/fallida
- Emails enviados
- Errores de configuración

¡Configurar el email en Gmail y usar MÉTODO 1 debería funcionar inmediatamente! 🚀