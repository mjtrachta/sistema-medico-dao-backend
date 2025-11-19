"""
Test simple de conexión pg8000
"""
import pg8000

print("Test 1: Conexión directa con strings literales")
try:
    conn = pg8000.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres123',
        database='turnos_medicos_dao'
    )
    print("✓ ÉXITO - Conexión establecida")
    cur = conn.cursor()
    cur.execute("SELECT version()")
    version = cur.fetchone()[0]
    print(f"✓ PostgreSQL version: {version[:50]}...")
    conn.close()
except Exception as e:
    print(f"✗ ERROR: {e}")

print("\nTest 2: Conexión con bytes")
try:
    conn = pg8000.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres123',
        database=b'turnos_medicos_dao'
    )
    print("✓ ÉXITO - Conexión con bytes")
    conn.close()
except Exception as e:
    print(f"✗ ERROR: {e}")
