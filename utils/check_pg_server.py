"""
Script para verificar la configuración del servidor PostgreSQL.
Intenta conectarse usando psycopg2 binario (sin encoding automático).
Uso: python -m utils.check_pg_server
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres123')
DB_NAME = os.getenv('DB_NAME', 'turnos_medicos_dao')

print("=" * 80)
print("DIAGNÓSTICO DEL SERVIDOR POSTGRESQL")
print("=" * 80)
print()

# 1. Verificar si podemos conectarnos con psycopg2 binary
print("1. INTENTANDO CONEXIÓN CON PSYCOPG2-BINARY")
print("-" * 80)

try:
    import psycopg2
    import psycopg2.extensions
    print(f"✓ psycopg2 versión: {psycopg2.__version__}")

    # Intentar conexión forzando client_encoding
    print("\nIntentando conexión con client_encoding='UTF8'...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            client_encoding='UTF8'
        )
        print("✓ Conexión exitosa con client_encoding='UTF8'")

        # Obtener información del servidor
        cur = conn.cursor()

        print("\nInformación del servidor:")
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"  PostgreSQL versión: {version}")

        cur.execute("SHOW server_encoding;")
        server_encoding = cur.fetchone()[0]
        print(f"  Server encoding: {server_encoding}")

        cur.execute("SHOW client_encoding;")
        client_encoding = cur.fetchone()[0]
        print(f"  Client encoding: {client_encoding}")

        cur.execute("SHOW lc_collate;")
        lc_collate = cur.fetchone()[0]
        print(f"  LC_COLLATE: {lc_collate}")

        cur.execute("SHOW lc_ctype;")
        lc_ctype = cur.fetchone()[0]
        print(f"  LC_CTYPE: {lc_ctype}")

        cur.close()
        conn.close()

        print("\n✓ Conexión exitosa y configuración obtenida")

    except UnicodeDecodeError as e:
        print(f"❌ Error UTF-8: {e}")
        print(f"\nDetalles del error:")
        print(f"  Posición: {e.start}")
        print(f"  Byte problemático: 0x{e.object[e.start]:02x}")
        print(f"  Encoding esperado: {e.encoding}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

except ImportError as e:
    print(f"❌ No se pudo importar psycopg2: {e}")

print()

# 2. Intentar con diferentes encodings
print("2. PROBANDO DIFERENTES CLIENT_ENCODINGS")
print("-" * 80)

encodings_a_probar = ['UTF8', 'LATIN1', 'WIN1252', 'SQL_ASCII']

for encoding in encodings_a_probar:
    try:
        print(f"\nProbando con client_encoding='{encoding}'...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            client_encoding=encoding
        )
        print(f"  ✓ Conexión exitosa")
        conn.close()
        break
    except UnicodeDecodeError as e:
        print(f"  ❌ Error UTF-8 en posición {e.start}: byte 0x{e.object[e.start]:02x}")
    except Exception as e:
        print(f"  ❌ Error: {type(e).__name__}: {e}")

print()

# 3. Intentar conexión a nivel de socket TCP (sin psycopg2)
print("3. VERIFICACIÓN DE CONEXIÓN TCP A POSTGRESQL")
print("-" * 80)

try:
    import socket

    print(f"Intentando conectar a {DB_HOST}:{DB_PORT}...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)

    result = sock.connect_ex((DB_HOST, int(DB_PORT)))

    if result == 0:
        print("✓ Conexión TCP exitosa al servidor PostgreSQL")

        # Recibir mensaje inicial del servidor
        print("\nRecibiendo mensaje inicial del servidor...")
        try:
            data = sock.recv(1024)
            print(f"  Bytes recibidos: {len(data)}")
            print(f"  Primeros 100 bytes (hex): {data[:100].hex()}")
            print(f"  Primeros 100 bytes (raw): {data[:100]}")

            # Buscar el byte 0xab
            if b'\xab' in data:
                posiciones = [i for i, b in enumerate(data) if b == 0xab]
                print(f"\n  ⚠️  Se encontró el byte 0xab en posiciones: {posiciones}")
                for pos in posiciones[:3]:  # Mostrar primeras 3 ocurrencias
                    contexto_inicio = max(0, pos - 10)
                    contexto_fin = min(len(data), pos + 10)
                    print(f"    Contexto en posición {pos}: {data[contexto_inicio:contexto_fin].hex()}")
            else:
                print("  ✓ No se encontró el byte 0xab en el mensaje inicial")

        except socket.timeout:
            print("  ⚠️  Timeout esperando respuesta del servidor")
        except Exception as e:
            print(f"  ❌ Error al recibir datos: {e}")

        sock.close()
    else:
        print(f"❌ No se pudo conectar al servidor (código de error: {result})")

except Exception as e:
    print(f"❌ Error en conexión TCP: {e}")

print()
print("=" * 80)
print("FIN DEL DIAGNÓSTICO")
print("=" * 80)

print()
print("RECOMENDACIONES:")
print()
print("Si la conexión TCP funciona pero psycopg2 falla, el problema está en:")
print("  1. La configuración de encoding del servidor PostgreSQL")
print("  2. Una incompatibilidad de psycopg2 con el servidor en Windows")
print()
print("SOLUCIÓN SUGERIDA:")
print("  1. Verificar encoding del servidor PostgreSQL en Windows")
print("  2. Intentar reinstalar psycopg2-binary:")
print("     pip uninstall psycopg2 psycopg2-binary")
print("     pip install psycopg2-binary")
print()
