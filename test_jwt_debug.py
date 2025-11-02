from app import create_app
from flask_jwt_extended import create_access_token

app = create_app('development')

with app.app_context():
    print("=== DEBUG JWT ===")
    print(f"JWT_SECRET_KEY: {app.config.get('JWT_SECRET_KEY')}")
    
    # Crear un token de prueba
    identity = 4
    additional_claims = {"rol": "paciente"}
    access_token = create_access_token(identity=identity, additional_claims=additional_claims)
    
    print(f"\nToken generado: {access_token[:50]}...")
    
    # Ahora vamos a intentar decodificar ese token usando PyJWT directamente
    import jwt
    try:
        decoded = jwt.decode(access_token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        print(f"\n✓ Token decodificado exitosamente con JWT_SECRET_KEY")
        print(f"Payload: {decoded}")
    except Exception as e:
        print(f"\n✗ Error decodificando token: {e}")
        
