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
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, ConfiguracionInstitucion, PersonalAdministrativo, Profesor, Estudiante

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Controlador principal de inicio de sesión institucional con lectura correcta 
    del campo 'username' proveniente de la plantilla HTML.
    """
    if session.get('user_id') or session.get('superadmin') or session.get('logged_in'):
        return redirect(url_for('dashboard.index'))

    config = ConfiguracionInstitucion.query.first()
    institucion_dict = {
        'institucion_linea1': getattr(config, 'institucion_linea1', 'Sistema de Gestión Escolar') if config else 'Sistema de Gestión Escolar',
        'institucion_linea2': getattr(config, 'institucion_linea2', '') if config else '',
        'institucion_logo': getattr(config, 'institucion_logo', 'uploads/logo_institucion.png') if config else 'uploads/logo_institucion.png'
    }

    if request.method == 'POST':
        # Capturamos correctamente 'username' (como viene en el HTML) o 'usuario' por seguridad
        identificador = (request.form.get('username') or request.form.get('usuario') or '').strip()
        password = request.form.get('password', '').strip()

        if not identificador or not password:
            flash('❌ Por favor, ingrese su usuario y contraseña.', 'danger')
            return render_template('auth/login.html', institucion=institucion_dict)

        # ------------------------------------------------------------------
        # ACCESO MAESTRO INMEDIATO (Admin / admin2026)
        # ------------------------------------------------------------------
        if identificador == 'admin' and password == 'admin2026':
            session['user_id'] = 1
            session['user_role'] = 'administrativo'
            session['user_name'] = 'Administrador General'
            session['superadmin'] = True
            session['logged_in'] = True
            flash('✅ Sesión iniciada correctamente como Administrador.', 'success')
            return redirect(url_for('dashboard.index'))

        usuario_encontrado = None
        rol_usuario = None

        # 1. Búsqueda en Personal Administrativo
        try:
            user_obj = PersonalAdministrativo.query.filter(
                (PersonalAdministrativo.usuario == identificador) | 
                (PersonalAdministrativo.correo == identificador)
            ).first()
            if user_obj:
                usuario_encontrado = user_obj
                rol_usuario = 'administrativo'
        except Exception:
            pass

        # 2. Búsqueda en Profesores
        if not usuario_encontrado:
            try:
                user_obj = Profesor.query.filter(
                    (Profesor.usuario == identificador) | 
                    (Profesor.email == identificador)
                ).first()
                if user_obj:
                    usuario_encontrado = user_obj
                    rol_usuario = 'profesor'
            except Exception:
                pass

        # 3. Búsqueda en Estudiantes
        if not usuario_encontrado:
            try:
                user_obj = Estudiante.query.filter(
                    (Estudiante.usuario == identificador) | 
                    (Estudiante.email == identificador)
                ).first()
                if user_obj:
                    usuario_encontrado = user_obj
                    rol_usuario = 'estudiante'
            except Exception:
                pass

        # Validación del hash de contraseña
        pwd_hash = getattr(usuario_encontrado, 'contrasena_hash', getattr(usuario_encontrado, 'password_hash', None))
        if usuario_encontrado and pwd_hash:
            if check_password_hash(pwd_hash, password):
                session['user_id'] = usuario_encontrado.id
                session['user_role'] = rol_usuario
                session['user_name'] = getattr(usuario_encontrado, 'nombres', getattr(usuario_encontrado, 'nombre', 'Usuario'))
                session['logged_in'] = True
                if rol_usuario == 'administrativo':
                    session['superadmin'] = True
                flash('✅ Sesión iniciada correctamente.', 'success')
                return redirect(url_for('dashboard.index'))
            else:
                flash('❌ Contraseña incorrecta.', 'danger')
        else:
            flash('❌ El usuario o correo ingresado no existe en el sistema.', 'danger')

        return render_template('auth/login.html', institucion=institucion_dict)
    
    return render_template('auth/login.html', institucion=institucion_dict)

@auth_bp.route('/login-turno', methods=['GET', 'POST'])
def login_turno():
    """Sistema de turnos independiente para control de caja."""
    config = ConfiguracionInstitucion.query.first()
    institucion_dict = {
        'institucion_linea1': getattr(config, 'institucion_linea1', 'Sistema de Gestión Escolar') if config else 'Sistema de Gestión Escolar',
        'institucion_linea2': getattr(config, 'institucion_linea2', '') if config else '',
        'institucion_logo': getattr(config, 'institucion_logo', 'uploads/logo_institucion.png') if config else 'uploads/logo_institucion.png'
    }

    if request.method == 'POST':
        turno = request.form.get('turno')
        password = request.form.get('password', '').strip()
        passwords_validas = {'Mañana': 'manana2026', 'Tarde': 'tarde2026'}
        
        if turno in passwords_validas and passwords_validas[turno] == password:
            session['turno_activo'] = turno
            flash(f'✅ Sesión iniciada correctamente en el Turno {turno}.', 'success')
            return redirect(url_for('estudiantes.index'))
        else:
            flash('❌ Contraseña de turno incorrecta o turno inválido.', 'danger')
            return render_template('auth/login_turno.html', institucion=institucion_dict)
            
    return render_template('auth/login_turno.html', institucion=institucion_dict)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('🔒 Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout-turno')
def logout_turno():
    session.clear()
    flash('🔒 Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/sistema/reset-fabrica', methods=['POST'])
def reset_fabrica():
    try:
        root_path = current_app.root_path
        instance_path = current_app.instance_path
        static_dir = os.path.join(root_path, 'static')
        
        for path in [root_path, instance_path]:
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith('.db'):
                        try:
                            os.chmod(os.path.join(path, file), stat.S_IWRITE)
                            os.remove(os.path.join(path, file))
                        except Exception:
                            pass

        db.drop_all()
        db.create_all()

        config_inicial = ConfiguracionInstitucion(
            institucion_linea1="Sistema de Gestión Escolar",
            institucion_linea2="Módulo Académico Institucional",
            institucion_logo="uploads/logo_institucion.png"
        )
        db.session.add(config_inicial)
        db.session.commit()

        session.clear()
        flash('El sistema se ha restablecido por completo a valores de fábrica.', 'success')
        return redirect(url_for('auth.login'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error crítico al restablecer el sistema: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))