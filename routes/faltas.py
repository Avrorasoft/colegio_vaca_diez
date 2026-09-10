# -*- coding: utf-8 -*-
# ==============================================================================
# Archivo: routes/faltas.py
# Proyecto: Sistema de Gestión Escolar - Colegio Dr. Antonio Vaca Díez
# Desarrollado por: Avrora Soft - Vibola LLC
# Descripción: Blueprint para gestión de Faltas y Licencias (SIN WhatsApp)
#              ⭐ FASE B: Sin N+1 (carga de nombres en 1 consulta) y con paginación
# ==============================================================================

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import db, Falta, Estudiante, Profesor, PersonalAdministrativo, Padre, Mensaje
from datetime import datetime
from werkzeug.utils import secure_filename

faltas_bp = Blueprint('faltas', __name__, template_folder='templates/faltas')

# =========================================================================
# LISTADO DE FALTAS (⭐ OPTIMIZADO + PAGINADO)
# =========================================================================
@faltas_bp.route('/')
def lista_faltas():
    """Muestra todas las faltas de estudiantes con filtros y paginación."""
    curso_filtro = request.args.get('curso', '')
    tipo_filtro = request.args.get('tipo', 'Todos')
    estado_filtro = request.args.get('estado', 'Todos')
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 25

    query = Falta.query.filter(Falta.tipo_sujeto == 'Estudiante')

    if curso_filtro:
        estudiante_ids = [e.id for e in Estudiante.query.filter_by(curso=curso_filtro, estado='Activo').all()]
        query = query.filter(Falta.sujeto_id.in_(estudiante_ids))

    if tipo_filtro != 'Todos':
        query = query.filter(Falta.tipo_falta == tipo_filtro)

    if estado_filtro != 'Todos':
        query = query.filter(Falta.estado == estado_filtro)

    # ⭐ PAGINACIÓN
    pagination = query.order_by(Falta.fecha.desc()).paginate(
        page=pagina, per_page=por_pagina, error_out=False
    )
    faltas = pagination.items

    # ⭐ SIN N+1: cargar todos los nombres en UNA sola consulta
    ids = {f.sujeto_id for f in faltas}
    mapa = {}
    if ids:
        estudiantes = Estudiante.query.filter(Estudiante.id.in_(ids)).all()
        mapa = {e.id: f"{e.apellidos}, {e.nombres}" for e in estudiantes}

    for falta in faltas:
        falta.nombre_estudiante = mapa.get(falta.sujeto_id, f"ID: {falta.sujeto_id}")

    cursos = db.session.query(Estudiante.curso).filter_by(estado='Activo').distinct().all()
    cursos = [c[0] for c in cursos]

    return render_template('faltas/lista.html', faltas=faltas, cursos=cursos,
                          curso_actual=curso_filtro, tipo_actual=tipo_filtro,
                          estado_actual=estado_filtro, pagination=pagination)

# =========================================================================
# REGISTRAR NUEVA FALTA / LICENCIA
# =========================================================================
@faltas_bp.route('/nuevo', methods=['GET', 'POST'])
def nueva_falta():
    if request.method == 'POST':
        try:
            estudiante_id = int(request.form['estudiante_id'])
            est = Estudiante.query.get_or_404(estudiante_id)

            fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            tipo_falta = request.form['tipo_falta']
            observaciones = request.form.get('observaciones', '')

            archivo_nombre = None
            if 'archivo' in request.files:
                archivo = request.files['archivo']
                if archivo and archivo.filename != '':
                    filename = secure_filename(f"falta_{estudiante_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{archivo.filename}")
                    upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'faltas')
                    os.makedirs(upload_folder, exist_ok=True)
                    archivo.save(os.path.join(upload_folder, filename))
                    archivo_nombre = filename

            nueva = Falta(
                tipo_sujeto='Estudiante',
                sujeto_id=estudiante_id,
                rude_estudiante=est.rude,
                fecha=fecha,
                tipo_falta=tipo_falta,
                observaciones=observaciones,
                estado='Pendiente',
                archivo_adjunto=archivo_nombre
            )
            db.session.add(nueva)
            db.session.commit()

            padre = Padre.query.filter_by(estudiante_id=estudiante_id).first()
            if padre:
                nombre_tutor = padre.nombres or "Padre de Familia"
                telefono = padre.telefono1 or padre.telefono2 or "Sin teléfono"
                nombre_estudiante = f"{est.nombres} {est.apellidos}"

                contenido = (
                    f"COMUNICADO DE FALTA - COLEGIO DR. ANTONIO VACA DÍEZ\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"Estimado/a Sr./Sra. {nombre_tutor}:\n\n"
                    f"Le informamos que {nombre_estudiante} registró una {tipo_falta} "
                    f"el día {fecha.strftime('%d/%m/%Y')}.\n\n"
                    f"Observaciones: {observaciones or 'Ninguna'}\n\n"
                    f"Atentamente,\nLA DIRECCIÓN DEL COLEGIO"
                )

                mensaje_interno = Mensaje(
                    destinatario=nombre_tutor,
                    estudiante_id=estudiante_id,
                    telefono=telefono,
                    tipo_mensaje=f'Falta {tipo_falta}',
                    contenido=contenido,
                    remitente='Colegio'
                )
                db.session.add(mensaje_interno)
                db.session.commit()

            flash('✅ Falta/Licencia registrada y comunicada internamente.', 'success')
            return redirect(url_for('faltas.lista_faltas'))

        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
            flash(f'❌ Error al registrar: {str(e)}', 'danger')

    curso_filtro = request.args.get('curso', '')
    estudiantes = []
    if curso_filtro:
        estudiantes = Estudiante.query.filter_by(curso=curso_filtro, estado='Activo').order_by(Estudiante.apellidos).all()

    cursos = db.session.query(Estudiante.curso).filter_by(estado='Activo').distinct().all()
    cursos = [c[0] for c in cursos]

    return render_template('faltas/form.html', estudiantes=estudiantes, cursos=cursos,
                          curso_actual=curso_filtro, today=datetime.now().strftime('%Y-%m-%d'))

# =========================================================================
# ACTUALIZAR ESTADO (JUSTIFICAR, APROBAR, RECHAZAR)
# =========================================================================
@faltas_bp.route('/actualizar_estado/<int:id>', methods=['POST'])
def actualizar_estado(id):
    falta = Falta.query.get_or_404(id)
    accion = request.form.get('accion', '')

    try:
        if accion == 'justificar':
            falta.estado = 'Justificada'
            falta.tipo_falta = 'Justificada'
            flash('✅ Falta justificada correctamente.', 'success')
        elif accion == 'aprobar':
            falta.estado = 'Aprobada'
            flash('✅ Falta aprobada correctamente.', 'success')
        elif accion == 'rechazar':
            falta.estado = 'Rechazada'
            flash('⚠️ Falta rechazada.', 'warning')
        elif accion == 'pendiente':
            falta.estado = 'Pendiente'
            flash('ℹ️ Falta marcada como pendiente.', 'info')

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error: {str(e)}', 'danger')

    return redirect(url_for('faltas.lista_faltas'))

# =========================================================================
# JUSTIFICAR CON OBSERVACIÓN
# =========================================================================
@faltas_bp.route('/justificar/<int:id>', methods=['POST'])
def justificar_falta(id):
    falta = Falta.query.get_or_404(id)
    observacion = request.form.get('observacion', '').strip()

    falta.estado = 'Justificada'
    falta.tipo_falta = 'Justificada'
    if observacion:
        falta.observaciones = observacion

    db.session.commit()
    flash('✅ Falta justificada correctamente.', 'success')
    return redirect(url_for('faltas.lista_faltas'))

# =========================================================================
# ELIMINAR FALTA
# =========================================================================
@faltas_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_falta(id):
    falta = Falta.query.get_or_404(id)

    try:
        db.session.delete(falta)
        db.session.commit()
        flash('✅ Falta eliminada permanentemente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error al eliminar: {str(e)}', 'danger')

    return redirect(url_for('faltas.lista_faltas'))

# =========================================================================
# REPORTE POR ESTUDIANTE
# =========================================================================
@faltas_bp.route('/reporte/<int:estudiante_id>')
def reporte_estudiante(estudiante_id):
    faltas = Falta.query.filter_by(sujeto_id=estudiante_id, tipo_sujeto='Estudiante').order_by(Falta.fecha.desc()).all()
    estudiante = Estudiante.query.get_or_404(estudiante_id)
    return render_template('faltas/reporte.html', faltas=faltas, estudiante=estudiante)

# =========================================================================
# REPORTE GENÉRICO POR SUJETO
# =========================================================================
@faltas_bp.route('/reporte_sujeto/<tipo_sujeto>/<int:sujeto_id>')
def reporte_sujeto(tipo_sujeto, sujeto_id):
    faltas = Falta.query.filter_by(tipo_sujeto=tipo_sujeto, sujeto_id=sujeto_id).order_by(Falta.fecha.desc()).all()

    sujeto_nombre = "Desconocido"
    if tipo_sujeto == 'Estudiante':
        sujeto = Estudiante.query.get(sujeto_id)
        if sujeto:
            sujeto_nombre = f"{sujeto.apellidos}, {sujeto.nombres}"
    elif tipo_sujeto == 'Profesor':
        sujeto = Profesor.query.get(sujeto_id)
        if sujeto:
            sujeto_nombre = f"{sujeto.apellidos}, {sujeto.nombres}"
    elif tipo_sujeto == 'Administrativo':
        sujeto = PersonalAdministrativo.query.get(sujeto_id)
        if sujeto:
            sujeto_nombre = f"{sujeto.apellidos}, {sujeto.nombres}"

    return render_template('faltas/reporte_sujeto.html',
                          faltas=faltas,
                          sujeto_nombre=sujeto_nombre,
                          tipo_sujeto=tipo_sujeto)