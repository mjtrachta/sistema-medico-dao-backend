from app import create_app
from models import db, Usuario, Medico

app = create_app('development')

with app.app_context():
    # Obtener médicos sin usuario
    medicos_sin_usuario = Medico.query.filter_by(usuario_id=None).all()
    
    for medico in medicos_sin_usuario:
        # Crear usuario para el médico
        nombre_usuario = f"{medico.nombre.lower()}.{medico.apellido.lower()}"
        email = f"{nombre_usuario}@hospital.com"
        
        # Verificar si ya existe el usuario
        usuario_existente = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()
        if usuario_existente:
            print(f"Usuario {nombre_usuario} ya existe")
            continue
        
        nuevo_usuario = Usuario(
            nombre_usuario=nombre_usuario,
            email=email,
            rol='medico'
        )
        # Password por defecto: Medico123
        nuevo_usuario.set_password('Medico123')
        
        db.session.add(nuevo_usuario)
        db.session.flush()
        
        # Asociar usuario al médico
        medico.usuario_id = nuevo_usuario.id
        medico.email = email
        
        print(f"✓ Usuario creado: {nombre_usuario} / Medico123")
        print(f"  Email: {email}")
        print(f"  Médico: Dr./Dra. {medico.nombre} {medico.apellido}")
        print(f"  Especialidad: {medico.especialidad.nombre if medico.especialidad else 'N/A'}")
        print()
    
    db.session.commit()
    print("✓ Usuarios de médicos creados exitosamente")
