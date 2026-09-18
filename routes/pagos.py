# -*- coding: utf-8 -*-
# ==============================================================================
# Archivo: routes/pagos.py
# Proyecto: Sistema de Gestión Escolar - Colegio Dr. Antonio Vaca Díez
# Desarrollado por: Avrora Soft - Vibola LLC
# Descripción: Blueprint para gestión de Pagos, Caja y Recibos con validación
#             estricta de turno activo (Cero asignaciones automáticas).
# ==============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, session
from models import db, Pago, Estudiante, Padre
from datetime import datetime
import io
import os
from sqlalchemy import func, or_, and_
pagos_bp = Blueprint('pagos', __name__, template_folder='templates/pagos')


def asegurar_turno_activo():
    """Valida estrictamente que exista un turno activo en sesión . 
    Cero asignaciones automáticas de turno bajo ninguna circunstancia."""
    turno = session.get('turno_activo')
    rol = session.get('rol')
    
    if not turno:
        return False
    return True


# =========================================================================
# VISTA PRINCIPAL DE CAJA
# =========================================================================
@pagos_bp.route('/')
def index():
    """Vista principal de caja con resumen."""
    turno_actual = session.get('turno_activo', 'No asignado')
    
    total_recaudado = db.session.query(db.func.sum(Pago.monto_pagado)).filter_by(estado='Pagado').scalar() or 0
    pagos_recientes = Pago.query.order_by(Pago.fecha_pago.desc()).limit(10).all()
    
    return render_template('pagos/index.html', 
                           total=total_recaudado, 
                           recientes=pagos_recientes,
                           turno_actual=turno_actual)


# =========================================================================
# REGISTRAR PAGO (SOPORTA PAGO INDIVIDUAL Y MÚLTIPLE POR CHECKBOXES)
# =========================================================================
@pagos_bp.route('/registrar', methods=['GET', 'POST'])
def registrar():
    # ⭐ Validación estricta: Bloquea inmediatamente si no hay turno activo 
    if not asegurar_turno_activo():
        flash('❌ Transacción bloqueada: El sistema no cuenta con un turno activo. Debe iniciar sesión manualmente en un turno para registrar pagos en caja.', 'danger')
        return redirect(url_for('pagos.index'))

    turno_actual = session.get('turno_activo')
    responsable_turno = turno_actual if turno_actual else None

    if request.method == 'POST':
        try:
            accion_cobro = request.form.get('accion_cobro', 'pension')
            estudiante_id = request.form['estudiante_id']
            anio = int(request.form['anio'])
            metodo_pago = request.form.get('metodo_pago', 'Efectivo')
            descuento = float(request.form.get('descuento', 0))
            monto_abonado = float(request.form.get('monto_abono', 0))

            estudiante_obj = Estudiante.query.get(estudiante_id)
            if not estudiante_obj:
                flash('⚠️ El estudiante seleccionado no existe en la base de datos.', 'danger')
                return redirect(url_for('pagos.registrar'))

            ci_est = estudiante_obj.ci if hasattr(estudiante_obj, 'ci') and estudiante_obj.ci else 'S/N'
            rude_est = estudiante_obj.rude if hasattr(estudiante_obj, 'rude') and estudiante_obj.rude else 'S/N'

            # CASO 1: PAGO MÚLTIPLE POR CASILLAS DE VERIFICACIÓN (CHECKBOXES)
            if accion_cobro == 'pension_multiple':
                meses_seleccionados = request.form.getlist('meses_seleccionados')
                if not meses_seleccionados:
                    flash('❌ No seleccionó ningún mes de pensión.', 'danger')
                    return redirect(request.referrer or url_for('pagos.registrar'))

                pension_base_est = float(estudiante_obj.pension or 0.0)
                
                for mes_nombre in meses_seleccionados:
                    pago_existente = Pago.query.filter_by(
                        estudiante_id=estudiante_id, mes=mes_nombre, anio=anio
                    ).first()

                    monto_mes = pension_base_est
                    desc_mes = descuento / len(meses_seleccionados) if descuento > 0 else 0.0
                    pagado_mes = min(monto_abonado, monto_mes - desc_mes)
                    monto_abonado -= pagado_mes # Descontar del abono global ingresado

                    if pago_existente:
                        # Si ya existía, actualizar o sumar
                        pago_existente.monto_pagado = float(pago_existente.monto_pagado or 0) + pagado_mes
                        pago_existente.descuento = float(pago_existente.descuento or 0) + desc_mes
                        if pago_existente.monto_pagado >= (pago_existente.monto_total - pago_existente.descuento):
                            pago_existente.estado = 'Pagado'
                        else:
                            pago_existente.estado = 'Parcial'
                    else:
                        nuevo_pago = Pago(
                            estudiante_id=estudiante_id,
                            ci_estudiante=ci_est,
                            rude_estudiante=rude_est,
                            mes=mes_nombre,
                            anio=anio,
                            monto_total=monto_mes,
                            descuento=desc_mes,
                            monto_pagado=pagado_mes,
                            fecha_pago=datetime.now(),
                            estado='Pagado' if pagado_mes >= (monto_mes - desc_mes) else 'Parcial',
                            turno_responsable=responsable_turno
                        )
                        db.session.add(nuevo_pago)

                db.session.commit()
                flash(f'✅ ¡PAGO MÚLTIPLE EXITOSO! Se procesaron {len(meses_seleccionados)} mes(es) en caja (Turno: {responsable_turno}).', 'success')
                return redirect(url_for('pagos.index'))

            # CASO 2: PAGO INDIVIDUAL TRADICIONAL
            else:
                mes = request.form['mes']
                monto_total = float(request.form['monto_total'])
                monto_pagado = float(request.form['monto_pagado'])

                pago_existente = Pago.query.filter_by(
                    estudiante_id=estudiante_id, mes=mes, anio=anio
                ).first()
                
                if pago_existente:
                    flash('⚠️ Ya existe un registro para este mes y año.', 'warning')
                    return redirect(url_for('pagos.registrar'))
                
                nuevo_pago = Pago(
                    estudiante_id=estudiante_id,
                    ci_estudiante=ci_est,
                    rude_estudiante=rude_est,
                    mes=mes,
                    anio=anio,
                    monto_total=monto_total,
                    descuento=descuento,
                    monto_pagado=monto_pagado,
                    fecha_pago=datetime.now(),
                    estado='Pagado' if monto_pagado >= (monto_total - descuento) else 'Parcial',
                    turno_responsable=responsable_turno
                )
                db.session.add(nuevo_pago)
                db.session.commit()
                
                flash(f'✅ Pago registrado exitosamente (Turno: {responsable_turno}).', 'success')
                return redirect(url_for('pagos.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al registrar: {str(e)}', 'danger')
    
    estudiantes = Estudiante.query.filter_by(estado='Activo').order_by(Estudiante.apellidos).all()
    return render_template('pagos/registrar.html', estudiantes=estudiantes, turno_actual=turno_actual)

# =========================================================================
# GENERAR RECIBO (Vista para imprimir)
# =========================================================================
@pagos_bp.route('/recibo/<int:id>')
def generar_recibo(id):
    """Genera una vista simple para imprimir el recibo."""
    pago = Pago.query.get_or_404(id)
    estudiante = Estudiante.query.get(pago.estudiante_id)
    padre = Padre.query.filter_by(estudiante_id=pago.estudiante_id).first()
    return render_template('pagos/recibo.html', pago=pago, estudiante=estudiante, padre=padre)

# =========================================================================
# DESCARGAR RECIBO PDF
# =========================================================================
@pagos_bp.route('/descargar_recibo/<int:id>')
def descargar_recibo_pdf(id):
    """Genera y descarga el recibo en formato PDF."""
    try:
        pago = Pago.query.get_or_404(id)
        estudiante = Estudiante.query.get_or_404(pago.estudiante_id)
        padre = Padre.query.filter_by(estudiante_id=pago.estudiante_id).first()
        
        # Generar PDF
        bytes_pdf = generar_recibo_pago_pdf_simple(pago, estudiante, padre)
        
        # Guardar localmente usando current_app para evitar fallos de rutas relativas
        recibos_dir = os.path.join(current_app.static_folder, 'recibos')
        os.makedirs(recibos_dir, exist_ok=True)
        
        filename = f"recibo_pago_{pago.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = os.path.join(recibos_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(bytes_pdf)
        
        return send_file(filepath, as_attachment=True, download_name=f"Recibo_Pago_{estudiante.apellidos}_{pago.mes}_{pago.anio}.pdf")
        
    except Exception as e:
        flash(f'❌ Error al generar el recibo: {str(e)}', 'danger')
        return redirect(url_for('pagos.generar_recibo', id=id))

# =========================================================================
# HISTORIAL DE PAGOS
# =========================================================================
@pagos_bp.route('/historial')
def historial():
    search = request.args.get('search', '', type=str)
    query = Pago.query.join(Estudiante)
    
    if search:
        query = query.filter(
            db.or_(
                Estudiante.apellidos.ilike(f'%{search}%'),
                Estudiante.nombres.ilike(f'%{search}%'),
                Pago.mes.ilike(f'%{search}%')
            )
        )
    
    pagos = query.order_by(Pago.fecha_pago.desc()).all()
    return render_template('pagos/historial.html', pagos=pagos, search=search)
    
@pagos_bp.route('/deudores/curso', methods=['GET'])
def deudores_por_curso():
    """Muestra la lista de estudiantes deudores filtrados por curso."""
    curso_seleccionado = request.args.get('curso', '')
    gestion = request.args.get('gestion', datetime.now().year, type=int)

    # Obtener lista única de cursos activos para el selector
    cursos = db.session.query(Estudiante.curso).filter_by(estado='Activo').distinct().order_by(Estudiante.curso).all()
    cursos = [c[0] for c in cursos]

    deudores = []

    if curso_seleccionado:
        meses_esperados = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        costo_mensual = 350.0 
        total_esperado_anual = len(meses_esperados) * costo_mensual

        estudiantes = Estudiante.query.filter_by(curso=curso_seleccionado, estado='Activo').order_by(Estudiante.apellidos).all()
        
        for est in estudiantes:
            pagos_estudiante = Pago.query.filter_by(estudiante_id=est.id, anio=gestion).all()
            
            meses_pagados = [p.mes for p in pagos_estudiante if getattr(p, 'estado', 'Pagado') == 'Pagado']
            total_pagado = sum([p.monto_pagado for p in pagos_estudiante if getattr(p, 'estado', 'Pagado') == 'Pagado'])
            
            if total_pagado < total_esperado_anual:
                saldo_pendiente = total_esperado_anual - total_pagado
                deudores.append({
                    'estudiante': est,
                    'meses_pagados': len(meses_pagados),
                    'total_pagado': total_pagado,
                    'saldo_pendiente': saldo_pendiente
                })

    return render_template('pagos/deudores_curso.html',
                           cursos=cursos,
                           curso_seleccionado=curso_seleccionado,
                           gestion=gestion,
                           deudores=deudores)

# =========================================================================
# GENERAR RECIBO PDF SIMPLE (SOPORTA PAGOS MÚLTIPLES Y TURNO)
# =========================================================================
def generar_recibo_pago_pdf_simple(pagos_o_pago, estudiante, padre):
    """Genera un recibo en PDF soportando tanto pagos únicos como múltiples y turno."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    except ImportError:
        raise Exception("ReportLab no está instalado. Ejecute: pip install reportlab")
    
    # Asegurar que 'pagos' sea siempre una lista iterable
    if isinstance(pagos_o_pago, list):
        pagos = pagos_o_pago
    else:
        pagos = [pagos_o_pago]

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                            rightMargin=1*inch, leftMargin=1*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                 fontSize=18, textColor=colors.HexColor('#1a1a1a'),
                                 spaceAfter=12, alignment=TA_CENTER, fontName='Helvetica-Bold')
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'],
                                  fontSize=10, textColor=colors.HexColor('#333333'), alignment=TA_CENTER)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'],
                                  fontSize=10, textColor=colors.HexColor('#333333'))
    
    elements = []
    
    # Encabezado institucional
    elements.append(Paragraph("COLEGIO DR. ANTONIO VACA DÍEZ", title_style))
    elements.append(Paragraph("Dirección Administrativa y Académica", header_style))
    elements.append(Paragraph("Riberalta, Beni, Bolivia", header_style))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("RECIBO OFICIAL DE PAGO", title_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # Datos de referencia (N° de Recibo, Fecha y Turno)
    primer_pago = pagos[0] if pagos else None
    recibo_id = primer_pago.id if primer_pago else 1000
    anio_ref = primer_pago.anio if primer_pago else datetime.now().year
    numero_recibo = f"REC-{anio_ref}-{recibo_id:04d}"
    
    fecha_pago_val = getattr(primer_pago, 'fecha_pago', None) if primer_pago else None
    fecha_str = fecha_pago_val.strftime('%d/%m/%Y %H:%M') if fecha_pago_val else datetime.now().strftime('%d/%m/%Y %H:%M')
    
    turno_cobro = getattr(primer_pago, 'turno_responsable', None) if primer_pago else 'Caja Central'
    if not turno_cobro:
        turno_cobro = 'Caja Central'

    info_data = [
        [Paragraph(f"<b>N° de Recibo:</b> {numero_recibo}", normal_style), 
         Paragraph(f"<b>Fecha:</b> {fecha_str}", normal_style)],
        [Paragraph(f"<b>Caja / Turno:</b> {turno_cobro}", normal_style),
         Paragraph("", normal_style)]
    ]
    info_table = Table(info_data, colWidths=[3.5*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f0f0')),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Datos del estudiante
    elements.append(Paragraph("<b>DATOS DEL ESTUDIANTE</b>", normal_style))
    elements.append(Spacer(1, 0.05*inch))
    
    estudiante_data = [
        [Paragraph(f"<b>Nombre:</b> {estudiante.apellidos}, {estudiante.nombres}", normal_style),
         Paragraph(f"<b>C.I.:</b> {estudiante.ci if hasattr(estudiante, 'ci') and estudiante.ci else 'S/N'}", normal_style)],
        [Paragraph(f"<b>Curso:</b> {estudiante.curso if hasattr(estudiante, 'curso') else 'No asignado'}", normal_style),
         Paragraph(f"<b>Gestión:</b> {anio_ref}", normal_style)],
    ]
    
    if padre:
        estudiante_data.append([
            Paragraph(f"<b>Tutor:</b> {padre.nombres or 'No registrado'}", normal_style),
            Paragraph(f"<b>Parentesco:</b> {padre.parentesco or 'No especificado'}", normal_style)
        ])
    
    estudiante_table = Table(estudiante_data, colWidths=[3.5*inch, 3.5*inch])
    estudiante_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(estudiante_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Detalle de la tabla de pagos (Soporta múltiples meses)
    elements.append(Paragraph("<b>DETALLE DE CONCEPTOS CANCELADOS</b>", normal_style))
    elements.append(Spacer(1, 0.05*inch))
    
    pago_data = [
        [Paragraph("<b>Concepto / Mes</b>", normal_style), 
         Paragraph("<b>Monto Base</b>", normal_style), 
         Paragraph("<b>Descuento</b>", normal_style), 
         Paragraph("<b>Pagado</b>", normal_style)]
    ]
    
    total_general_pagado = 0.0

    for p in pagos:
        concepto = f"Pensión - {p.mes}" if getattr(p, 'tipo_concepto', 'Pensión') == 'Pensión' else f"{p.tipo_concepto}: {p.detalle_concepto}"
        monto_t = float(p.monto_total or 0.0)
        desc_t = float(p.descuento or 0.0)
        pagado_t = float(p.monto_pagado or 0.0)
        total_general_pagado += pagado_t

        pago_data.append([
            Paragraph(concepto, normal_style),
            Paragraph(f"Bs. {monto_t:.2f}", normal_style),
            Paragraph(f"Bs. {desc_t:.2f}", normal_style),
            Paragraph(f"<b>Bs. {pagado_t:.2f}</b>", normal_style)
        ])
    
    pago_table = Table(pago_data, colWidths=[2.8*inch, 1.4*inch, 1.4*inch, 1.4*inch])
    pago_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a4a4a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(pago_table)
    elements.append(Spacer(1, 0.15*inch))

    # Total General
    totales_data = [
        [Paragraph("<b>TOTAL GENERAL CANCELADO:</b>", normal_style),
         Paragraph(f"<b>Bs. {total_general_pagado:.2f}</b>", normal_style)]
    ]
    totales_table = Table(totales_data, colWidths=[4.2*inch, 2.8*inch])
    totales_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#d4edda')),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(totales_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Firma y pie de página
    elements.append(Paragraph("_" * 40, normal_style))
    elements.append(Paragraph("Firma y Sello de Administración / Caja", normal_style))
    elements.append(Spacer(1, 0.15*inch))
    
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                  textColor=colors.grey, alignment=TA_CENTER)
    footer_text = Paragraph(
        f"<i>Este recibo es un comprobante oficial de pago consolidado. "
        f"Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} por el Sistema de Gestión Escolar - Colegio Dr. Antonio Vaca Díez.</i>",
        footer_style
    )
    elements.append(footer_text)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

@pagos_bp.route('/reporte-deudores', methods=['GET'])
def reporte_deudores():
    from collections import defaultdict
    meses_escolares = ["Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre"]
    anio_actual = 2026

    estudiantes = Estudiante.query.filter(
        Estudiante.estado.in_(["Activo", "Inscrito"]) | Estudiante.estado.is_(None)
    ).order_by(Estudiante.curso, Estudiante.apellidos, Estudiante.nombres).all()

    deudores_por_curso = defaultdict(lambda: {"subtotal": 0.0, "alumnos": []})
    gran_total = 0.0
    total_deudores_conteo = 0

    for est in estudiantes:
        pension_base = float(est.pension or 0.0)
        if pension_base <= 0:
            continue

        pagos_est = Pago.query.filter_by(estudiante_id=est.id, anio=anio_actual).all()
        pagos_map = {p.mes.strip().capitalize(): p for p in pagos_est if p.mes}

        meses_adeudados = []
        deuda_estudiante = 0.0

        for mes in meses_escolares:
            if mes in pagos_map:
                p = pagos_map[mes]
                saldo_mes = float(p.monto_total or pension_base) - float(p.monto_pagado or 0.0)
                if saldo_mes > 0:
                    deuda_estudiante += saldo_mes
                    meses_adeudados.append(f"{mes[:3]} (Bs.{saldo_mes:,.0f})")
            else:
                deuda_estudiante += pension_base
                meses_adeudados.append(mes[:3])

        if deuda_estudiante > 0:
            curso_nom = est.curso or "Sin Curso Asignado"
            deudores_por_curso[curso_nom]["subtotal"] += deuda_estudiante
            deudores_por_curso[curso_nom]["alumnos"].append({
                "estudiante": f"{est.apellidos}, {est.nombres}",
                "ci": est.ci or "S/N",
                "pension": pension_base,
                "deuda": deuda_estudiante,
                "cant_meses": len(meses_adeudados),
                "detalle_meses": ", ".join(meses_adeudados)
            })
            gran_total += deuda_estudiante
            total_deudores_conteo += 1

    return render_template(
        'pagos/reporte_deudores.html',
        deudores_por_curso=dict(deudores_por_curso),
        gran_total=gran_total,
        total_alumnos_deudores=total_deudores_conteo,
        anio_actual=anio_actual
    )