# -*- coding: utf-8 -*-
"""
==============================================================================
Archivo: routes/profesores.py
Proyecto: Sistema de Gestión Escolar - Colegio Dr. Antonio Vaca Díez
Desarrollado por: Avrora Soft - Vibola LLC
Descripción: Blueprint para la gestión integral del Cárdex Docente:
             Expediente profesional, carga horaria, asignaciones de materias,
             balance financiero y registro de pagos con validación estricta de turno.
==============================================================================
"""

import os
import io
from datetime import datetime

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, current_app, send_file, session
)
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from models import (
    db, Profesor, PagoPersonal, Materia,
    CURSOS_POR_NIVEL, NIVELES, TURNOS
)

profesores_bp = Blueprint(
    'profesores',
    __name__,
    url_prefix='/personal',
    template_folder='templates/profesores'
)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'tif', 'tiff', 'webp', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def asegurar_turno_activo():
    """Valida estrictamente que exista un turno activo en sesión o rol de superadmin.
    Cero asignaciones automáticas de turno bajo ninguna circunstancia."""
    turno = session.get('turno_activo')
    rol = session.get('rol')

    if not turno and rol != 'superadmin':
        return False
    return True


# ==============================================================================
# LISTA GENERAL DE PROFESORES CON FILTROS EN TIEMPO REAL
# ==============================================================================

@profesores_bp.route('/')
def index():
    q = request.args.get('q', '').strip()
    filtro_estado = request.args.get('estado', '').strip()
    filtro_turno = request.args.get('turno', '').strip()
    filtro_nivel = request.args.get('nivel', '').strip()

    query = Profesor.query.options(joinedload(Profesor.materias))

    if q:
        termino = f"%{q}%"
        query = query.filter(
            or_(
                Profesor.ci.ilike(termino),
                Profesor.nombres.ilike(termino),
                Profesor.apellidos.ilike(termino),
                Profesor.especialidad.ilike(termino)
            )
        )

    if filtro_estado:
        query = query.filter(Profesor.estado == filtro_estado)

    if filtro_turno:
        query = query.filter(Profesor.turno == filtro_turno)

    if filtro_nivel:
        query = query.filter(Profesor.nivel == filtro_nivel)

    profesores = query.order_by(Profesor.apellidos.asc(), Profesor.nombres.asc()).all()

    # Métricas para las tarjetas de resumen
    todos = Profesor.query.all()
    total_docentes = len(todos)
    total_activos = sum(1 for p in todos if getattr(p, 'estado', 'Activo') == 'Activo')
    total_materias_asignadas = Materia.query.filter(Materia.profesor_id.isnot(None)).count()

    return render_template(
        'profesores/index.html',
        profesores=profesores,
        q=q,
        filtro_estado=filtro_estado,
        filtro_turno=filtro_turno,
        filtro_nivel=filtro_nivel,
        total_docentes=total_docentes,
        total_activos=total_activos,
        total_materias_asignadas=total_materias_asignadas,
        niveles_disponibles=NIVELES if 'NIVELES' in globals() else ['Primaria', 'Secundaria'],
        turnos_disponibles=TURNOS if 'TURNOS' in globals() else ['Mañana', 'Tarde', 'Noche']
    )


@profesores_bp.route('/profesores')
def listar_profesores():
    return redirect(url_for('profesores.index'))


@profesores_bp.route('/administrativos')
def listar_administrativos():
    flash('ℹ️ Accediendo al listado general de personal.', 'info')
    return redirect(url_for('profesores.index'))


# ==============================================================================
# NUEVO PROFESOR (CON COLUMNAS EXACTAS DE LA BASE DE DATOS)
# ==============================================================================

@profesores_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_profesor():
    if request.method == 'POST':
        try:
            ci = request.form.get('ci', '').strip()
            nombres = request.form.get('nombres', '').strip()
            apellidos = request.form.get('apellidos', '').strip()
            especialidad = request.form.get('especialidad', '').strip()
            nivel = request.form.get('nivel', '').strip()
            turno = request.form.get('turno', '').strip()
            telefono = request.form.get('telefono', '').strip()
            correo = request.form.get('correo', '').strip()
            estado = request.form.get('estado', 'Activo').strip()
            sueldo_str = request.form.get('salario_base') or request.form.get('sueldo', '0')

            if not ci or not nombres or not apellidos:
                flash('⚠️ C.I., Nombres y Apellidos son obligatorios.', 'warning')
                return render_template('profesores/nuevo.html')

            existente = Profesor.query.filter_by(ci=ci).first()
            if existente:
                flash(f'⚠️ Ya existe un docente registrado con el C.I. {ci}.', 'danger')
                return render_template('profesores/nuevo.html')

            try:
                salario_base = float(sueldo_str) if sueldo_str else 0.0
            except ValueError:
                salario_base = 0.0

            nuevo = Profesor(
                ci=ci,
                nombres=nombres,
                apellidos=apellidos,
                especialidad=especialidad,
                nivel=nivel,
                turno=turno,
                telefono=telefono,
                correo=correo,
                salario_base=salario_base,
                adelanto=0.0,
                salario_neto=salario_base,
                estado=estado
            )

            db.session.add(nuevo)
            db.session.commit()

            flash(f'✅ Docente {nuevo.apellidos}, {nuevo.nombres} registrado exitosamente.', 'success')
            return redirect(url_for('profesores.ver_profesor', id=nuevo.id))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al registrar el docente: {str(e)}', 'danger')

    return render_template(
        'profesores/nuevo.html',
        niveles_disponibles=NIVELES if 'NIVELES' in globals() else ['Primaria', 'Secundaria'],
        turnos_disponibles=TURNOS if 'TURNOS' in globals() else ['Mañana', 'Tarde', 'Noche']
    )


# ==============================================================================
# KÁRDEX / VER PERFIL DE PROFESOR (INTEGRAL: EXPEDIENTE, MATERIAS Y PAGOS)
# ==============================================================================

@profesores_bp.route('/ver/<int:id>')
def ver_profesor(id):
    profesor = Profesor.query.options(joinedload(Profesor.materias)).get_or_404(id)
    materias = profesor.materias if profesor.materias else []

    pagos = PagoPersonal.query.filter_by(
        tipo='Profesor',
        persona_id=id
    ).order_by(PagoPersonal.fecha_pago.desc(), PagoPersonal.id.desc()).all()

    anio_actual = datetime.now().year
    salario_base = float(profesor.salario_base or 0.0)
    adelanto = float(profesor.adelanto or 0.0)

    total_pagado_historico = sum(float(p.monto_neto_pagado or 0.0) for p in pagos if p.estado == 'Pagado')
    pagos_este_anio = [p for p in pagos if p.anio == anio_actual and p.estado == 'Pagado']
    total_pagado_anio = sum(float(p.monto_neto_pagado or 0.0) for p in pagos_este_anio)
    meses_pagados_anio = [p.mes for p in pagos_este_anio]

    return render_template(
        'profesores/ver.html',
        profesor=profesor,
        materias=materias,
        pagos=pagos,
        salario_base=salario_base,
        adelanto=adelanto,
        total_pagado_historico=total_pagado_historico,
        total_pagado_anio=total_pagado_anio,
        meses_pagados_anio=meses_pagados_anio,
        anio_actual=anio_actual,
        total_materias=len(materias)
    )


# ==============================================================================
# EDITAR EXPEDIENTE DE PROFESOR
# ==============================================================================

@profesores_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_profesor(id):
    profesor = Profesor.query.get_or_404(id)

    if request.method == 'POST':
        try:
            profesor.nombres = request.form.get('nombres', profesor.nombres).strip()
            profesor.apellidos = request.form.get('apellidos', profesor.apellidos).strip()
            profesor.ci = request.form.get('ci', profesor.ci).strip()
            profesor.especialidad = request.form.get('especialidad', profesor.especialidad).strip()
            profesor.nivel = request.form.get('nivel', profesor.nivel).strip()
            profesor.turno = request.form.get('turno', profesor.turno).strip()
            profesor.telefono = request.form.get('telefono', profesor.telefono).strip()
            profesor.correo = request.form.get('correo', profesor.correo).strip()
            profesor.estado = request.form.get('estado', profesor.estado).strip()

            sueldo_str = request.form.get('salario_base') or request.form.get('sueldo', '0')
            try:
                profesor.salario_base = float(sueldo_str) if sueldo_str else 0.0
            except ValueError:
                pass

            db.session.commit()
            flash('✅ Expediente del docente actualizado correctamente.', 'success')
            return redirect(url_for('profesores.ver_profesor', id=profesor.id))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al actualizar expediente: {str(e)}', 'danger')

    return render_template(
        'profesores/editar.html',
        profesor=profesor,
        niveles_disponibles=NIVELES if 'NIVELES' in globals() else ['Primaria', 'Secundaria'],
        turnos_disponibles=TURNOS if 'TURNOS' in globals() else ['Mañana', 'Tarde', 'Noche']
    )


# ==============================================================================
# REGISTRAR PAGO / SUELDO (ESTRICTAMENTE BLINDADO CON TURNO DE CAJA)
# ==============================================================================

@profesores_bp.route('/pagar/<int:id>', methods=['GET', 'POST'])
def pagar_profesor(id):
    if not asegurar_turno_activo():
        flash('❌ Transacción bloqueada: El sistema no cuenta con un turno activo. Debe iniciar sesión manualmente en un turno para procesar pagos a docentes.', 'danger')
        return redirect(url_for('profesores.ver_profesor', id=id))

    turno_actual = session.get('turno_activo')
    responsable_turno = turno_actual if turno_actual else 'Superadmin'

    profesor = Profesor.query.get_or_404(id)
    anio_actual = datetime.now().year

    meses_todos = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]

    pagos_existentes = PagoPersonal.query.filter_by(
        tipo='Profesor',
        persona_id=id,
        anio=anio_actual,
        estado='Pagado'
    ).all()

    meses_pagados = [p.mes for p in pagos_existentes]
    meses_pendientes = [m for m in meses_todos if m not in meses_pagados]

    if request.method == 'POST':
        meses_seleccionados = request.form.getlist('meses_a_pagar')
        monto_str = request.form.get('monto', '0')
        metodo_pago = request.form.get('metodo_pago', 'Efectivo').strip()

        if metodo_pago not in ['Efectivo', 'Bancario']:
            metodo_pago = 'Efectivo'

        base_sueldo = float(profesor.salario_base or 0.0)

        try:
            monto_personalizado = float(monto_str) if monto_str else base_sueldo
        except ValueError:
            monto_personalizado = base_sueldo

        if not meses_seleccionados:
            flash('⚠️ Seleccione al menos un mes para registrar el pago.', 'warning')
            return redirect(url_for('profesores.pagar_profesor', id=id))

        try:
            for mes in meses_seleccionados:
                pago_existente = PagoPersonal.query.filter_by(
                    tipo='Profesor',
                    persona_id=id,
                    anio=anio_actual,
                    mes=mes
                ).first()

                if pago_existente:
                    pago_existente.estado = 'Pagado'
                    pago_existente.monto_neto_pagado = monto_personalizado
                    pago_existente.fecha_pago = datetime.now().date()
                    pago_existente.metodo_pago = metodo_pago
                else:
                    nuevo_pago = PagoPersonal(
                        tipo='Profesor',
                        persona_id=id,
                        ci_persona=profesor.ci,
                        nombre_persona=f"{profesor.apellidos}, {profesor.nombres}",
                        mes=mes,
                        anio=anio_actual,
                        monto_base=base_sueldo,
                        monto_adelanto=float(getattr(profesor, 'adelanto', 0.0) or 0.0),
                        monto_neto_pagado=monto_personalizado,
                        fecha_pago=datetime.now().date(),
                        metodo_pago=metodo_pago,
                        estado='Pagado'
                    )
                    db.session.add(nuevo_pago)

            db.session.commit()
            flash(f'✅ Pago al docente registrado exitosamente (Turno: {responsable_turno}).', 'success')
            return redirect(url_for('profesores.ver_profesor', id=id))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al procesar el pago: {str(e)}', 'danger')
            return redirect(url_for('profesores.pagar_profesor', id=id))

    return render_template(
        'profesores/pagar.html',
        profesor=profesor,
        meses_pendientes=meses_pendientes,
        anio=anio_actual
    )


# ==============================================================================
# ELIMINAR PROFESOR
# ==============================================================================

@profesores_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_profesor(id):
    try:
        profesor = Profesor.query.get_or_404(id)

        # Desvincular materias antes de eliminar para mantener integridad referencial
        for materia in profesor.materias:
            materia.profesor_id = None

        db.session.delete(profesor)
        db.session.commit()
        flash(f'✅ El docente {profesor.apellidos}, {profesor.nombres} fue eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error al eliminar el registro: {str(e)}', 'danger')

    return redirect(url_for('profesores.index'))