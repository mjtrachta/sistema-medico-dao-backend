"""
Script para crear la base de datos PostgreSQL si no existe.
Uso: python create_db.py
"""

import os
from dotenv import load_dotenv
import pg8000

load_dotenv()

DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres123')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'turnos_medicos_dao')

print("=" * 60)
print("CREACIÓN DE BASE DE DATOS")
print("=" * 60)
print()
print(f"Host: {DB_HOST}:{DB_PORT}")
print(f"Usuario: {DB_USER}")
print(f"Base de datos a crear: {DB_NAME}")
print()

try:
    # Conectarse a la base de datos 'postgres' (que siempre existe)
    print("Conectando a PostgreSQL...")
    conn = pg8000.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database='postgres'
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Verificar si la base de datos ya existe
    print(f"Verificando si '{DB_NAME}' existe...")
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", [DB_NAME])
    exists = cur.fetchone()

    if exists:
        print(f"✓ La base de datos '{DB_NAME}' ya existe")
    else:
        # Crear la base de datos
        print(f"Creando base de datos '{DB_NAME}'...")
        cur.execute(f'CREATE DATABASE "{DB_NAME}" ENCODING \'UTF8\'')
        print(f"✓ Base de datos '{DB_NAME}' creada exitosamente")

    cur.close()
    conn.close()

    # Verificar que podemos conectarnos a la nueva base de datos
    print()
    print(f"Verificando conexión a '{DB_NAME}'...")
    test_conn = pg8000.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    test_conn.close()
    print(f"✓ Conexión exitosa a '{DB_NAME}'")

    print()
    print("=" * 60)
    print("ÉXITO - La base de datos está lista")
    print("=" * 60)
    print()
    print("Ahora ejecuta:")
    print("  flask db upgrade     # Para aplicar migraciones")
    print("  flask run            # Para iniciar el servidor")
    print()

except Exception as e:
    print()
    print("=" * 60)
    print("ERROR")
    print("=" * 60)
    print(f"No se pudo crear la base de datos: {e}")
    print()
    import traceback
    traceback.print_exc()
    exit(1)
