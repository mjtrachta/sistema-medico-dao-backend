"""
Script para diagnosticar y reparar hashes de contraseñas corruptos.
Uso: python -m utils.fix_password_hashes
"""

from app import create_app
from models import db, Usuario
import sys

def diagnosticar_hashes():
    """Diagnostica problemas con hashes de contraseñas."""
    app = create_app('development')
    with app.app_context():
        usuarios = Usuario.query.all()
        print(f"\n{'='*60}")
        print(f"DIAGNÓSTICO DE HASHES DE CONTRASEÑAS")
        print(f"{'='*60}\n")
        print(f"Total de usuarios: {len(usuarios)}\n")

        problemas = []

        for usuario in usuarios:
            print(f"Usuario: {usuario.nombre_usuario}")
            print(f"  Email: {usuario.email}")
            print(f"  Rol: {usuario.rol}")

            # Verificar tipo de dato
            if usuario.hash_contrasena is None:
                print(f"  ❌ ERROR: Hash es None")
                problemas.append((usuario, "Hash es None"))
                continue

            # Verificar si es bytes en lugar de string
            if isinstance(usuario.hash_contrasena, bytes):
                print(f"  ⚠️  ADVERTENCIA: Hash almacenado como bytes")
                try:
                    # Intentar decodificar
                    hash_str = usuario.hash_contrasena.decode('utf-8')
                    print(f"  ✓ Se puede decodificar a string")
                except UnicodeDecodeError as e:
                    print(f"  ❌ ERROR: No se puede decodificar - {e}")
                    problemas.append((usuario, f"Hash corrupto: {e}"))
                    continue
            elif isinstance(usuario.hash_contrasena, str):
                print(f"  ✓ Hash es string (correcto)")
            else:
                print(f"  ❌ ERROR: Tipo inesperado: {type(usuario.hash_contrasena)}")
                problemas.append((usuario, f"Tipo inesperado: {type(usuario.hash_contrasena)}"))
                continue

            # Verificar formato
            hash_val = usuario.hash_contrasena
            if isinstance(hash_val, bytes):
                try:
                    hash_val = hash_val.decode('utf-8')
                except:
                    pass

            if isinstance(hash_val, str):
                print(f"  Longitud: {len(hash_val)} caracteres")
                if hash_val.startswith('scrypt:'):
                    print(f"  ✓ Formato scrypt correcto")
                elif hash_val.startswith('pbkdf2:'):
                    print(f"  ✓ Formato pbkdf2 correcto")
                else:
                    print(f"  ⚠️  Formato desconocido: {hash_val[:20]}...")

                # Intentar verificar con una contraseña de prueba
                try:
                    from werkzeug.security import check_password_hash
                    # No verificamos la contraseña real, solo que la función no lance error
                    check_password_hash(hash_val, "test_password_that_wont_match_123456")
                    print(f"  ✓ Hash puede ser verificado sin errores")
                except UnicodeDecodeError as e:
                    print(f"  ❌ ERROR al verificar: {e}")
                    problemas.append((usuario, f"Error de verificación: {e}"))
                except Exception as e:
                    # Otros errores son esperados (contraseña incorrecta, etc)
                    print(f"  ✓ Función de verificación ejecutable")

            print()

        if problemas:
            print(f"\n{'='*60}")
            print(f"RESUMEN DE PROBLEMAS ENCONTRADOS: {len(problemas)}")
            print(f"{'='*60}\n")
            for usuario, problema in problemas:
                print(f"• {usuario.nombre_usuario}: {problema}")
        else:
            print(f"\n{'='*60}")
            print(f"✓ NO SE ENCONTRARON PROBLEMAS")
            print(f"{'='*60}\n")

        return problemas

def resetear_password(nombre_usuario, nueva_password):
    """Resetea la contraseña de un usuario específico."""
    app = create_app('development')
    with app.app_context():
        usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()
        if not usuario:
            print(f"❌ Usuario '{nombre_usuario}' no encontrado")
            return False

        print(f"Reseteando contraseña para: {usuario.nombre_usuario}")
        usuario.set_password(nueva_password)

        # Verificar que el nuevo hash es correcto
        print(f"Nuevo hash generado: {usuario.hash_contrasena[:50]}...")
        print(f"Tipo: {type(usuario.hash_contrasena)}")

        db.session.commit()
        print(f"✓ Contraseña actualizada exitosamente")

        # Verificar que funciona
        if usuario.check_password(nueva_password):
            print(f"✓ Verificación exitosa")
            return True
        else:
            print(f"❌ La verificación falló")
            return False

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'reset' and len(sys.argv) >= 4:
            # python -m utils.fix_password_hashes reset <usuario> <nueva_password>
            resetear_password(sys.argv[2], sys.argv[3])
        else:
            print("Uso:")
            print("  python -m utils.fix_password_hashes              # Diagnosticar")
            print("  python -m utils.fix_password_hashes reset <usuario> <password>  # Resetear")
    else:
        diagnosticar_hashes()
