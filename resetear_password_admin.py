#!/usr/bin/env python3
"""
Script para resetear la contraseña del usuario admin
"""
from app import create_app
from models.database import db
from models.usuario import Usuario

# Crear aplicación
app = create_app('development')

with app.app_context():
    # Buscar el usuario admin
    admin = Usuario.query.filter_by(email='admin@sistema.com').first()

    if admin:
        # Nueva contraseña
        nueva_password = 'Admin123'

        # Actualizar contraseña
        admin.set_password(nueva_password)
        db.session.commit()

        print("✓ Contraseña del admin reseteada exitosamente")
        print(f"  Usuario: {admin.nombre_usuario}")
        print(f"  Email: {admin.email}")
        print(f"  Nueva contraseña: {nueva_password}")
    else:
        print("✗ No se encontró el usuario admin@sistema.com")
