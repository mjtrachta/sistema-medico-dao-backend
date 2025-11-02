from app import create_app
from flask_jwt_extended import create_access_token, decode_token

app = create_app('development')

with app.app_context():
    print("=== TEST VALIDACIÓN JWT ===")
    
    # Crear token
    identity = 4
    additional_claims = {"rol": "paciente"}
    access_token = create_access_token(identity=identity, additional_claims=additional_claims)
    
    print(f"Token creado: {access_token[:50]}...")
    
    # Intentar decodificar con Flask-JWT-Extended
    try:
        decoded = decode_token(access_token)
        print(f"\n✓ Token decodificado exitosamente con decode_token()")
        print(f"Payload: {decoded}")
    except Exception as e:
        print(f"\n✗ Error decodificando token con Flask-JWT-Extended: {e}")
        import traceback
        traceback.print_exc()
        
