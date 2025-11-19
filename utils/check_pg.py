"""
Script para diagnosticar variables de entorno y configuración de PostgreSQL en Windows.
Busca todas las variables PG* y archivos de configuración que puedan estar causando problemas.
Uso: python -m utils.diagnosticar_postgresql_env
"""

import os
import sys

print("=" * 80)
print("DIAGNÓSTICO DE CONFIGURACIÓN DE POSTGRESQL")
print("=" * 80)
print()

# 1. Variables de entorno relacionadas con PostgreSQL
print("1. VARIABLES DE ENTORNO DE POSTGRESQL")
print("-" * 80)

pg_vars = {}
all_vars = dict(os.environ)

for key, value in all_vars.items():
    if key.startswith('PG') or key.startswith('POSTGRES'):
        pg_vars[key] = value

if pg_vars:
    print(f"Se encontraron {len(pg_vars)} variables de entorno relacionadas con PostgreSQL:")
    print()
    for key, value in sorted(pg_vars.items()):
        # Analizar si hay caracteres problemáticos
        tiene_especiales = any(ord(c) > 127 for c in value)

        print(f"  {key}:")
        print(f"    Valor: '{value}'")
        print(f"    Longitud: {len(value)} caracteres")

        if tiene_especiales:
            print(f"    ⚠️  ADVERTENCIA: Contiene caracteres no-ASCII")
            for i, c in enumerate(value):
                if ord(c) > 127:
                    print(f"       Posición {i}: '{c}' (Unicode: {ord(c)}, hex: 0x{ord(c):04x})")

        # Analizar bytes
        try:
            value_bytes = value.encode('utf-8')
            print(f"    Bytes UTF-8: {' '.join(f'0x{b:02x}' for b in value_bytes[:20])}{'...' if len(value_bytes) > 20 else ''}")
        except Exception as e:
            print(f"    ❌ ERROR al codificar: {e}")

        print()
else:
    print("✓ No se encontraron variables de entorno PG* o POSTGRES*")
    print()

# 2. Buscar archivos de configuración comunes de PostgreSQL en Windows
print("2. ARCHIVOS DE CONFIGURACIÓN DE POSTGRESQL")
print("-" * 80)

# Ubicaciones comunes en Windows
posibles_ubicaciones = [
    os.path.expanduser('~/.pgpass'),
    os.path.expanduser('~/.pg_service.conf'),
    os.path.expanduser('~/pgpass.conf'),
    os.path.expanduser('~/pg_service.conf'),
    os.path.join(os.getenv('APPDATA', ''), 'postgresql', 'pgpass.conf'),
    os.path.join(os.getenv('APPDATA', ''), 'postgresql', 'pg_service.conf'),
]

archivos_encontrados = []
for ruta in posibles_ubicaciones:
    if os.path.exists(ruta):
        archivos_encontrados.append(ruta)

if archivos_encontrados:
    print(f"⚠️  Se encontraron {len(archivos_encontrados)} archivos de configuración:")
    print()
    for ruta in archivos_encontrados:
        print(f"  {ruta}")
        try:
            with open(ruta, 'rb') as f:
                contenido_bytes = f.read()
                print(f"    Tamaño: {len(contenido_bytes)} bytes")

                # Intentar leer como texto
                try:
                    contenido_texto = contenido_bytes.decode('utf-8')
                    print(f"    ✓ Se puede leer como UTF-8")
                    print(f"    Primeras líneas:")
                    for linea in contenido_texto.split('\n')[:5]:
                        print(f"      {linea}")
                except UnicodeDecodeError as e:
                    print(f"    ❌ ERROR al leer como UTF-8: {e}")
                    print(f"    Primeros 100 bytes: {contenido_bytes[:100]}")

                    # Buscar el byte 0xab
                    if b'\xab' in contenido_bytes:
                        posiciones = [i for i, b in enumerate(contenido_bytes) if b == 0xab]
                        print(f"    ⚠️  Se encontró el byte 0xab en posiciones: {posiciones}")
        except Exception as e:
            print(f"    ❌ ERROR al leer archivo: {e}")
        print()
else:
    print("✓ No se encontraron archivos de configuración de PostgreSQL comunes")
    print()

# 3. Información del sistema
print("3. INFORMACIÓN DEL SISTEMA")
print("-" * 80)
print(f"Sistema operativo: {sys.platform}")
print(f"Encoding por defecto: {sys.getdefaultencoding()}")
print(f"Encoding del sistema de archivos: {sys.getfilesystemencoding()}")
print()

# 4. Test directo con psycopg2
print("4. TEST DIRECTO CON PSYCOPG2")
print("-" * 80)

try:
    import psycopg2
    print(f"✓ psycopg2 versión: {psycopg2.__version__}")
    print()

    # Construir DSN
    from dotenv import load_dotenv
    load_dotenv()

    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres123')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'turnos_medicos_dao')

    dsn = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

    print(f"DSN a usar: {dsn}")
    print(f"Longitud del DSN: {len(dsn)} caracteres")
    print()

    print("Intentando conectar con psycopg2 directamente...")
    try:
        # Intentar conexión usando el formato de DSN
        conn = psycopg2.connect(dsn)
        print("✓ Conexión exitosa con DSN estilo URI")
        conn.close()
    except Exception as e:
        print(f"❌ Error con DSN estilo URI: {e}")
        print(f"Tipo de error: {type(e).__name__}")

        # Mostrar traceback detallado
        import traceback
        print("\nTraceback completo:")
        traceback.print_exc()
        print()

    # Intentar con parámetros separados
    print("\nIntentando conectar con parámetros separados...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("✓ Conexión exitosa con parámetros separados")
        conn.close()
    except Exception as e:
        print(f"❌ Error con parámetros separados: {e}")
        print(f"Tipo de error: {type(e).__name__}")

        import traceback
        print("\nTraceback completo:")
        traceback.print_exc()

except ImportError:
    print("❌ No se pudo importar psycopg2")

print()
print("=" * 80)
print("FIN DEL DIAGNÓSTICO")
print("=" * 80)
