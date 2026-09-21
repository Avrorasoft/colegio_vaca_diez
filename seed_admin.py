# -*- coding: utf-8 -*-
import os
from app import app
from models import db, PersonalAdministrativo
from werkzeug.security import generate_password_hash

with app.app_context():
    # Verificar si ya existe el usuario admin
    admin_existente = PersonalAdministrativo.query.filter_by(usuario='admin').first()
    
    if admin_existente:
        # Actualizar credenciales si ya existe
        admin_existente.contrasena_hash = generate_password_hash('admin2026')
        admin_existente.nombres = 'Administrador'
        admin_existente.apellidos = 'General'
        admin_existente.cargo = 'Superadministrador'
        admin_existente.estado = 'Activo'
        db.session.commit()
        print("✅ Usuario 'admin' actualizado correctamente en la base de datos.")
    else:
        # Crear nuevo administrador
        nuevo_admin = PersonalAdministrativo(
            ci='0000000',
            apellidos='General',
            nombres='Administrador',
            cargo='Superadministrador',
            usuario='admin',
            correo='admin@vacadiez.edu',
            contrasena_hash=generate_password_hash('admin2026'),
            estado='Activo'
        )
        db.session.add(nuevo_admin)
        db.session.commit()
        print("✅ Usuario 'admin' creado e insertado correctamente en la base de datos.")