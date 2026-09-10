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

auth_bp = Blueprint('auth', __name__)

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

@auth_bp.route('/logout-turno')
def logout_turno():
    session.pop('turno_activo', None)
    flash('Sesión de turno cerrada.', 'info')
    return redirect(url_for('auth.login_turno'))