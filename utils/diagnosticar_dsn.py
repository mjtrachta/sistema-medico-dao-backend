"""
Script para diagnosticar problemas con el DSN de PostgreSQL.
Muestra el string de conexión y analiza qué está en la posición 96.
Uso: python -m utils.diagnosticar_dsn
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Leer variables de entorno
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres123')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'turnos_medicos_dao')

# Construir DSN exactamente como lo hace config.py
dsn = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

print("=" * 80)
print("DIAGNÓSTICO DE DSN (Database Source Name)")
print("=" * 80)
print()

# Mostrar variables individuales
print("Variables de entorno:")
print(f"  DB_USER     = '{DB_USER}'")
print(f"  DB_PASSWORD = '{DB_PASSWORD}'")
print(f"  DB_HOST     = '{DB_HOST}'")
print(f"  DB_PORT     = '{DB_PORT}'")
print(f"  DB_NAME     = '{DB_NAME}'")
print()

# Mostrar DSN completo
print("DSN construido:")
print(f"  {dsn}")
print(f"  Longitud total: {len(dsn)} caracteres")
print()

# Analizar posición 96
print("=" * 80)
print("ANÁLISIS DE POSICIÓN 96 (donde ocurre el error)")
print("=" * 80)
print()

if len(dsn) > 96:
    # Mostrar contexto alrededor de la posición 96
    start = max(0, 96 - 20)
    end = min(len(dsn), 96 + 20)

    print(f"Contexto (posiciones {start} a {end}):")
    print(f"  '{dsn[start:end]}'")
    print(f"   {' ' * (96 - start)}^ posición 96")
    print()

    print(f"Carácter en posición 96:")
    char_96 = dsn[96]
    print(f"  Carácter: '{char_96}'")
    print(f"  Código ASCII/Unicode: {ord(char_96)}")
    print(f"  Código hexadecimal: 0x{ord(char_96):02x}")
    print()

    # Mostrar bytes del DSN
    print("Bytes del DSN en posición 96:")
    try:
        dsn_bytes = dsn.encode('utf-8')
        print(f"  Byte en posición 96: 0x{dsn_bytes[96]:02x}")
        print(f"  Contexto de bytes alrededor de posición 96:")
        for i in range(max(0, 96-10), min(len(dsn_bytes), 96+10)):
            marker = " <-- POSICIÓN 96" if i == 96 else ""
            print(f"    Posición {i:3d}: 0x{dsn_bytes[i]:02x} ('{chr(dsn_bytes[i]) if 32 <= dsn_bytes[i] < 127 else '?'}'){marker}")
    except UnicodeEncodeError as e:
        print(f"  ❌ ERROR al codificar a UTF-8: {e}")
        print(f"  Esto sugiere que hay un carácter no válido en el DSN")
    print()
else:
    print(f"❌ El DSN solo tiene {len(dsn)} caracteres, no llega a la posición 96")
    print()

# Análisis adicional: buscar caracteres problemáticos
print("=" * 80)
print("ANÁLISIS DE CARACTERES ESPECIALES")
print("=" * 80)
print()

caracteres_especiales = []
for i, char in enumerate(dsn):
    code = ord(char)
    # Buscar caracteres fuera del rango ASCII estándar (0-127)
    if code > 127:
        caracteres_especiales.append((i, char, code))

if caracteres_especiales:
    print(f"⚠️  Se encontraron {len(caracteres_especiales)} caracteres no-ASCII:")
    for pos, char, code in caracteres_especiales:
        print(f"  Posición {pos}: '{char}' (Unicode: {code}, hex: 0x{code:04x})")
    print()
    print("RECOMENDACIÓN: Estos caracteres podrían estar causando problemas.")
    print("Verifica especialmente la contraseña (DB_PASSWORD) si contiene caracteres especiales.")
else:
    print("✓ No se encontraron caracteres no-ASCII en el DSN")
    print()

# Mostrar cada parte del DSN por separado
print("=" * 80)
print("DESGLOSE DEL DSN")
print("=" * 80)
print()

parts = [
    ("Protocolo", "postgresql://"),
    ("Usuario", DB_USER),
    ("Separador", ":"),
    ("Contraseña", DB_PASSWORD),
    ("Separador", "@"),
    ("Host", DB_HOST),
    ("Separador", ":"),
    ("Puerto", DB_PORT),
    ("Separador", "/"),
    ("Base de datos", DB_NAME),
]

posicion_actual = 0
for nombre, valor in parts:
    longitud = len(valor)
    print(f"{nombre:15s} (pos {posicion_actual:3d}-{posicion_actual+longitud-1:3d}): '{valor}'")
    if posicion_actual <= 96 < posicion_actual + longitud:
        offset = 96 - posicion_actual
        print(f"                {'':15s} ^ LA POSICIÓN 96 ESTÁ AQUÍ (offset {offset} en '{nombre}')")
    posicion_actual += longitud

print()
print("=" * 80)
