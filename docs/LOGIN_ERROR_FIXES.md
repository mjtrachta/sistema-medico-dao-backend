# Correcciones de Error de Login UTF-8

## Problema Reportado

Se reportó un error de codificación UTF-8 al intentar hacer login:
```
'utf-8' codec can't decode byte 0xab in position 96: invalid start byte
```

## Diagnóstico Realizado

1. **Verificación de hashes en base de datos**: Se verificaron todos los usuarios en la base de datos y NO se encontraron problemas con los hashes de contraseñas. Todos están almacenados correctamente como strings en formato `scrypt`.

2. **Análisis de código**: El código de autenticación estaba funcionando correctamente, pero no tenía manejo robusto de errores para casos de hashes corruptos.

## Mejoras Implementadas

### 1. Manejo de Errores Mejorado en Login (`routes/auth.py`)

Se separó la verificación de contraseña en un bloque try-catch dedicado:

```python
# Verificar contraseña con mejor manejo de errores
try:
    password_valida = usuario.check_password(data['password'])
except UnicodeDecodeError as e:
    # Error específico de codificación UTF-8
    logging.error(f"Error UTF-8 al verificar contraseña para usuario {usuario.nombre_usuario}: {e}")
    return jsonify({
        'error': 'Error en la verificación de credenciales. Contacte al administrador.',
        'detail': 'Password hash encoding error'
    }), 500
except Exception as e:
    # Otros errores en la verificación de contraseña
    logging.error(f"Error al verificar contraseña para usuario {usuario.nombre_usuario}: {e}")
    return jsonify({'error': 'Error en la verificación de credenciales'}), 500
```

**Beneficios:**
- Logging detallado de errores de codificación
- Mensajes de error informativos sin exponer detalles internos
- Separación de errores de autenticación fallida vs. errores técnicos

### 2. Protección en Modelo Usuario (`models/usuario.py`)

Se mejoró el método `check_password()` para manejar hashes almacenados como bytes:

```python
def check_password(self, password):
    """Verifica si la contraseña es correcta"""
    # Asegurar que el hash es string (no bytes)
    hash_val = self.hash_contrasena
    if isinstance(hash_val, bytes):
        try:
            hash_val = hash_val.decode('utf-8')
        except UnicodeDecodeError:
            # Si no se puede decodificar, el hash está corrupto
            import logging
            logging.error(f"Hash corrupto para usuario {self.nombre_usuario}: no puede decodificarse como UTF-8")
            raise

    return check_password_hash(hash_val, password)
```

**Beneficios:**
- Maneja automáticamente hashes almacenados como bytes
- Logging específico para hashes corruptos
- Previene errores silenciosos

### 3. Herramienta de Diagnóstico (`utils/fix_password_hashes.py`)

Se creó una utilidad para diagnosticar y reparar problemas con hashes de contraseñas.

#### Uso:

**Diagnosticar todos los usuarios:**
```bash
cd backend
source venv/bin/activate
python -m utils.fix_password_hashes
```

Esto mostrará:
- Total de usuarios
- Tipo de dato del hash (string/bytes)
- Longitud del hash
- Formato del hash (scrypt/pbkdf2)
- Verificación de que el hash puede ser procesado

**Resetear contraseña de un usuario:**
```bash
python -m utils.fix_password_hashes reset <nombre_usuario> <nueva_contraseña>
```

Ejemplo:
```bash
python -m utils.fix_password_hashes reset admin NuevaPassword123!
```

## Verificación de Correcciones

Se ejecutó el diagnóstico y todos los usuarios pasaron las verificaciones:

```
============================================================
✓ NO SE ENCONTRARON PROBLEMAS
============================================================

Total de usuarios: 7
- Todos los hashes son strings ✓
- Todos usan formato scrypt ✓
- Todos pueden ser verificados sin errores ✓
```

## Causas Posibles del Error Original

Dado que no se encontraron problemas en la base de datos actual, el error pudo haber sido causado por:

1. **Datos corruptos temporales**: Hashes que fueron corregidos automáticamente
2. **Problema de sincronización**: El error ocurrió en otra computadora con una versión diferente de la base de datos
3. **Error en otra capa**: El error pudo ocurrir durante la serialización de la respuesta HTTP, no durante la verificación de contraseña

## Prevención Futura

Las mejoras implementadas aseguran que:
- Los errores de codificación se capturen y logueen correctamente
- Se puedan diagnosticar problemas de hashes fácilmente
- Se puedan reparar hashes corruptos sin pérdida de datos
- Los usuarios reciban mensajes de error informativos

## Recomendaciones

1. **Monitorear logs**: Revisar los logs de la aplicación para detectar cualquier error UTF-8 que pueda ocurrir
2. **Ejecutar diagnóstico regularmente**: Correr el script de diagnóstico periódicamente
3. **Migración de producción**: Si el error persiste, ejecutar el diagnóstico en el ambiente de producción
4. **Backup de base de datos**: Mantener backups regulares antes de cualquier corrección de hashes

## Contacto para Soporte

Si el error persiste:
1. Verificar los logs del servidor Flask
2. Ejecutar el script de diagnóstico
3. Reportar el output completo del diagnóstico
4. Incluir el traceback completo del error
