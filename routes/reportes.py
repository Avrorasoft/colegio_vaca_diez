# -*- coding: utf-8 -*-
"""
==============================================================================
Archivo: routes/reportes.py
Proyecto: Sistema de Gestión Escolar - Colegio Dr. Antonio Vaca Díez
Desarrollado por: Avrora Soft - Vibola LLC
Descripción: Módulo de reportes económicos por turno (Mañana/Tarde) y 
consolidado general para caja única (Ingresos, Gastos y Pagos al Personal).
==============================================================================
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash
from models import db, Pago, Gasto, PagoPersonal
from sqlalchemy import func, or_, and_

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes', template_folder='templates/reportes')

@reportes_bp.route('/economico/manana')
def economico_manana():
    """Reporte económico exclusivo del Turno Mañana (Ingresos y Egresos)"""
    if 'turno_activo' not in session:
        flash('Debe iniciar sesión para ver los reportes.', 'warning')
        return redirect(url_for('auth.login_turno'))
    
    # 1. Ingresos del Turno Mañana
    pagos = Pago.query.filter_by(turno_responsable='Mañana', estado='Pagado').order_by(Pago.fecha_pago.desc()).all()
    total = sum(p.monto_pagado for p in pagos)

    # 2. Egresos: Gastos Operativos
    gastos = Gasto.query.all()
    total_gastos = sum(g.monto for g in gastos)

    # 3. Egresos: Pagos al Personal
    pagos_personal = PagoPersonal.query.all()
    total_personal = sum(p.monto_neto_pagado for p in pagos_personal)

    total_egresos = total_gastos + total_personal
    balance_neto = total - total_egresos

    return render_template('reportes/economico.html', 
                           pagos=pagos,
                           gastos=gastos,
                           pagos_personal=pagos_personal,
                           total=total,
                           total_gastos=total_gastos,
                           total_personal=total_personal,
                           total_egresos=total_egresos,
                           balance_neto=balance_neto,
                           titulo='Reporte Económico - Turno Mañana',
                           turno='Mañana')

@reportes_bp.route('/economico/tarde')
def economico_tarde():
    """Reporte económico exclusivo del Turno Tarde (Ingresos y Egresos)"""
    if 'turno_activo' not in session:
        flash('Debe iniciar sesión para ver los reportes.', 'warning')
        return redirect(url_for('auth.login_turno'))

    # 1. Ingresos del Turno Tarde
    pagos = Pago.query.filter_by(turno_responsable='Tarde', estado='Pagado').order_by(Pago.fecha_pago.desc()).all()
    total = sum(p.monto_pagado for p in pagos)

    # 2. Egresos: Gastos Operativos
    gastos = Gasto.query.all()
    total_gastos = sum(g.monto for g in gastos)

    # 3. Egresos: Pagos al Personal
    pagos_personal = PagoPersonal.query.all()
    total_personal = sum(p.monto_neto_pagado for p in pagos_personal)

    total_egresos = total_gastos + total_personal
    balance_neto = total - total_egresos

    return render_template('reportes/economico.html', 
                           pagos=pagos,
                           gastos=gastos,
                           pagos_personal=pagos_personal,
                           total=total,
                           total_gastos=total_gastos,
                           total_personal=total_personal,
                           total_egresos=total_egresos,
                           balance_neto=balance_neto,
                           titulo='Reporte Económico - Turno Tarde',
                           turno='Tarde')

@reportes_bp.route('/economico/general')
def economico_general():
    """Reporte económico general consolidado (Mañana y Tarde - Ingresos y Egresos)"""
    if 'turno_activo' not in session:
        flash('Debe iniciar sesión para ver los reportes.', 'warning')
        return redirect(url_for('auth.login_turno'))

    # 1. Ingresos Generales
    pagos = Pago.query.filter_by(estado='Pagado').order_by(Pago.fecha_pago.desc()).all()
    total_general = sum(p.monto_pagado for p in pagos)
    
    total_manana = sum(p.monto_pagado for p in pagos if p.turno_responsable == 'Mañana')
    total_tarde = sum(p.monto_pagado for p in pagos if p.turno_responsable == 'Tarde')

    # 2. Egresos Generales (Gastos y Personal)
    gastos = Gasto.query.all()
    total_gastos = sum(g.monto for g in gastos)

    pagos_personal = PagoPersonal.query.all()
    total_personal = sum(p.monto_neto_pagado for p in pagos_personal)

    total_egresos = total_gastos + total_personal
    balance_general_neto = total_general - total_egresos
    
    return render_template('reportes/economico_general.html', 
                           pagos=pagos,
                           gastos=gastos,
                           pagos_personal=pagos_personal,
                           total_general=total_general,
                           total_manana=total_manana,
                           total_tarde=total_tarde,
                           total_gastos=total_gastos,
                           total_personal=total_personal,
                           total_egresos=total_egresos,
                           balance_general_neto=balance_general_neto,
                           titulo='Reporte Económico General')