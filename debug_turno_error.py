"""
Script para debuggear el error 500 en POST /api/turnos
Reproduce exactamente la petición del usuario
"""
import requests
import json

# Configuración exacta del usuario
BASE_URL = "http://localhost:5001"
BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc2MzU4OTc4OSwianRpIjoiM2NiMzgxNmUtNjJhNy00YzU0LTg1OGQtNmJkZDA0Njg3NzlhIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjkiLCJuYmYiOjE3NjM1ODk3ODksImNzcmYiOiJiMzBiZjMwOS1iOGMzLTQxZWUtYTQ5NS01NzNmYmNlODY1MDkiLCJleHAiOjE3NjM1OTMzODksInJvbCI6InBhY2llbnRlIn0.6JeCRrnquC-vaIp9CR2cmaBji1QBm0cFZFslHjzpDHU"

# Body exacto del usuario (corrigiendo tipos de datos)
REQUEST_BODY = {
    "medico_id": "1",        # String - para probar la conversión automática 
    "ubicacion_id": "1",     # String - para probar la conversión automática
    "fecha": "2025-11-19",
    "hora": "14:30", 
    "duracion_min": 30,
    "motivo_consulta": "14:30"
}

# Body con tipos correctos (para comparar)
REQUEST_BODY_FIXED = {
    "medico_id": 1,          # Integer - tipo correcto
    "ubicacion_id": 1,       # Integer - tipo correcto  
    "fecha": "2025-11-19",
    "hora": "14:30",
    "duracion_min": 30,
    "motivo_consulta": "14:30"
}

def test_health():
    """Test de health para verificar que el servidor está corriendo"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"✅ Server Health: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Server Health Error: {e}")
        return False

def test_turno_post(use_fixed_body=False):
    """Test exacto de la petición del usuario"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {BEARER_TOKEN}"
        }
        
        body = REQUEST_BODY_FIXED if use_fixed_body else REQUEST_BODY
        body_type = "con tipos correctos" if use_fixed_body else "original del usuario"
        
        print(f"🔍 Haciendo petición POST /api/turnos ({body_type})...")
        print(f"   Headers: {headers}")
        print(f"   Body: {json.dumps(body, indent=2)}")
        print()
        
        response = requests.post(
            f"{BASE_URL}/api/turnos",
            json=body,
            headers=headers,
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        print(f"📝 Response Text: {response.text}")
        
        if response.status_code == 500:
            print()
            print("🚨 ERROR 500 DETECTADO")
            print("   Revisa los logs del servidor Flask para ver el stack trace completo")
        elif response.status_code == 201:
            print()
            print("✅ TURNO CREADO EXITOSAMENTE")
        elif response.status_code == 400:
            print()
            print("⚠️ ERROR DE VALIDACIÓN")
        
        return response
        
    except Exception as e:
        print(f"❌ Error en petición: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("🐛 DEBUG: POST /api/turnos ERROR 500")
    print("=" * 60)
    print()
    
    # 1. Verificar servidor
    print("1️⃣ Verificando servidor...")
    if not test_health():
        print("❌ Servidor no disponible. Asegúrate de que Flask esté corriendo en localhost:5001")
        exit(1)
    
    print()
    
    # 2. Reproducir petición problemática
    print("2️⃣ Reproduciendo petición problemática...")
    response = test_turno_post(use_fixed_body=False)  # Primero con el body original
    
    print()
    print("=" * 60)
    
    if response and response.status_code == 500:
        print("🚨 CONFIRMADO: Error 500 reproducido con body original")
        print("   Probando con tipos de datos corregidos...")
        print()
        
        response2 = test_turno_post(use_fixed_body=True)  # Luego con tipos correctos
        
        if response2 and response2.status_code == 201:
            print("✅ PROBLEMA RESUELTO: Tipos de datos corregidos funcionan")
        elif response2 and response2.status_code != 500:
            print(f"✅ MEJOR: No hay error 500, código: {response2.status_code}")
        
    elif response and response.status_code != 500:
        print(f"✅ No hay error 500, código: {response.status_code}")
    else:
        print("❓ No se pudo completar la petición")