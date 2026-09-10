# -*- coding: utf-8 -*-
"""
==============================================================================
Archivo: routes/pwa.py
Proyecto: Sistema de Gestión Escolar - Colegio Dr. Antonio Vaca Díez
Desarrollado por: Avrora Soft - Vibola LLC
Módulo: Acceso PWA para Padres de Familia / Tutores
        - Identificador: Cédula de Identidad (CI) del Tutor como Usuario.
        - Clave inicial universal: '1234'.
        - Cambio de contraseña voluntario por parte del tutor.
        - Reseteo administrativo de contraseña a '1234'.
==============================================================================
"""

import os
from datetime import datetime, timedelta, timezone
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, session, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Estudiante, Padre, Mensaje, Pago, Calificacion

pwa_bp = Blueprint('pwa', __name__, url_prefix='/pwa', template_folder='templates/pwa')

BOLIVIA_TZ = timezone(timedelta(hours=-4))


@pwa_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya cuenta con sesión abierta válida, ingresa directo al panel
    if 'padre_logueado' in session:
        return redirect(url_for('pwa.dashboard'))

    if request.method == 'POST':
        ci_tutor = request.form.get('ci', '').strip()
        contrasena = request.form.get('contrasena', '').strip()

        if not ci_tutor or not contrasena:
            flash('⚠️ Debe ingresar su Cédula de Identidad y su contraseña.', 'warning')
            return render_template('pwa/login.html')

        # Búsqueda directa del tutor por su CI
        padre = Padre.query.filter_by(ci=ci_tutor).first()

        if not padre:
            flash('❌ No se encontró ningún tutor registrado con el C.I. ingresado.', 'danger')
            return render_template('pwa/login.html')

        # Validación de contraseña (personalizada o universal 1234)
        clave_valida = False
        if hasattr(padre, 'verificar_clave'):
            clave_valida = padre.verificar_clave(contrasena)
        else:
            if not padre.contrasena_hash:
                clave_valida = (contrasena == '1234')
            else:
                clave_valida = check_password_hash(padre.contrasena_hash, contrasena)

        if not clave_valida:
            flash('❌ Contraseña incorrecta. (Si es su primer ingreso, utilice la contraseña universal 1234).', 'danger')
            return render_template('pwa/login.html')

        # Estudiante asociado
        estudiante = Estudiante.query.get(padre.estudiante_id)

        # Configuración de persistencia de sesión móvil (90 días)
        session.permanent = True
        current_app.permanent_session_lifetime = timedelta(days=90)

        session['padre_logueado'] = True
        session['padre_id'] = padre.id
        session['estudiante_id'] = estudiante.id if estudiante else None
        session['nombre_tutor'] = padre.nombres
        session['nombre_estudiante'] = f"{estudiante.nombres} {estudiante.apellidos}" if estudiante else "Estudiante"
        session['clave_universal_activa'] = (padre.contrasena_hash is None)

        flash(f'✅ Bienvenido/a {padre.nombres}', 'success')
        return redirect(url_for('pwa.dashboard'))

    return render_template('pwa/login.html')


@pwa_bp.route('/dashboard')
def dashboard():
    if 'padre_logueado' not in session:
        return redirect(url_for('pwa.login'))

    padre_id = session.get('padre_id')
    padre = Padre.query.get_or_404(padre_id)
    estudiante = Estudiante.query.get(padre.estudiante_id)

    # Estado de cuenta y comunicados
    pagos_pendientes = []
    monto_pendiente = 0.0
    mensajes_recientes = []

    if estudiante:
        pagos_pendientes = Pago.query.filter_by(estudiante_id=estudiante.id, estado='Pendiente').all()
        monto_pendiente = sum((p.monto_total - (p.descuento or 0.0)) for p in pagos_pendientes)
        mensajes_recientes = Mensaje.query.filter_by(estudiante_id=estudiante.id).order_by(Mensaje.fecha_envio.desc()).limit(5).all()

    es_clave_universal = (padre.contrasena_hash is None)

    return render_template(
        'pwa/dashboard.html',
        padre=padre,
        estudiante=estudiante,
        pagos_pendientes=pagos_pendientes,
        monto_pendiente=monto_pendiente,
        mensajes_recientes=mensajes_recientes,
        es_clave_universal=es_clave_universal
    )


@pwa_bp.route('/cambiar_contrasena', methods=['POST'])
def cambiar_contrasena():
    if 'padre_logueado' not in session:
        return redirect(url_for('pwa.login'))

    padre_id = session.get('padre_id')
    padre = Padre.query.get_or_404(padre_id)

    nueva_clave = request.form.get('nueva_contrasena', '').strip()
    confirmar_clave = request.form.get('confirmar_contrasena', '').strip()

    if not nueva_clave or len(nueva_clave) < 4:
        flash('⚠️ La nueva contraseña debe tener un mínimo de 4 caracteres.', 'warning')
        return redirect(url_for('pwa.dashboard'))

    if nueva_clave != confirmar_clave:
        flash('⚠️ Las contraseñas ingresadas no coinciden. Intente de nuevo.', 'warning')
        return redirect(url_for('pwa.dashboard'))

    try:
        if hasattr(padre, 'establecer_clave'):
            padre.establecer_clave(nueva_clave)
        else:
            padre.contrasena_hash = generate_password_hash(nueva_clave)

        db.session.commit()
        session['clave_universal_activa'] = False
        flash('✅ Su contraseña ha sido personalizada exitosamente. Utilícela en sus próximos ingresos.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error al cambiar la contraseña: {str(e)}', 'danger')

    return redirect(url_for('pwa.dashboard'))


@pwa_bp.route('/restablecer_clave/<int:padre_id>', methods=['POST'])
def restablecer_clave_padre(padre_id):
    """
    Ruta administrativa para que Secretaría / Superadmin devuelva
    la clave del tutor a la contraseña universal '1234'.
    """
    rol = session.get('rol')
    es_super = session.get('es_superadmin')

    if rol not in ['admin', 'superadmin'] and not es_super:
        flash('❌ Acción no autorizada.', 'danger')
        return redirect('/')

    padre = Padre.query.get_or_404(padre_id)
    try:
        if hasattr(padre, 'restablecer_clave_universal'):
            padre.restablecer_clave_universal()
        else:
            padre.contrasena_hash = None

        db.session.commit()
        flash(f'✅ Acceso restablecido: El tutor {padre.nombres} ahora puede ingresar nuevamente con la clave 1234.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error al restablecer la contraseña: {str(e)}', 'danger')

    return redirect(request.referrer or url_for('dashboard.index'))


@pwa_bp.route('/logout')
def logout():
    session.clear()
    flash('👋 Sesión cerrada correctamente.', 'info')
    return redirect(url_for('pwa.login'))