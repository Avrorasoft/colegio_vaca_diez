# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Gasto
from datetime import datetime

gastos_bp = Blueprint('gastos', __name__, template_folder='templates/gastos')

CATEGORIAS = [
    'Luz', 'Agua', 'Internet', 'Teléfono',
    'Papelería', 'Limpieza', 'Mantenimiento',
    'Combustible', 'Seguridad', 'Eventos',
    'Sueldos', 'Impuestos', 'Otros'
]


@gastos_bp.route('/')
def index():
    search = request.args.get('search', '', type=str)
    mes_filtro = request.args.get('mes', '', type=str)
    anio_filtro = request.args.get('anio', type=int)

    query = Gasto.query

    if search:
        query = query.filter(
            db.or_(
                Gasto.descripcion.ilike(f'%{search}%'),
                Gasto.proveedor.ilike(f'%{search}%'),
                Gasto.categoria.ilike(f'%{search}%')
            )
        )

    if mes_filtro:
        query = query.filter(db.func.strftime('%m', Gasto.fecha) == mes_filtro.zfill(2))

    if anio_filtro:
        query = query.filter(db.func.strftime('%Y', Gasto.fecha) == str(anio_filtro))

    gastos = query.order_by(Gasto.fecha.desc()).all()

    total_general = sum(g.monto for g in gastos)

    resumen_categorias = {}

    for gasto in gastos:
        if gasto.categoria not in resumen_categorias:
            resumen_categorias[gasto.categoria] = 0
        resumen_categorias[gasto.categoria] += gasto.monto

    return render_template(
        'gastos/index.html',
        gastos=gastos,
        search=search,
        mes_filtro=mes_filtro,
        anio_filtro=anio_filtro,
        total_general=total_general,
        resumen=resumen_categorias,
        categorias=CATEGORIAS
    )


@gastos_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo():
    if request.method == 'POST':
        try:
            metodo_pago = request.form.get('metodo_pago', 'Efectivo').strip()
            if metodo_pago not in ['Efectivo', 'Bancario']:
                metodo_pago = 'Efectivo'

            nuevo_gasto = Gasto(
                categoria=request.form['categoria'],
                descripcion=request.form['descripcion'],
                monto=float(request.form['monto']),
                fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
                proveedor=request.form.get('proveedor', ''),
                responsable=request.form.get('responsable', ''),
                metodo_pago=metodo_pago
            )

            db.session.add(nuevo_gasto)
            db.session.commit()

            flash('✅ Gasto registrado exitosamente.', 'success')
            return redirect(url_for('gastos.index'))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al registrar: {str(e)}', 'danger')

    return render_template('gastos/form.html', gasto=None, categorias=CATEGORIAS)


@gastos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    # CANDADO: Solo admin y superadmin pueden modificar o eliminar gastos
    rol_actual = str(session.get('rol', '')).lower().strip()
    if rol_actual not in ['admin', 'superadmin', 'administrador']:
        flash('❌ Acceso denegado: Solo el Administrador o Superadmin pueden editar o anular gastos.', 'danger')
        return redirect(url_for('gastos.index'))
    gasto = Gasto.query.get_or_404(id)

    if request.method == 'POST':
        try:
            metodo_pago = request.form.get('metodo_pago', 'Efectivo').strip()
            if metodo_pago not in ['Efectivo', 'Bancario']:
                metodo_pago = 'Efectivo'

            gasto.categoria = request.form['categoria']
            gasto.descripcion = request.form['descripcion']
            gasto.monto = float(request.form['monto'])
            gasto.fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            gasto.proveedor = request.form.get('proveedor', '')
            gasto.responsable = request.form.get('responsable', '')
            gasto.metodo_pago = metodo_pago

            db.session.commit()

            flash('✅ Gasto actualizado.', 'success')
            return redirect(url_for('gastos.index'))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {str(e)}', 'danger')

    return render_template('gastos/form.html', gasto=gasto, categorias=CATEGORIAS)


@gastos_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    # CANDADO: Solo admin y superadmin pueden modificar o eliminar gastos
    rol_actual = str(session.get('rol', '')).lower().strip()
    if rol_actual not in ['admin', 'superadmin', 'administrador']:
        flash('❌ Acceso denegado: Solo el Administrador o Superadmin pueden editar o anular gastos.', 'danger')
        return redirect(url_for('gastos.index'))
    try:
        gasto = Gasto.query.get_or_404(id)

        db.session.delete(gasto)
        db.session.commit()

        flash('✅ Gasto eliminado.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error: {str(e)}', 'danger')

    return redirect(url_for('gastos.index'))


@gastos_bp.route('/reporte')
def reporte():
    anio = request.args.get('anio', type=int, default=datetime.now().year)

    gastos_anio = Gasto.query.filter(db.func.strftime('%Y', Gasto.fecha) == str(anio)).all()

    resumen = {}

    for gasto in gastos_anio:
        if gasto.categoria not in resumen:
            resumen[gasto.categoria] = 0
        resumen[gasto.categoria] += gasto.monto

    total_anio = sum(resumen.values())

    return render_template(
        'gastos/reporte.html',
        resumen=resumen,
        total=total_anio,
        anio=anio
    )


@gastos_bp.route('/comprobante/<int:gasto_id>')
def comprobante_gasto(gasto_id):
    """Muestra la vista previa formal del comprobante de gasto antes de imprimir."""
    gasto = Gasto.query.get_or_404(gasto_id)
    return render_template('gastos/comprobante.html', gasto=gasto)
