# -*- coding: utf-8 -*-
"""
==============================================================================
Archivo: routes/auth.py
Proyecto: ASestud-Konetz - Sistema de Gestión Escolar
Basado en: Colegio Dr. Antonio Vaca Díez
Desarrollado por: Avrora Soft - Vibola LLC
==============================================================================
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import ConfiguracionInstitucion

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
        # Lógica de autenticación principal si corresponde, o redirección
        return redirect(url_for('auth.login_turno'))
    
    return render_template('auth/login.html', institucion=institucion_dict)

@auth_bp.route('/login-turno', methods=['GET', 'POST'])
def login_turno():
    if request.method == 'POST':
        turno = request.form.get('turno')  # 'Mañana' o 'Tarde'
        password = request.form.get('password')
        
        # Contraseñas configuradas para cada turno
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