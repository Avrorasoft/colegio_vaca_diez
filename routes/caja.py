# -*- coding: utf-8 -*-
from flask import Blueprint, render_template
from models import db, Pago, Gasto, Estudiante, PagoPersonal
from sqlalchemy import func
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

    # INGRESOS: Ahora contabiliza cualquier pago o abono donde monto_pagado > 0
    ingresos_dia = db.session.query(func.sum(Pago.monto_pagado)).filter(
        func.date(Pago.fecha_pago) == hoy, Pago.monto_pagado > 0
    ).scalar() or 0
    
    ingresos_semana = db.session.query(func.sum(Pago.monto_pagado)).filter(
        Pago.fecha_pago >= inicio_semana, Pago.monto_pagado > 0
    ).scalar() or 0
    
    ingresos_mes = db.session.query(func.sum(Pago.monto_pagado)).filter(
        Pago.fecha_pago >= inicio_mes, Pago.monto_pagado > 0
    ).scalar() or 0
    
    ingresos_mes_pasado = db.session.query(func.sum(Pago.monto_pagado)).filter(
        Pago.fecha_pago >= inicio_mes_pasado, 
        Pago.fecha_pago <= fin_mes_pasado, 
        Pago.monto_pagado > 0
    ).scalar() or 0

    # EGRESOS / GASTOS (CÁLCULO EXACTO POR PERIODOS)[cite: 1]
    egresos_dia = db.session.query(func.sum(Gasto.monto)).filter(
        func.date(Gasto.fecha) == hoy
    ).scalar() or 0

    egresos_semana = db.session.query(func.sum(Gasto.monto)).filter(
        Gasto.fecha >= inicio_semana
    ).scalar() or 0

    # Gastos del mes + Pagos de personal al mes[cite: 1]
    gastos_mes_total = db.session.query(func.sum(Gasto.monto)).filter(
        Gasto.fecha >= inicio_mes
    ).scalar() or 0

    pagos_personal_mes = PagoPersonal.query.filter(PagoPersonal.fecha_pago >= inicio_mes).all()
    total_pagos_personal = sum(p.monto_neto_pagado for p in pagos_personal_mes)
    
    total_egresos_mes = gastos_mes_total + total_pagos_personal

    # MOROSIDAD[cite: 1]
    total_estudiantes = Estudiante.query.filter_by(estado='Activo').count()
    pagos_pendientes = Pago.query.filter_by(estado='Pendiente').all()
    monto_moroso = sum((p.monto_total - (p.descuento or 0)) - p.monto_pagado for p in pagos_pendientes)

    # Lista de gastos recientes para mostrar en la tabla unificada de caja[cite: 1]
    gastos_recientes = Gasto.query.order_by(Gasto.fecha.desc()).limit(15).all()

    return render_template('caja/index.html',
        ingresos_dia=ingresos_dia, ingresos_semana=ingresos_semana,
        ingresos_mes=ingresos_mes, ingresos_mes_pasado=ingresos_mes_pasado,
        egresos_dia=egresos_dia, egresos_semana=egresos_semana,
        total_egresos_mes=total_egresos_mes,
        monto_moroso=monto_moroso, total_estudiantes=total_estudiantes,
        gastos_recientes=gastos_recientes
    )

@caja_bp.route('/reporte/turno/<int:turno_id>/previa')
def reporte_turno_previa(turno_id):
    return render_template('caja/reporte_previa.html', turno_id=turno_id)

@caja_bp.route('/reporte/general/previa')
def reporte_general_previa():
    return render_template('caja/reporte_general_previa.html')