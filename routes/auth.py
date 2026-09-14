# -*- coding: utf-8 -*-
"""
==============================================================================
Archivo: routes/auth.py
Proyecto: ASestud-Konetz - Sistema de Gestión Escolar
Desarrollado por: Avrora Soft - Vibola LLC
==============================================================================
"""

import os
import time
import stat
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models import db, ConfiguracionInstitucion

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    config = ConfiguracionInstitucion.query.first()
    institucion_dict = {
        'institucion_linea1': getattr(config, 'institucion_linea1', 'Sistema de Gestión Escolar') if config else 'Sistema de Gestión Escolar',
        'institucion_linea2': getattr(config, 'institucion_linea2', '') if config else '',
        'institucion_logo': getattr(config, 'institucion_logo', 'uploads/logo_institucion.png') if config else 'uploads/logo_institucion.png'
    }

    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        return redirect(url_for('auth.login_turno'))
    
    return render_template('auth/login.html', institucion=institucion_dict)

@auth_bp.route('/login-turno', methods=['GET', 'POST'])
def login_turno():
    if request.method == 'POST':
        turno = request.form.get('turno')  # 'Mañana' o 'Tarde'
        password = request.form.get('password')
        
        passwords_validas = {
            'Mañana': 'manana2026',
            'Tarde': 'tarde2026'
        }
        
        if turno in passwords_validas and passwords_validas[turno] == password:
            session['turno_activo'] = turno
            flash(f'Sesión iniciada correctamente en el Turno {turno}.', 'success')
            return redirect(url_for('estudiantes.index'))
        else:
            flash('Contraseña incorrecta o turno inválido.', 'danger')
            
    return render_template('auth/login_turno.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout-turno')
def logout_turno():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/sistema/reset-fabrica', methods=['POST'])
def reset_fabrica():
    try:
        root_path = current_app.root_path
        instance_path = current_app.instance_path
        static_dir = os.path.join(root_path, 'static')

        # 1. Carpetas exactas a vaciar por completo
        carpetas_objetivo = [
            os.path.join(static_dir, 'recibos_personal'),
            os.path.join(static_dir, 'uploads'),
            os.path.join(static_dir, 'backups'),
            os.path.join(static_dir, 'boletines'),
            os.path.join(static_dir, 'recibos')
        ]

        # 2. Barrido archivo por archivo con tolerancia a fallos y desbloqueo de Windows
        for carpeta in carpetas_objetivo:
            if os.path.exists(carpeta):
                for root_dir, dirs, files in os.walk(carpeta, topdown=False):
                    for filename in files:
                        file_path = os.path.join(root_dir, filename)
                        for intento in range(3):
                            try:
                                # Forzar permisos de escritura para evitar bloqueos de Windows
                                os.chmod(file_path, stat.S_IWRITE)
                                os.remove(file_path)
                                break
                            except PermissionError:
                                time.sleep(0.1)
                            except Exception:
                                break
                    # Intentar limpiar subdirectorios vacíos
                    for dirname in dirs:
                        dir_path = os.path.join(root_dir, dirname)
                        try:
                            os.rmdir(dir_path)
                        except Exception:
                            pass

        # 3. Asegurar que la estructura base exista y regenerar un logo limpio en uploads
        uploads_dir = os.path.join(static_dir, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        default_logo_path = os.path.join(uploads_dir, 'logo_institucion.png')
        if not os.path.exists(default_logo_path):
            with open(default_logo_path, 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\r')

        # 4. Eliminar bases de datos SQLite (.db) físicas en raíz e instancia
        paths_to_check = [root_path, instance_path]
        for path in paths_to_check:
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith('.db'):
                        db_path = os.path.join(path, file)
                        try:
                            os.chmod(db_path, stat.S_IWRITE)
                            os.remove(db_path)
                        except Exception:
                            pass

        # 5. Reiniciar esquema de la base de datos con SQLAlchemy
        db.drop_all()
        db.create_all()

        # 6. Insertar configuración institucional inicial neutra
        config_inicial = ConfiguracionInstitucion(
            institucion_linea1="Sistema de Gestión Escolar",
            institucion_linea2="Módulo Académico Institucional",
            institucion_logo="uploads/logo_institucion.png"
        )
        db.session.add(config_inicial)
        db.session.commit()

        # 7. Limpiar sesión y redirigir
        session.clear()
        flash('El sistema se ha restablecido por completo a valores de fábrica.', 'success')
        return redirect(url_for('auth.login'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error crítico al restablecer el sistema: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))