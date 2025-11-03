# Configuración con Tailscale - Acceso Remoto a Base de Datos

Este documento explica cómo configurar el proyecto para acceder a la base de datos de forma remota usando Tailscale.

## ¿Qué es Tailscale?

Tailscale es una VPN mesh que crea una red privada segura entre dispositivos. Permite que tus compañeros accedan a tu base de datos PostgreSQL local de forma segura sin exponer el puerto públicamente.

## Configuración del Host (Persona con la Base de Datos)

### 1. Instalar Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

### 2. Autenticar Tailscale

```bash
sudo tailscale up
```

Esto abrirá un navegador para autenticar con tu cuenta de Tailscale.

### 3. Obtener tu IP de Tailscale

```bash
tailscale ip -4
```

Ejemplo de salida: `100.105.169.57`

### 4. Configurar PostgreSQL para Aceptar Conexiones Remotas

Edita `/etc/postgresql/{version}/main/postgresql.conf`:
```bash
# Busca y cambia:
listen_addresses = '*'
```

Edita `/etc/postgresql/{version}/main/pg_hba.conf`:
```bash
# Agrega al final (reemplaza 100.0.0.0/8 con el rango de Tailscale):
host    all             all             100.0.0.0/8             md5
```

Reinicia PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### 5. Tu Configuración Local (.env)

Mantén tu `.env` con localhost:
```env
DB_HOST=localhost
```

## Configuración del Cliente (Compañeros Remotos)

### 1. Instalar Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

### 2. Unirse a la Misma Red Tailscale

- Ve a https://login.tailscale.com/admin/machines
- Verifica que veas la máquina del host listada
- Asegúrate de estar autenticado con la misma cuenta/organización

### 3. Configurar .env para Conexión Remota

Copia el archivo de ejemplo:
```bash
cp .env.tailscale.example .env
```

Edita `.env` y reemplaza la IP con la del host:
```env
DB_HOST=100.105.169.57  # IP de Tailscale del host
```

### 4. Verificar Conectividad

Prueba la conexión:
```bash
# Ping al host
ping 100.105.169.57

# Test de conexión a PostgreSQL
psql -h 100.105.169.57 -U postgres -d turnos_medicos_dao
```

## Verificación de Configuración

### Host
```bash
# Ver dispositivos conectados
tailscale status

# Ver tu IP
tailscale ip -4
```

### Cliente
```bash
# Ver conexión
tailscale status

# Debe mostrar el host como "online"
```

## Troubleshooting

### No puedo conectarme a la base de datos

1. **Verifica que Tailscale esté corriendo en ambas máquinas:**
   ```bash
   tailscale status
   ```

2. **Verifica conectividad de red:**
   ```bash
   ping <IP_DEL_HOST>
   ```

3. **Verifica que PostgreSQL escuche en la IP correcta:**
   ```bash
   # En el host
   sudo netstat -tlnp | grep 5432
   ```
   Debe mostrar `0.0.0.0:5432` o la IP específica.

4. **Verifica el firewall:**
   ```bash
   # En el host, permite conexiones desde Tailscale
   sudo ufw allow from 100.0.0.0/8 to any port 5432
   ```

5. **Verifica logs de PostgreSQL:**
   ```bash
   sudo tail -f /var/log/postgresql/postgresql-*.log
   ```

### Error: "FATAL: no pg_hba.conf entry"

Asegúrate de haber agregado la regla en `pg_hba.conf`:
```
host    all             all             100.0.0.0/8             md5
```

### La conexión es muy lenta

Verifica el estado de la conexión:
```bash
tailscale ping <IP_DEL_PEER>
```

## Seguridad

✅ **Ventajas de usar Tailscale:**
- Conexión encriptada punto a punto
- No expones puertos públicamente
- Control de acceso granular
- Fácil de auditar quién está conectado

⚠️ **Consideraciones:**
- Solo comparte acceso con personas de confianza
- Usa contraseñas fuertes para PostgreSQL
- Considera usar roles de solo lectura para desarrolladores
- Revisa regularmente los dispositivos conectados

## Alternativa: Desarrollo Local con Base de Datos Propia

Si prefieres no depender de la conexión remota:

1. Instala PostgreSQL localmente
2. Usa `.env.example` como base
3. Configura tu propia base de datos local
4. Comparte dumps de la BD para sincronizar datos

```bash
# Crear dump (host)
pg_dump -U postgres turnos_medicos_dao > backup.sql

# Restaurar (cliente)
psql -U postgres turnos_medicos_dao < backup.sql
```

## Recursos Adicionales

- [Documentación oficial de Tailscale](https://tailscale.com/kb/)
- [PostgreSQL Remote Access](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [Tailscale Dashboard](https://login.tailscale.com/admin/)
