# -*- coding: utf-8 -*-
from flask import Blueprint, render_template
from models import db, Pago, Gasto, Estudiante, PagoPersonal
from sqlalchemy import func, or_, and_
from datetime import datetime, timedelta

caja_bp = Blueprint('caja', __name__, template_folder='templates/caja')

@caja_bp.route('/')
def index():
    hoy = datetime.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    
    if hoy.month == 1:
        inicio_mes_pasado = hoy.replace(year=hoy.year-1, month=12, day=1)
        fin_mes_pasado = hoy.replace(year=hoy.year-1, month=12, day=31)
    else:
        inicio_mes_pasado = hoy.replace(month=hoy.month-1, day=1)
        fin_mes_pasado = hoy.replace(day=1) - timedelta(days=1)

    # INGRESOS
    ingresos_dia = db.session.query(func.sum(Pago.monto_pagado)).filter(
        func.date(Pago.fecha_pago) == hoy, Pago.estado=='Pagado'
    ).scalar() or 0
    
    ingresos_semana = db.session.query(func.sum(Pago.monto_pagado)).filter(
        Pago.fecha_pago >= inicio_semana, Pago.estado=='Pagado'
    ).scalar() or 0
    
    ingresos_mes = db.session.query(func.sum(Pago.monto_pagado)).filter(
        Pago.fecha_pago >= inicio_mes, Pago.estado=='Pagado'
    ).scalar() or 0
    
    ingresos_mes_pasado = db.session.query(func.sum(Pago.monto_pagado)).filter(
        Pago.fecha_pago >= inicio_mes_pasado, 
        Pago.fecha_pago <= fin_mes_pasado, 
        Pago.estado=='Pagado'
    ).scalar() or 0

    # EGRESOS - CORREGIDO: Ahora maneja TODAS las categorías reales
    gastos_mes = Gasto.query.filter(Gasto.fecha >= inicio_mes).all()
    
    gastos_luz = 0.0
    gastos_agua = 0.0
    gastos_internet = 0.0
    gastos_telefono = 0.0
    gastos_sueldos = 0.0
    gastos_papeleria = 0.0
    gastos_limpieza = 0.0
    gastos_mantenimiento = 0.0
    gastos_combustible = 0.0
    gastos_seguridad = 0.0
    gastos_eventos = 0.0
    gastos_impuestos = 0.0
    gastos_otros = 0.0
    
    for g in gastos_mes:
        cat = (g.categoria or '').lower()
        if 'luz' in cat or 'electricidad' in cat:
            gastos_luz += g.monto
        elif 'agua' in cat:
            gastos_agua += g.monto
        elif 'internet' in cat:
            gastos_internet += g.monto
        elif 'tel' in cat or 'telefono' in cat:
            gastos_telefono += g.monto
        elif 'sueldo' in cat or 'salario' in cat:
            gastos_sueldos += g.monto
        elif 'papeler' in cat:
            gastos_papeleria += g.monto
        elif 'limpieza' in cat:
            gastos_limpieza += g.monto
        elif 'manten' in cat:
            gastos_mantenimiento += g.monto
        elif 'combust' in cat:
            gastos_combustible += g.monto
        elif 'segur' in cat:
            gastos_seguridad += g.monto
        elif 'evento' in cat:
            gastos_eventos += g.monto
        elif 'impuesto' in cat:
            gastos_impuestos += g.monto
        else:
            gastos_otros += g.monto
    
    # Agregar pagos al personal
    pagos_personal_mes = PagoPersonal.query.filter(PagoPersonal.fecha_pago >= inicio_mes).all()
    total_pagos_personal = sum(p.monto_neto_pagado for p in pagos_personal_mes)
    gastos_sueldos += total_pagos_personal
    
    total_egresos_mes = sum(g.monto for g in gastos_mes) + total_pagos_personal

    # MOROSIDAD
    total_estudiantes = Estudiante.query.filter_by(estado='Activo').count()
    pagos_pendientes = Pago.query.filter_by(estado='Pendiente').all()
    monto_moroso = sum((p.monto_total - (p.descuento or 0)) - p.monto_pagado for p in pagos_pendientes)

    return render_template('caja/control.html',
        ingresos_dia=ingresos_dia, ingresos_semana=ingresos_semana,
        ingresos_mes=ingresos_mes, ingresos_mes_pasado=ingresos_mes_pasado,
        gastos_luz=gastos_luz, gastos_agua=gastos_agua,
        gastos_internet=gastos_internet, gastos_telefono=gastos_telefono,
        gastos_sueldos=gastos_sueldos, gastos_papeleria=gastos_papeleria,
        gastos_limpieza=gastos_limpieza, gastos_mantenimiento=gastos_mantenimiento,
        gastos_combustible=gastos_combustible, gastos_seguridad=gastos_seguridad,
        gastos_eventos=gastos_eventos, gastos_impuestos=gastos_impuestos,
        gastos_otros=gastos_otros, total_egresos_mes=total_egresos_mes,
        monto_moroso=monto_moroso, total_estudiantes=total_estudiantes
    )

@caja_bp.route('/reporte/turno/<int:turno_id>/previa')
def reporte_turno_previa(turno_id):
    """Vista previa formal en pantalla antes de imprimir el reporte de turno."""
    return render_template('caja/reporte_previa.html', turno_id=turno_id)

@caja_bp.route('/reporte/general/previa')
def reporte_general_previa():
    """Vista previa formal en pantalla del reporte general de caja."""
    return render_template('caja/reporte_general_previa.html')