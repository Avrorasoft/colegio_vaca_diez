# -*- coding: utf-8 -*-
"""
==============================================================================
Archivo: routes/reportes.py
Proyecto: Sistema de Gestión Escolar - Colegio Dr. Antonio Vaca Díez
Desarrollado por: Avrora Soft - Vibola LLC
Descripción: Módulo de reportes económicos por turno (Mañana/Tarde) y 
             consolidado general para caja única.
==============================================================================
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash
from models import db, Pago
from sqlalchemy import func, or_, and_
reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes', template_folder='templates/reportes')

@reportes_bp.route('/economico/manana')
def economico_manana():
    """Reporte económico exclusivo del Turno Mañana"""
    if 'turno_activo' not in session:
        flash('Debe iniciar sesión para ver los reportes.', 'warning')
        return redirect(url_for('auth.login_turno'))
        
    pagos = Pago.query.filter_by(turno_responsable='Mañana', estado='Pagado').order_by(Pago.fecha_pago.desc()).all()
    total = sum(p.monto_pagado for p in pagos)
    return render_template('reportes/economico.html', 
                           pagos=pagos, 
                           total=total, 
                           titulo='Reporte Económico - Turno Mañana',
                           turno='Mañana')

@reportes_bp.route('/economico/tarde')
def economico_tarde():
    """Reporte económico exclusivo del Turno Tarde"""
    if 'turno_activo' not in session:
        flash('Debe iniciar sesión para ver los reportes.', 'warning')
        return redirect(url_for('auth.login_turno'))

    pagos = Pago.query.filter_by(turno_responsable='Tarde', estado='Pagado').order_by(Pago.fecha_pago.desc()).all()
    total = sum(p.monto_pagado for p in pagos)
    return render_template('reportes/economico.html', 
                           pagos=pagos, 
                           total=total, 
                           titulo='Reporte Económico - Turno Tarde',
                           turno='Tarde')

@reportes_bp.route('/economico/general')
def economico_general():
    """Reporte económico general consolidado (Mañana y Tarde)"""
    if 'turno_activo' not in session:
        flash('Debe iniciar sesión para ver los reportes.', 'warning')
        return redirect(url_for('auth.login_turno'))

    pagos = Pago.query.filter_by(estado='Pagado').order_by(Pago.fecha_pago.desc()).all()
    total_general = sum(p.monto_pagado for p in pagos)
    
    # Desglose exacto de recaudación por turno
    total_manana = sum(p.monto_pagado for p in pagos if p.turno_responsable == 'Mañana')
    total_tarde = sum(p.monto_pagado for p in pagos if p.turno_responsable == 'Tarde')
    
    return render_template('reportes/economico_general.html', 
                           pagos=pagos, 
                           total_general=total_general, 
                           total_manana=total_manana, 
                           total_tarde=total_tarde, 
                           titulo='Reporte Económico General')