# -*- coding: utf-8 -*-
# ==============================================================================
# Archivo: routes/faltas.py
# Proyecto: Sistema de Gestión Escolar
# Desarrollado por: Avrora Soft - Vibola LLC
# Descripción: Blueprint para gestión de Faltas y Licencias
#             ⭐ FASE B: Sin N+1 (carga de nombres en 1 consulta) y con paginación
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
# REGISTRAR NUEVA FALTA / LICENCIA + NOTIFICACIÓN AUTOMÁTICA
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
                estado=tipo_falta,
                archivo_adjunto=archivo_nombre
            )
            db.session.add(nueva)
            db.session.commit()

            # ⭐ ENVÍO AUTOMÁTICO AL CHAT DEL PADRE DE FAMILIA
            try:
                padre = Padre.query.filter_by(estudiante_id=estudiante_id).first()
                
                # Asignar valores por defecto si el estudiante aún no tiene padre registrado
                nombre_tutor = padre.nombres if padre and padre.nombres else "Padre/Tutor"
                telefono = (padre.telefono1 or padre.telefono2) if padre else "Sin teléfono"
                nombre_estudiante = f"{est.nombres} {est.apellidos}"

                # Adaptar la redacción según el tipo de falta para que suene natural
                fecha_formato = fecha.strftime('%d/%m/%Y')
                if tipo_falta == 'Injustificada':
                    accion_texto = f"faltó hoy al colegio {fecha_formato} sin ninguna justificación."
                elif tipo_falta == 'Justificada':
                    accion_texto = f"faltó hoy al colegio {fecha_formato} con falta justificada."
                elif tipo_falta == 'Licencia':
                    accion_texto = f"tiene licencia aprobada para el día {fecha_formato}."
                elif tipo_falta == 'Atraso':
                    accion_texto = f"llegó atrasado al colegio el día {fecha_formato}."
                else:
                    accion_texto = f"registró una {tipo_falta} el día {fecha_formato}."

                contenido = (
                    f"COMUNICADO DE ASISTENCIA - INSTITUCIÓN EDUCATIVA\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"Estimado/a Sr./Sra. {nombre_tutor}:\n\n"
                    f"Le informamos que {nombre_estudiante}, {accion_texto}\n\n"
                    f"Observaciones: {observaciones or 'Ninguna'}\n\n"
                    f"Atentamente,\nLA DIRECCIÓN"
                )

                mensaje_interno = Mensaje(
                    destinatario=nombre_tutor,
                    estudiante_id=estudiante_id,
                    telefono=telefono,
                    tipo_mensaje=f'Falta {tipo_falta}',
                    contenido=contenido,
                    remitente='Institución'
                )
                db.session.add(mensaje_interno)
                db.session.commit()
                
                print(f"✅ Mensaje de falta guardado en BD para: {nombre_estudiante}")
                
            except Exception as msg_err:
                print(f"⚠️ Aviso: No se pudo generar el mensaje interno para el padre: {msg_err}")

            flash('✅ Falta registrada y comunicada automáticamente al chat de los padres.', 'success')
            return redirect(url_for('faltas.lista_faltas'))

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error crítico al registrar falta: {e}")
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
# EDITAR / JUSTIFICAR FALTA + ESTADO "JUSTIFICADA" + NOTIFICACIÓN AUTOMÁTICA
# =========================================================================
@faltas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_falta(id):
    falta = Falta.query.get_or_404(id)
    estudiante_actual = Estudiante.query.get(falta.sujeto_id)

    if request.method == 'POST':
        try:
            falta.fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            falta.tipo_falta = request.form['tipo_falta']
            
            # ⭐ REGLA: Al justificar y guardar, el estado se fija obligatoriamente como "Justificada"
            falta.estado = 'Justificada'  
            falta.observaciones = request.form.get('observaciones', '')

            # Procesar nuevo archivo si se adjuntó
            if 'archivo' in request.files:
                archivo = request.files['archivo']
                if archivo and archivo.filename != '':
                    filename = secure_filename(f"falta_{falta.sujeto_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{archivo.filename}")
                    upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'faltas')
                    os.makedirs(upload_folder, exist_ok=True)
                    archivo.save(os.path.join(upload_folder, filename))
                    falta.archivo_adjunto = filename

            db.session.commit()

            # ⭐ ENVÍO AUTOMÁTICO DE JUSTIFICACIÓN AL CHAT DE LOS PADRES
            try:
                if estudiante_actual:
                    padre = Padre.query.filter_by(estudiante_id=estudiante_actual.id).first()
                    if padre:
                        nombre_tutor = padre.nombres or "Padre de Familia"
                        telefono = padre.telefono1 or padre.telefono2 or "Sin teléfono"
                        nombre_estudiante = f"{estudiante_actual.nombres} {estudiante_actual.apellidos}"

                        contenido = (
                            f"ACTUALIZACIÓN DE JUSTIFICACIÓN - INSTITUCIÓN EDUCATIVA\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"Estimado/a Sr./Sra. {nombre_tutor}:\n\n"
                            f"Le informamos que la falta de {nombre_estudiante} "
                            f"del día {falta.fecha.strftime('%d/%m/%Y')} ha sido formalmente *JUSTIFICADA*.\n\n"
                            f"Detalle / Observaciones: {falta.observaciones or 'Ninguna'}\n\n"
                            f"Atentamente,\nLA DIRECCIÓN"
                        )

                        mensaje_interno = Mensaje(
                            destinatario=nombre_tutor,
                            estudiante_id=estudiante_actual.id,
                            telefono=telefono,
                            tipo_mensaje='Falta Justificada',
                            contenido=contenido,
                            remitente='Institución'
                        )
                        db.session.add(mensaje_interno)
                        db.session.commit()
            except Exception as msg_err:
                print(f"⚠️ Aviso: No se pudo generar el mensaje interno de justificación: {msg_err}")

            flash('✅ Falta justificada correctamente y comunicada al chat de los padres.', 'success')
            return redirect(url_for('faltas.lista_faltas'))

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error crítico al actualizar falta: {e}")
            flash(f'❌ Error al actualizar: {str(e)}', 'danger')

    cursos = db.session.query(Estudiante.curso).filter_by(estado='Activo').distinct().all()
    cursos = [c[0] for c in cursos]
    
    estudiantes = []
    if estudiante_actual and estudiante_actual.curso:
        estudiantes = Estudiante.query.filter_by(curso=estudiante_actual.curso, estado='Activo').order_by(Estudiante.apellidos).all()

    return render_template('faltas/form.html', falta=falta, estudiante_actual=estudiante_actual,
                         estudiantes=estudiantes, cursos=cursos, 
                         curso_actual=estudiante_actual.curso if estudiante_actual else '',
                         today=datetime.now().strftime('%Y-%m-%d'))

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