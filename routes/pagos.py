# -*- coding: utf-8 -*-
# ==============================================================================
# Archivo: routes/pagos.py
# Proyecto: Sistema de Gestión Escolar - Colegio Dr. Antonio Vaca Díez
# Desarrollado por: Avrora Soft - Vibola LLC
# Descripción: Blueprint para gestión de Pagos, Caja y Recibos con validación
#              estricta de turno activo (Cero asignaciones automáticas).
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
# REGISTRAR PAGO
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
            estudiante_id = request.form['estudiante_id']
            mes = request.form['mes']
            anio = int(request.form['anio'])
            monto_total = float(request.form['monto_total'])
            descuento = float(request.form.get('descuento', 0))
            monto_pagado = float(request.form['monto_pagado'])
            
            estudiante_obj = Estudiante.query.get(estudiante_id)
            
            if not estudiante_obj:
                flash('⚠️ El estudiante seleccionado no existe en la base de datos.', 'danger')
                return redirect(url_for('pagos.registrar'))

            ci_est = estudiante_obj.ci if hasattr(estudiante_obj, 'ci') and estudiante_obj.ci else 'S/N'
            rude_est = estudiante_obj.rude if hasattr(estudiante_obj, 'rude') and estudiante_obj.rude else 'S/N'

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
    gestion = request.args.get('gestion', datetime.now(BOLIVIA_TZ).year, type=int)

    # Obtener lista única de cursos activos para el selector
    cursos = db.session.query(Estudiante.curso).filter_by(estado='Activo').distinct().order_by(Estudiante.curso).all()
    cursos = [c[0] for c in cursos]

    deudores = []

    if curso_seleccionado:
        # Meses escolares fijos esperados en la gestión (puedes ajustar según tu calendario)
        meses_esperados = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        
        # Supongamos una mensualidad fija por defecto (puedes adaptarla si el modelo tiene un costo asignado)
        costo_mensual = 350.0  # Cambia esto al monto fijo real de la pensión mensual en Bolivianos
        total_esperado_anual = len(meses_esperados) * costo_mensual

        estudiantes = Estudiante.query.filter_by(curso=curso_seleccionado, estado='Activo').order_by(Estudiante.apellidos).all()
        
        for est in estudiantes:
            pagos_estudiante = Pago.query.filter_by(estudiante_id=est.id, gestion=gestion).all()
            
            # Obtener los meses que ya han sido pagados y registrados
            meses_pagados = [p.mes for p in pagos_estudiante if getattr(p, 'estado', 'Pagado') == 'Pagado']
            total_pagado = sum([p.monto for p in pagos_estudiante if getattr(p, 'estado', 'Pagado') == 'Pagado'])
            
            # Si el total pagado es menor al esperado anual, se calcula el saldo
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
# GENERAR RECIBO PDF SIMPLE (Función auxiliar)
# =========================================================================
def generar_recibo_pago_pdf_simple(pago, estudiante, padre):
    """Genera un recibo simple de pago en PDF."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    except ImportError:
        raise Exception("ReportLab no está instalado. Ejecute: pip install reportlab")
    
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
    
    # Encabezado
    elements.append(Paragraph("COLEGIO DR. ANTONIO VACA DÍEZ", title_style))
    elements.append(Paragraph("Dirección Administrativa y Académica", header_style))
    elements.append(Paragraph("Riberalta, Beni, Bolivia", header_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("RECIBO DE PAGO", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Número de recibo y fecha
    numero_recibo = f"REC-{pago.anio}-{pago.id:04d}"
    fecha_str = pago.fecha_pago.strftime('%d/%m/%Y %H:%M') if pago.fecha_pago else datetime.now().strftime('%d/%m/%Y %H:%M')
    
    info_data = [
        [Paragraph(f"<b>N° de Recibo:</b> {numero_recibo}", normal_style), 
         Paragraph(f"<b>Fecha:</b> {fecha_str}", normal_style)],
    ]
    info_table = Table(info_data, colWidths=[3.5*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f0f0')),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Datos del estudiante
    elements.append(Paragraph("<b>DATOS DEL ESTUDIANTE</b>", normal_style))
    elements.append(Spacer(1, 0.1*inch))
    
    estudiante_data = [
        [Paragraph(f"<b>Nombre:</b> {estudiante.apellidos}, {estudiante.nombres}", normal_style),
         Paragraph(f"<b>RUDE:</b> {estudiante.rude if estudiante.rude else 'S/N'}", normal_style)],
        [Paragraph(f"<b>Curso:</b> {estudiante.curso if hasattr(estudiante, 'curso') else 'No asignado'}", normal_style),
         Paragraph(f"<b>Gestión:</b> {pago.anio}", normal_style)],
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
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(estudiante_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Detalle del pago
    elements.append(Paragraph("<b>DETALLE DEL PAGO</b>", normal_style))
    elements.append(Spacer(1, 0.1*inch))
    
    pago_data = [
        [Paragraph("<b>Concepto</b>", normal_style), Paragraph("<b>Valor</b>", normal_style)],
        [Paragraph(f"Mes: {pago.mes}", normal_style), Paragraph(f"Bs. {pago.monto_total:.2f}", normal_style)],
        [Paragraph("Descuento", normal_style), Paragraph(f"- Bs. {(pago.descuento or 0):.2f}", normal_style)],
        [Paragraph("<b>Monto Pagado</b>", normal_style), Paragraph(f"<b>Bs. {pago.monto_pagado:.2f}</b>", normal_style)],
        [Paragraph("Estado", normal_style), Paragraph(pago.estado, normal_style)],
    ]
    
    pago_table = Table(pago_data, colWidths=[4*inch, 3*inch])
    pago_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a4a4a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(pago_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Firma
    elements.append(Paragraph("_" * 50, normal_style))
    elements.append(Paragraph("Firma del Administrador", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Pie de página
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                  textColor=colors.grey, alignment=TA_CENTER)
    elements.append(Spacer(1, 0.2*inch))
    footer_text = Paragraph(
        f"<i>Este recibo es un comprobante oficial de pago. Conserve este documento para sus registros. "
        f"Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} por el Sistema de Gestión Escolar - Colegio Dr. Antonio Vaca Díez.</i>",
        footer_style
    )
    elements.append(footer_text)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()