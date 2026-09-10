# -*- coding: utf-8 -*-
"""
Generador de Boletines en PDF con diseño escalonado por trimestre
SOPORTE COMPLETO: Nidito (Cualitativo) y Primaria/Secundaria (Cuantitativo)
"""
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

def _estampar_marca_agua_estudiante(c_canvas, estudiante, width, height):
    """Estampa la marca de agua de seguridad institucional con opacidad exacta del 15%."""
    try:
        c_canvas.saveState()
        c_canvas.setFillColor(colors.Color(0.2, 0.2, 0.2, alpha=0.15))
        c_canvas.setFont("Helvetica-Bold", 36)
        c_canvas.translate(width / 2.0, height / 2.0)
        c_canvas.rotate(32)

        apellidos = getattr(estudiante, 'apellidos', '') or ''
        nombres = getattr(estudiante, 'nombres', '') or ''
        ci = getattr(estudiante, 'ci', '') or ''
        exp = getattr(estudiante, 'expedido', '') or 'BN'
        rude = getattr(estudiante, 'rude', '') or '-'

        nombre_est = f"{apellidos} {nombres}".strip().upper()
        if nombre_est:
            c_canvas.drawCentredString(0, 25, nombre_est)
            c_canvas.setFont("Helvetica-Bold", 14)
            c_canvas.drawCentredString(0, -12, f"C.I. {ci} {exp}  •  RUDE: {rude}  •  COL. DR. ANTONIO VACA DÍEZ")
        c_canvas.restoreState()
    except Exception:
        pass

def guardar_boletin_localmente(estudiante, pdf_bytes):
    """Función auxiliar de compatibilidad."""
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
        print(f"Error al guardar boletín localmente: {e}")
        return None

def generar_boletin_pdf(estudiante, calificaciones, materias, cloudinary_url=None):
    """Genera un Boletín de Calificaciones en orientación horizontal (landscape),
    adaptado estrictamente según el nivel (Nidito vs Primaria/Secundaria)."""

    buffer = io.BytesIO()
    c_canvas = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)

    # Detección estricta y exclusiva para Nidito
    es_nidito = False
    curso_str = ""
    if estudiante:
        if isinstance(estudiante, dict):
            curso_str = str(estudiante.get('curso', '') or estudiante.get('nivel', '')).lower().strip()
        else:
            curso_str = str(getattr(estudiante, 'curso', '') or getattr(estudiante, 'nivel', '')).lower().strip()
    
    if curso_str.startswith('nidito') or curso_str.startswith('inicial') or curso_str.startswith('kinder'):
        es_nidito = True

    # Datos del estudiante
    nombre_est = "Estudiante"
    if estudiante:
        if isinstance(estudiante, dict):
            nombre_est = (
                estudiante.get('nombre_completo') or
                estudiante.get('nombre') or
                f"{estudiante.get('nombres', '')} {estudiante.get('apellidos', '')}".strip() or
                "Estudiante"
            )
        else:
            nombre_est = (
                getattr(estudiante, 'nombre_completo', None) or
                getattr(estudiante, 'nombre', None) or
                (f"{getattr(estudiante, 'nombres', '')} {getattr(estudiante, 'apellidos', '')}".strip() if hasattr(estudiante, 'nombres') or hasattr(estudiante, 'apellidos') else None) or
                "Estudiante"
            )

    curso_est = getattr(estudiante, 'curso', getattr(estudiante, 'nivel', '6to. de Secundaria')) if not isinstance(estudiante, dict) else estudiante.get('curso', '6to. de Secundaria')
    rude_est = getattr(estudiante, 'rude', getattr(estudiante, 'codigo', 'S/N')) if not isinstance(estudiante, dict) else estudiante.get('rude', 'S/N')
    turno_est = getattr(estudiante, 'turno', 'Regular') if not isinstance(estudiante, dict) else estudiante.get('turno', 'Regular')

    materias_notas = {}
    parciales_keys = ['P1', 'P2', 'P3', 'P4']
    trimestres_activos = [1, 2, 3]

    for cal in calificaciones:
        mat = next((m for m in materias if str(m.id) == str(cal.materia_id)), None)
        if mat is None:
            continue

        mat_nombre = mat.nombre
        if mat_nombre not in materias_notas:
            if es_nidito:
                materias_notas[mat_nombre] = []
            else:
                materias_notas[mat_nombre] = {
                    1: {k: None for k in parciales_keys},
                    2: {k: None for k in parciales_keys},
                    3: {k: None for k in parciales_keys}
                }

        raw_tri = getattr(cal, 'trimestre', None) or getattr(cal, 'periodo', None) or 1
        try:
            tri = int(raw_tri)
        except (ValueError, TypeError):
            tri = 1

        if tri not in trimestres_activos:
            tri = 1

        tipo_texto = (cal.tipo or '').upper().strip()

        if es_nidito:
            if not isinstance(materias_notas[mat_nombre], list):
                materias_notas[mat_nombre] = []
            materias_notas[mat_nombre].append({
                'tipo': cal.tipo,
                'valoracion': getattr(cal, 'valoracion_cualitativa', '') or '',
                'informe': getattr(cal, 'informe_descriptivo', '') or '',
                'periodo': getattr(cal, 'periodo', '1er Trimestre')
            })
            continue

        eval_key = 'P1'
        if '4' in tipo_texto or 'CUARTO' in tipo_texto:
            eval_key = 'P4'
        elif '3' in tipo_texto or 'TERCER' in tipo_texto:
            eval_key = 'P3'
        elif '2' in tipo_texto or 'SEGUNDO' in tipo_texto:
            eval_key = 'P2'
        elif tipo_texto in parciales_keys:
            eval_key = tipo_texto

        if isinstance(materias_notas[mat_nombre], dict):
            materias_notas[mat_nombre][tri][eval_key] = cal.nota

    for m in materias:
        if m.nombre not in materias_notas:
            if es_nidito:
                materias_notas[m.nombre] = []
            else:
                materias_notas[m.nombre] = {
                    1: {k: None for k in parciales_keys},
                    2: {k: None for k in parciales_keys},
                    3: {k: None for k in parciales_keys}
                }

    lista_tabla_data = []
    suma_promedios_generales = 0
    total_materias_evaluadas = 0

    if not es_nidito:
        for mat_nombre, trim_data in materias_notas.items():
            fila_item = {'nombre': mat_nombre, 'trimestres': {}, 'promedio_anual': '-'}
            notas_todas_materia = []

            for tri in trimestres_activos:
                p_dict = trim_data.get(tri, {k: None for k in parciales_keys})
                lista_p_tri = [p_dict[k] for k in parciales_keys if p_dict[k] is not None]

                if lista_p_tri:
                    prom_tri = sum(lista_p_tri) / len(lista_p_tri)
                    fila_item['trimestres'][tri] = {
                        'notas': [f"{p_dict[k]:.0f}" if p_dict[k] is not None else "-" for k in parciales_keys],
                        'prom': f"{prom_tri:.1f}"
                    }
                    notas_todas_materia.extend(lista_p_tri)
                else:
                    fila_item['trimestres'][tri] = {
                        'notas': ["-", "-", "-", "-"],
                        'prom': "-"
                    }

            if notas_todas_materia:
                prom_anual_mat = sum(notas_todas_materia) / len(notas_todas_materia)
                fila_item['promedio_anual'] = f"{prom_anual_mat:.1f}"
                suma_promedios_generales += prom_anual_mat
                total_materias_evaluadas += 1

            lista_tabla_data.append(fila_item)

    promedio_general_institucional = (suma_promedios_generales / total_materias_evaluadas) if total_materias_evaluadas > 0 else 0

    c_canvas.setFillColor(colors.white)
    c_canvas.rect(0, 0, width, height, fill=1, stroke=0)

    _estampar_marca_agua_estudiante(c_canvas, estudiante, width, height)

    logo_path = ruta_logo()
    if logo_path and os.path.exists(logo_path):
        try:
            c_canvas.drawImage(logo_path, 40, height - 90, width=75, height=75, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c_canvas.setFillColor(colors.HexColor('#1A365D'))
    c_canvas.setFont("Helvetica-Bold", 18)
    c_canvas.drawString(130, height - 42, nombre_institucion().upper())

    c_canvas.setFont("Helvetica", 11)
    c_canvas.setFillColor(colors.HexColor('#4A5568'))
    c_canvas.drawString(130, height - 60, "COLEGIO PARTICULAR - EXCELENCIA ACADÉMICA Y EDUCATIVA")

    c_canvas.setFont("Helvetica-Bold", 14)
    c_canvas.setFillColor(colors.HexColor('#2B6CB0'))
    c_canvas.drawRightString(width - 40, height - 42, "BOLETÍN OFICIAL DE CALIFICACIONES")

    fecha_emision = datetime.now(BOLIVIA_TZ).strftime('%d de %B de %Y')
    c_canvas.setFont("Helvetica", 10)
    c_canvas.setFillColor(colors.HexColor('#718096'))
    c_canvas.drawRightString(width - 40, height - 60, f"Fecha de Emisión: {fecha_emision}")

    c_canvas.setFillColor(colors.HexColor('#F7FAFC'))
    c_canvas.setStrokeColor(colors.HexColor('#CBD5E0'))
    c_canvas.roundRect(40, height - 135, width - 80, 42, 6, fill=1, stroke=1)

    c_canvas.setFont("Helvetica-Bold", 10)
    c_canvas.setFillColor(colors.HexColor('#2D3748'))
    c_canvas.drawString(55, height - 105, f"Estudiante: {nombre_est}")
    c_canvas.drawString(380, height - 105, f"Curso / Nivel: {curso_est}")
    c_canvas.drawString(55, height - 122, f"Código RUDE: {rude_est}")
    c_canvas.drawString(380, height - 122, f"Turno: {turno_est}")

    if not es_nidito:
        c_canvas.setFont("Helvetica-Bold", 10)
        c_canvas.setFillColor(colors.HexColor('#1A365D'))
        c_canvas.drawRightString(width - 55, height - 138, f"Promedio General Anual: {promedio_general_institucional:.1f}")

    styles = getSampleStyleSheet()
    est_th_main = ParagraphStyle('THMain', fontName='Helvetica-Bold', fontSize=10, leading=12, textColor=colors.white, alignment=1)
    est_th_sub = ParagraphStyle('THSub', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.white, alignment=1)
    est_td_mat = ParagraphStyle('TDMat', fontName='Helvetica-Bold', fontSize=10, leading=13, alignment=0, textColor=colors.HexColor('#1A365D'))
    est_td_val = ParagraphStyle('TDVal', fontName='Helvetica', fontSize=10, leading=13, alignment=1, textColor=colors.HexColor('#2D3748'))
    est_td_prom = ParagraphStyle('TDProm', fontName='Helvetica-Bold', fontSize=11, leading=14, alignment=1, textColor=colors.HexColor('#2B6CB0'))

    header_row_1 = [
        Paragraph("<b>MATERIAS</b>", est_th_main),
        Paragraph("<b>PRIMER TRIMESTRE</b>", est_th_main), "", "", "", "",
        Paragraph("<b>SEGUNDO TRIMESTRE</b>", est_th_main), "", "", "", "",
        Paragraph("<b>TERCER TRIMESTRE</b>", est_th_main), "", "", "", "",
        Paragraph("<b>PROM. ANUAL</b>", est_th_main)
    ]

    header_row_2 = [
        "",
        Paragraph("P1", est_th_sub), Paragraph("P2", est_th_sub), Paragraph("P3", est_th_sub), Paragraph("P4", est_th_sub), Paragraph("PROM", est_th_sub),
        Paragraph("P1", est_th_sub), Paragraph("P2", est_th_sub), Paragraph("P3", est_th_sub), Paragraph("P4", est_th_sub), Paragraph("PROM", est_th_sub),
        Paragraph("P1", est_th_sub), Paragraph("P2", est_th_sub), Paragraph("P3", est_th_sub), Paragraph("P4", est_th_sub), Paragraph("PROM", est_th_sub),
        ""
    ]

    tabla_data = [header_row_1, header_row_2]

    for item in lista_tabla_data:
        fila = [Paragraph(item['nombre'], est_td_mat)]
        for tri in [1, 2, 3]:
            t_info = item['trimestres'].get(tri, {'notas': ["-", "-", "-", "-"], 'prom': "-"})
            for nota_val in t_info['notas']:
                fila.append(Paragraph(nota_val, est_td_val))
            fila.append(Paragraph(f"<b>{t_info['prom']}</b>", est_td_val))
        fila.append(Paragraph(item['promedio_anual'], est_td_prom))
        tabla_data.append(fila)

    col_widths = [152] + [32, 32, 32, 32, 36] + [32, 32, 32, 32, 36] + [32, 32, 32, 32, 36] + [80]

    if es_nidito:
        est_th_nidito = ParagraphStyle('THNidito', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.white, alignment=1)
        est_td_left = ParagraphStyle('TDLeft', fontName='Helvetica', fontSize=9, leading=12, alignment=0, textColor=colors.HexColor('#2D3748'))
        est_td_center = ParagraphStyle('TDCenter', fontName='Helvetica', fontSize=9, leading=12, alignment=1, textColor=colors.HexColor('#2D3748'))

        tabla_rows = [
            [
                Paragraph("<b>ÁREA / DIMENSIÓN DE DESARROLLO</b>", est_th_nidito), 
                Paragraph("<b>PERIODO</b>", est_th_nidito), 
                Paragraph("<b>VALORACIÓN / LOGRO CUALITATIVO</b>", est_th_nidito), 
                Paragraph("<b>INFORME DESCRIPTIVO / RECOMENDACIONES</b>", est_th_nidito)
            ]
        ]
        for mat_nombre, registros in materias_notas.items():
            if isinstance(registros, list) and registros:
                for r in registros:
                    tabla_rows.append([
                        Paragraph(f"<b>{mat_nombre}</b><br/><font color='#666666'>{r.get('tipo', '')}</font>", est_td_left),
                        Paragraph(r.get('periodo', '1er Trimestre'), est_td_center),
                        Paragraph(f"<b><font color='#2b6cb0'>{r.get('valoracion', '-')}</font></b>", est_td_center),
                        Paragraph(r.get('informe', '-'), est_td_left)
                    ])
            else:
                tabla_rows.append([
                    Paragraph(f"<b>{mat_nombre}</b>", est_td_left),
                    Paragraph("1er Trimestre", est_td_center),
                    Paragraph("-", est_td_center),
                    Paragraph("-", est_td_left)
                ])
        t = Table(tabla_rows, colWidths=[180, 90, 140, 302], repeatRows=1)
    else:
        t = Table(tabla_data, colWidths=col_widths, repeatRows=2)

    if es_nidito:
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
    else:
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor('#1A365D')),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (1, 0), (5, 0)),
            ('SPAN', (6, 0), (10, 0)),
            ('SPAN', (11, 0), (15, 0)),
            ('SPAN', (16, 0), (16, 1)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ]))

    t.wrapOn(c_canvas, width, height)
    t.drawOn(c_canvas, 40, height - 380)

    qr_text = cloudinary_url if cloudinary_url else f"ESTUDIANTE: {nombre_est} | CURSO: {curso_est} | RUDE: {rude_est}"
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(qr_text)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_qr:
        img_qr.save(tmp_qr.name)
        tmp_qr_path = tmp_qr.name

    try:
        c_canvas.drawImage(tmp_qr_path, width - 100, 40, width=60, height=60)
    except Exception:
        pass
    finally:
        if os.path.exists(tmp_qr_path):
            os.unlink(tmp_qr_path)

    c_canvas.setFont("Helvetica", 8)
    c_canvas.setFillColor(colors.HexColor('#718096'))
    c_canvas.drawString(40, 50, f"Generado digitalmente por Sistema de Gestión Educativa - {nombre_institucion()}")
    c_canvas.drawString(40, 38, "Este documento posee validez institucional bajo registro en base de datos.")

    c_canvas.save()
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
