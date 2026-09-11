# -*- coding: utf-8 -*-
import os
import io
import tempfile
from datetime import datetime, timezone, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import qrcode
from utils_pdf import ruta_logo, nombre_institucion

BOLIVIA_TZ = timezone(timedelta(hours=-4))

def guardar_boletin_localmente(estudiante, pdf_bytes):
    try:
        anio_actual = datetime.now(BOLIVIA_TZ).year
        est_id = getattr(estudiante, 'id', '0')
        est_ci = getattr(estudiante, 'ci', 'S_CI')
        filename = f"boletin_{est_id}_{anio_actual}_{est_ci}.pdf"
        boletines_dir = os.path.join(os.getcwd(), 'static', 'boletines')
        os.makedirs(boletines_dir, exist_ok=True)
        filepath = os.path.join(boletines_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(pdf_bytes)
        return filename
    except Exception as e:
        print(f"Error al guardar boletin: {e}")
        return None

def generar_boletin_pdf(estudiante, calificaciones, materias, cloudinary_url=None):
    buffer = io.BytesIO()
    c_canvas = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)

    # Datos estudiante
    if isinstance(estudiante, dict):
        nombre_est = estudiante.get('nombre_completo') or f"{estudiante.get('nombres', '')} {estudiante.get('apellidos', '')}".strip() or "Estudiante"
        curso_est = estudiante.get('curso', 'Secundaria')
        rude_est = estudiante.get('rude', '-')
        turno_est = estudiante.get('turno', 'Regular')
        ci_est = estudiante.get('ci', '-')
    else:
        nombre_est = getattr(estudiante, 'nombre_completo', None) or f"{getattr(estudiante, 'nombres', '')} {getattr(estudiante, 'apellidos', '')}".strip() or "Estudiante"
        curso_est = getattr(estudiante, 'curso', getattr(estudiante, 'nivel', 'Secundaria'))
        rude_est = getattr(estudiante, 'rude', '-')
        turno_est = getattr(estudiante, 'turno', 'Regular')
        ci_est = getattr(estudiante, 'ci', '-')

    # Procesamiento cuantitativo estricto
    trimestres_activos = [1, 2, 3]
    materias_notas = {}

    # Filtrar y excluir cualquier materia o calificación residual de nidito/inicial/kinder
    materias_validas = [
        m for m in materias 
        if not any(term in (m.nombre or '').lower() for term in ['nidito', 'inicial', 'kinder'])
    ]

    for cal in calificaciones:
        mat = next((m for m in materias_validas if str(m.id) == str(cal.materia_id)), None)
        if not mat:
            continue
        mat_nom = mat.nombre.strip()
        if mat_nom not in materias_notas:
            materias_notas[mat_nom] = {1: [], 2: [], 3: []}

        raw_tri = getattr(cal, 'trimestre', None) or getattr(cal, 'periodo', None) or 1
        try:
            tri = int(raw_tri)
        except Exception:
            tri = 1
        if tri not in trimestres_activos:
            tri = 1

        if cal.nota is not None:
            try:
                materias_notas[mat_nom][tri].append(float(cal.nota))
            except (ValueError, TypeError):
                pass

    for m in materias_validas:
        mat_nom = m.nombre.strip()
        if mat_nom not in materias_notas:
            materias_notas[mat_nom] = {1: [], 2: [], 3: []}

    # Fondo blanco
    c_canvas.setFillColor(colors.white)
    c_canvas.rect(0, 0, width, height, fill=1, stroke=0)

    # Cabecera institucional
    logo_path = ruta_logo()
    if logo_path and os.path.exists(logo_path):
        try:
            c_canvas.drawImage(logo_path, 36, height - 76, width=62, height=62, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c_canvas.setFillColor(colors.HexColor('#0F2942'))
    c_canvas.setFont("Helvetica-Bold", 16)
    c_canvas.drawString(108, height - 36, nombre_institucion().upper())

    c_canvas.setFont("Helvetica", 9)
    c_canvas.setFillColor(colors.HexColor('#4A5568'))
    c_canvas.drawString(108, height - 50, "COLEGIO PARTICULAR - EXCELENCIA ACADÉMICA Y FORMACIÓN INTEGRAL")

    c_canvas.setFont("Helvetica-Bold", 13)
    c_canvas.setFillColor(colors.HexColor('#1E4E79'))
    c_canvas.drawRightString(width - 36, height - 36, "BOLETÍN OFICIAL DE CALIFICACIONES")

    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    ahora = datetime.now(BOLIVIA_TZ)
    fecha_txt = f"{ahora.day} de {meses[ahora.month - 1]} de {ahora.year}"
    c_canvas.setFont("Helvetica", 9)
    c_canvas.setFillColor(colors.HexColor('#718096'))
    c_canvas.drawRightString(width - 36, height - 50, f"Gestión {ahora.year} • Emisión: {fecha_txt}")

    # Cuadro de datos del estudiante
    c_canvas.setFillColor(colors.HexColor('#F8FAFC'))
    c_canvas.setStrokeColor(colors.HexColor('#CBD5E1'))
    c_canvas.roundRect(36, height - 118, width - 72, 36, 4, fill=1, stroke=1)

    c_canvas.setFont("Helvetica-Bold", 9)
    c_canvas.setFillColor(colors.HexColor('#1E293B'))
    c_canvas.drawString(48, height - 96, f"Estudiante: {nombre_est.upper()}")
    c_canvas.drawString(320, height - 96, f"Curso: {curso_est}")
    c_canvas.drawString(560, height - 96, f"C.I.: {ci_est}")

    c_canvas.setFont("Helvetica", 9)
    c_canvas.setFillColor(colors.HexColor('#475569'))
    c_canvas.drawString(48, height - 110, f"Código RUDE: {rude_est}")
    c_canvas.drawString(320, height - 110, f"Turno: {turno_est}")

    # Estilos de celda
    styles = getSampleStyleSheet()
    th_style = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.white, alignment=1)
    td_mat = ParagraphStyle('TDMat', fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=colors.HexColor('#0F172A'))
    td_val = ParagraphStyle('TDVal', fontName='Helvetica', fontSize=9, leading=12, alignment=1, textColor=colors.HexColor('#334155'))
    td_prom = ParagraphStyle('TDProm', fontName='Helvetica-Bold', fontSize=9, leading=12, alignment=1, textColor=colors.HexColor('#0F2942'))

    filas_tabla = [[
        Paragraph("ÁREA / MATERIA", th_style),
        Paragraph("1° TRIMESTRE", th_style),
        Paragraph("2° TRIMESTRE", th_style),
        Paragraph("3° TRIMESTRE", th_style),
        Paragraph("PROMEDIO FINAL", th_style)
    ]]

    suma_anuales = 0
    total_materias = 0

    for mat_nom in sorted(materias_notas.keys()):
        t_dict = materias_notas[mat_nom]
        fila = [Paragraph(mat_nom, td_mat)]
        proms_trimestres = []

        for tri in [1, 2, 3]:
            notas_tri = t_dict.get(tri, [])
            if notas_tri:
                prom_tri = sum(notas_tri) / len(notas_tri)
                fila.append(Paragraph(f"{prom_tri:.1f}", td_val))
                proms_trimestres.append(prom_tri)
            else:
                fila.append(Paragraph("-", td_val))

        if proms_trimestres:
            prom_anual = sum(proms_trimestres) / len(proms_trimestres)
            fila.append(Paragraph(f"<b>{prom_anual:.1f}</b>", td_prom))
            suma_anuales += prom_anual
            total_materias += 1
        else:
            fila.append(Paragraph("-", td_val))

        filas_tabla.append(fila)

    prom_inst = (suma_anuales / total_materias) if total_materias > 0 else 0
    c_canvas.setFont("Helvetica-Bold", 9)
    c_canvas.setFillColor(colors.HexColor('#0F2942'))
    c_canvas.drawString(560, height - 110, f"Prom. General: {prom_inst:.1f}")

    # Tabla: 5 columnas exactas distribuidas en 720 pt
    col_w = [300, 105, 105, 105, 105]

    t = Table(filas_tabla, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E4E79')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
    ]))

    w_tab, h_tab = t.wrap(width - 72, height)
    pos_y = max(68, height - 130 - h_tab)
    t.drawOn(c_canvas, 36, pos_y)

    # QR de verificación
    qr_text = cloudinary_url if cloudinary_url else f"COLEGIO VACA DIEZ | EST: {nombre_est} | RUDE: {rude_est} | CURSO: {curso_est}"
    qr = qrcode.QRCode(version=1, box_size=2, border=1)
    qr.add_data(qr_text)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_qr:
        img_qr.save(tmp_qr.name)
        tmp_qr_path = tmp_qr.name

    try:
        c_canvas.drawImage(tmp_qr_path, width - 86, 16, width=48, height=48)
    except Exception:
        pass
    finally:
        if os.path.exists(tmp_qr_path):
            os.unlink(tmp_qr_path)

    c_canvas.setFont("Helvetica", 7.5)
    c_canvas.setFillColor(colors.HexColor('#64748B'))
    c_canvas.drawString(36, 32, f"Documento oficial generado digitalmente por el Sistema Académico - {nombre_institucion()}")
    c_canvas.drawString(36, 22, "Válido institucionalmente con registro en base de datos. Verificación mediante código QR.")

    c_canvas.save()
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
