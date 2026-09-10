# -*- coding: utf-8 -*-
"""
==============================================================================
Archivo: routes/profesores_portal.py
Proyecto: Sistema de Gestión Escolar - Colegio Dr. Antonio Vaca Díez
Desarrollado por: Avrora Soft - Vibola LLC
Descripción: Portal docente con motor de precedencia de rúbricas:
             1. Precedencia Específica: Criterios propios de la materia.
             2. Precedencia General: Rúbrica general del nivel (Nidito, Primaria, Secundaria).
             Bloqueo estricto de edición estructural para docentes.
==============================================================================
"""

import json
from functools import wraps
from datetime import datetime

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, session, abort
)
from werkzeug.security import check_password_hash

from models import (
    db, Profesor, Materia, Estudiante, Calificacion,
    CriterioEvaluacion, nivel_de_curso
)

profesores_portal_bp = Blueprint(
    'profesores_portal',
    __name__,
    template_folder='templates/profesores_portal'
)


def login_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'profesor_id' not in session:
            flash('Debe iniciar sesión para acceder al portal.', 'danger')
            return redirect(url_for('profesores_portal.login'))
        return f(*args, **kwargs)
    return decorated_function


def obtener_criterios_materia(materia_id):
    """
    Motor de precedencia de evaluación institucional:
    - Nivel 1: Criterios específicos asignados directamente a la materia.
    - Nivel 2: Criterios generales configurados para el nivel (Nidito, Primaria, Secundaria).
    - Mapeo exacto: Nidito 1 y Nidito 2 heredan la rúbrica general de 'Nidito'.
    """
    materia = Materia.query.get(materia_id)
    if not materia:
        return [], 'general', False, 'Primaria'

    nivel = nivel_de_curso(materia.curso_id)
    if not nivel:
        c_low = (materia.curso_id or '').lower()
        if 'nidito' in c_low:
            nivel = 'Nidito'
        elif 'secundaria' in c_low:
            nivel = 'Secundaria'
        else:
            nivel = 'Primaria'

    # 1. Verificar si existen criterios específicos asignados por la administración
    criterios_especificos = CriterioEvaluacion.query.filter_by(
        materia_id=materia_id,
        activo=True
    ).order_by(CriterioEvaluacion.orden.asc()).all()

    if criterios_especificos:
        origen = 'especifico'
        criterios = criterios_especificos
    else:
        # 2. Precedencia general: Criterios globales del nivel
        origen = 'general'
        criterios = CriterioEvaluacion.query.filter_by(
            nivel=nivel,
            materia_id=None,
            activo=True
        ).order_by(CriterioEvaluacion.orden.asc()).all()

        # Respaldo de seguridad en caso de base de datos recién inicializada
        if not criterios:
            if nivel == 'Nidito':
                base = [
                    CriterioEvaluacion(nombre='Desarrollo Psicomotriz', nivel='Nidito', tipo_evaluacion='CUALITATIVA', opciones_cualitativas='Logrado,En Proceso,En Inicio', es_descriptivo=False, orden=1, activo=True),
                    CriterioEvaluacion(nombre='Lenguaje y Comunicación', nivel='Nidito', tipo_evaluacion='CUALITATIVA', opciones_cualitativas='Logrado,En Proceso,En Inicio', es_descriptivo=False, orden=2, activo=True),
                    CriterioEvaluacion(nombre='Autonomía y Convivencia', nivel='Nidito', tipo_evaluacion='CUALITATIVA', opciones_cualitativas='Logrado,En Proceso,En Inicio', es_descriptivo=False, orden=3, activo=True),
                    CriterioEvaluacion(nombre='Informe Pedagógico y Recomendaciones', nivel='Nidito', tipo_evaluacion='CUALITATIVA', opciones_cualitativas=None, es_descriptivo=True, orden=4, activo=True)
                ]
            else:
                base = [
                    CriterioEvaluacion(nombre='Asistencia', nivel=nivel, tipo_evaluacion='NUMERICA', puntaje_maximo=10, permite_decimales=False, paso_step=1.0, orden=1, activo=True),
                    CriterioEvaluacion(nombre='Participación / Exposición', nivel=nivel, tipo_evaluacion='NUMERICA', puntaje_maximo=20, permite_decimales=False, paso_step=1.0, orden=2, activo=True),
                    CriterioEvaluacion(nombre='Evaluaciones y Trabajos', nivel=nivel, tipo_evaluacion='NUMERICA', puntaje_maximo=70, permite_decimales=True, paso_step=0.5, orden=3, activo=True)
                ]
            db.session.add_all(base)
            db.session.commit()
            criterios = CriterioEvaluacion.query.filter_by(nivel=nivel, materia_id=None, activo=True).order_by(CriterioEvaluacion.orden.asc()).all()

    es_nidito = (nivel == 'Nidito') or all(c.tipo_evaluacion == 'CUALITATIVA' for c in criterios)
    return criterios, origen, es_nidito, nivel


def recalcular_nota_final(materia_id, periodo='1er Trimestre'):
    """
    Calcula la sumatoria sobre 100 puntos y genera el desglose JSON.
    Se omite en régimen cualitativo (Nidito).
    """
    criterios, origen, es_nidito, nivel = obtener_criterios_materia(materia_id)
    if es_nidito:
        return

    materia = Materia.query.get(materia_id)
    if not materia:
        return

    # Mapeo de alumnos según curso
    if materia.curso_id == 'Nidito':
        estudiantes = Estudiante.query.filter(
            Estudiante.curso.in_(['Nidito 1', 'Nidito 2']),
            Estudiante.estado == 'Activo'
        ).all()
    else:
        estudiantes = Estudiante.query.filter_by(curso=materia.curso_id, estado='Activo').all()

    nombres_criterios = [c.nombre for c in criterios if c.tipo_evaluacion == 'NUMERICA']

    for est in estudiantes:
        notas_criterios = Calificacion.query.filter(
            Calificacion.estudiante_id == est.id,
            Calificacion.materia_id == materia_id,
            Calificacion.periodo == periodo,
            Calificacion.tipo.in_(nombres_criterios)
        ).all()

        desglose = {}
        total = 0.0
        for cal in notas_criterios:
            val = float(cal.nota or 0.0)
            desglose[cal.tipo] = val
            total += val

        total = min(100.0, max(0.0, total))

        cal_final = Calificacion.query.filter_by(
            estudiante_id=est.id,
            materia_id=materia_id,
            periodo=periodo,
            tipo='Nota Final'
        ).first()

        if cal_final:
            cal_final.nota = round(total, 1)
            cal_final.desglose_json = json.dumps(desglose, ensure_ascii=False)
            cal_final.fecha = datetime.now().date()
        else:
            nueva_final = Calificacion(
                estudiante_id=est.id,
                ci_estudiante=est.ci,
                rude_estudiante=est.rude,
                materia_id=materia_id,
                periodo=periodo,
                tipo='Nota Final',
                nota=round(total, 1),
                desglose_json=json.dumps(desglose, ensure_ascii=False),
                fecha=datetime.now().date()
            )
            db.session.add(nueva_final)

    db.session.commit()


# =========================================================================
# RUTAS DEL PORTAL DOCENTE
# =========================================================================

@profesores_portal_bp.route('/')
@login_requerido
def index():
    profesor_id = int(session['profesor_id'])
    profesor = Profesor.query.get(profesor_id)
    mis_materias = Materia.query.filter_by(profesor_id=profesor_id).all()
    return render_template('profesores_portal/index.html', profesor=profesor, materias=mis_materias)


@profesores_portal_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        contrasena = request.form.get('contrasena', '').strip()
        profesor = Profesor.query.filter_by(usuario=usuario, estado='Activo').first()

        if profesor and check_password_hash(profesor.contrasena_hash, contrasena):
            session['profesor_id'] = profesor.id
            session['profesor_nombre'] = f"{profesor.apellidos}, {profesor.nombres}"
            flash(f"Bienvenido/a Prof. {profesor.nombres}", 'success')
            return redirect(url_for('profesores_portal.index'))
        flash('Credenciales incorrectas.', 'danger')
    return render_template('profesores_portal/login.html')


@profesores_portal_bp.route('/logout')
def logout():
    session.pop('profesor_id', None)
    session.pop('profesor_nombre', None)
    return redirect(url_for('profesores_portal.login'))


@profesores_portal_bp.route('/materia/<int:materia_id>')
@login_requerido
def ver_materia(materia_id):
    profesor_id = int(session['profesor_id'])
    materia = Materia.query.get_or_404(materia_id)

    if materia.profesor_id != profesor_id:
        abort(403)

    periodo_sel = request.args.get('periodo', '1er Trimestre').strip()
    criterios, origen_rubrica, es_nidito, nivel = obtener_criterios_materia(materia_id)

    if not es_nidito:
        recalcular_nota_final(materia_id, periodo_sel)

    # Identificación de estudiantes respetando Nidito 1 y Nidito 2
    if materia.curso_id == 'Nidito':
        estudiantes = Estudiante.query.filter(
            Estudiante.curso.in_(['Nidito 1', 'Nidito 2']),
            Estudiante.estado == 'Activo'
        ).order_by(Estudiante.curso.asc(), Estudiante.apellidos.asc()).all()
    else:
        estudiantes = Estudiante.query.filter_by(
            curso=materia.curso_id,
            estado='Activo'
        ).order_by(Estudiante.apellidos.asc(), Estudiante.nombres.asc()).all()

    calificaciones_periodo = Calificacion.query.filter_by(
        materia_id=materia_id,
        periodo=periodo_sel
    ).all()

    cal_matrix = {}
    notas_finales = {}
    for c in calificaciones_periodo:
        tipo_limpio = c.tipo.strip() if c.tipo else ''
        if tipo_limpio == 'Nota Final':
            notas_finales[c.estudiante_id] = c.nota
        else:
            cal_matrix[(c.estudiante_id, tipo_limpio)] = c

    return render_template(
        'profesores_portal/materia.html',
        materia=materia,
        estudiantes=estudiantes,
        nivel=nivel,
        es_nidito=es_nidito,
        criterios=criterios,
        origen_rubrica=origen_rubrica,
        periodo_sel=periodo_sel,
        cal_matrix=cal_matrix,
        notas_finales=notas_finales,
        periodos=['1er Trimestre', '2do Trimestre', '3er Trimestre']
    )


@profesores_portal_bp.route('/guardar_notas_matriz/<int:materia_id>', methods=['POST'])
@login_requerido
def guardar_notas_matriz(materia_id):
    profesor_id = int(session['profesor_id'])
    materia = Materia.query.get_or_404(materia_id)

    if materia.profesor_id != profesor_id:
        abort(403)

    periodo = request.form.get('periodo', '1er Trimestre').strip()
    criterios, origen_rubrica, es_nidito, nivel = obtener_criterios_materia(materia_id)

    if materia.curso_id == 'Nidito':
        estudiantes = Estudiante.query.filter(
            Estudiante.curso.in_(['Nidito 1', 'Nidito 2']),
            Estudiante.estado == 'Activo'
        ).all()
    else:
        estudiantes = Estudiante.query.filter_by(curso=materia.curso_id, estado='Activo').all()

    contador = 0

    for est in estudiantes:
        desglose_est = {}
        total_est = 0.0

        for crit in criterios:
            campo_nombre = f"criterio_{est.id}_{crit.id}"

            if es_nidito:
                cal = Calificacion.query.filter_by(
                    estudiante_id=est.id,
                    materia_id=materia_id,
                    periodo=periodo,
                    tipo=crit.nombre
                ).first()

                if not cal:
                    cal = Calificacion(
                        estudiante_id=est.id,
                        ci_estudiante=est.ci,
                        rude_estudiante=est.rude,
                        materia_id=materia_id,
                        periodo=periodo,
                        tipo=crit.nombre,
                        nota=0.0,
                        fecha=datetime.now().date()
                    )
                    db.session.add(cal)
                elif cal.nota is None:
                    cal.nota = 0.0

                if crit.es_descriptivo:
                    cal.informe_descriptivo = request.form.get(campo_nombre, '').strip()
                else:
                    cal.valoracion_cualitativa = request.form.get(campo_nombre, '').strip()

                cal.fecha = datetime.now().date()

            else:
                # Régimen Numérico: Asistencia (0-10 int), Participación (1-20 int), Evaluaciones (0-70 float)
                val_str = request.form.get(campo_nombre, '').strip()
                try:
                    if not crit.permite_decimales:
                        val_num = int(round(float(val_str))) if val_str else 0
                    else:
                        val_num = float(val_str) if val_str else 0.0
                except (ValueError, TypeError):
                    val_num = 0 if not crit.permite_decimales else 0.0

                max_p = float(crit.puntaje_maximo or 100.0)
                val_num = max(0, min(int(max_p), int(val_num))) if not crit.permite_decimales else max(0.0, min(max_p, float(val_num)))

                desglose_est[crit.nombre] = val_num
                total_est += float(val_num)

                cal = Calificacion.query.filter_by(
                    estudiante_id=est.id,
                    materia_id=materia_id,
                    periodo=periodo,
                    tipo=crit.nombre
                ).first()

                if not cal:
                    cal = Calificacion(
                        estudiante_id=est.id,
                        ci_estudiante=est.ci,
                        rude_estudiante=est.rude,
                        materia_id=materia_id,
                        periodo=periodo,
                        tipo=crit.nombre,
                        nota=0.0,
                        fecha=datetime.now().date()
                    )
                    db.session.add(cal)
                elif cal.nota is None:
                    cal.nota = 0.0

                cal.nota = float(val_num)
                cal.fecha = datetime.now().date()

        if not es_nidito:
            total_est = min(100.0, max(0.0, total_est))
            cal_final = Calificacion.query.filter_by(
                estudiante_id=est.id,
                materia_id=materia_id,
                periodo=periodo,
                tipo='Nota Final'
            ).first()

            if not cal_final:
                cal_final = Calificacion(
                    estudiante_id=est.id,
                    ci_estudiante=est.ci,
                    rude_estudiante=est.rude,
                    materia_id=materia_id,
                    periodo=periodo,
                    tipo='Nota Final',
                    fecha=datetime.now().date()
                )
                db.session.add(cal_final)

            cal_final.nota = round(total_est, 1)
            cal_final.desglose_json = json.dumps(desglose_est, ensure_ascii=False)
            cal_final.fecha = datetime.now().date()

        contador += 1

    db.session.commit()
    flash(f'✅ Calificaciones guardadas correctamente ({contador} estudiantes) para el {periodo}.', 'success')
    return redirect(url_for('profesores_portal.ver_materia', materia_id=materia_id, periodo=periodo))


# Bloqueo de mutación de rúbricas desde el portal docente
@profesores_portal_bp.route('/nueva_evaluacion/<int:materia_id>', methods=['POST'])
@login_requerido
def nueva_evaluacion(materia_id):
    flash('❌ Acción restringida: La definición de rúbricas es de competencia exclusiva de la Administración.', 'warning')
    return redirect(url_for('profesores_portal.ver_materia', materia_id=materia_id))


@profesores_portal_bp.route('/eliminar_evaluacion/<int:materia_id>', methods=['POST'])
@login_requerido
def eliminar_evaluacion(materia_id):
    flash('❌ Acción restringida: La eliminación de parámetros evaluativos solo puede ser autorizada por Dirección.', 'warning')
    return redirect(url_for('profesores_portal.ver_materia', materia_id=materia_id))