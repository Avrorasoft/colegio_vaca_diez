# -*- coding: utf-8 -*-
"""
==============================================================================
Archivo: routes/reportes.py
Proyecto: Sistema de Gestión Escolar
Desarrollado por: Avrora Soft - Vibola LLC
Descripción: Módulo de reportes económicos por turno (Mañana/Tarde) y 
consolidado general para caja única. Incluye Panel de Control y Monitor Mural.
==============================================================================
"""

import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from werkzeug.utils import secure_filename
from models import db, Pago, Gasto, PagoPersonal, Falta, Estudiante
from sqlalchemy import func, or_, and_

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes', template_folder='templates/reportes')

# =========================================================================
# CONFIGURACIÓN DEL MONITOR MURAL (JSON Básico)
# =========================================================================
CONFIG_FILE = 'monitor_config.json'

def cargar_configuracion_monitor():
    default_config = {
        'velocidad_ticker': 150,        
        'velocidad_aeropuerto': 40,     
        'intervalo_carrusel': 4000,     
        'texto_ticker': '🔴 AVISO: Inscripciones abiertas para las Olimpiadas. 🟢 DEPORTES: Final de Futsal el sábado a las 10:00 AM.',
        'agenda_1': 'Viernes Cívico: Acto a las 08:00 AM.',
        'agenda_2': 'Reunión Padres: Secundaria, martes 19:00 hrs.',
        'album_titulo': 'Galería Institucional',
        'album_subtitulo': 'Momentos destacados de nuestra comunidad educativa'
    }
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for k, v in default_config.items():
                    if k not in config:
                        config[k] = v
                return config
    except Exception:
        pass
    return default_config

def guardar_configuracion_monitor(config_data):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Error guardando config del monitor: {e}")
        return False

# =========================================================================
# REPORTES ECONÓMICOS
# =========================================================================
@reportes_bp.route('/economico/manana')
def economico_manana():
    try:
        pagos = [p for p in Pago.query.filter(Pago.turno_responsable == 'Mañana', Pago.monto_pagado > 0).order_by(Pago.fecha_pago.desc()).all() if getattr(p, 'estado', 'Pagado') != 'Anulado']
    except Exception:
        pagos = [p for p in Pago.query.filter(Pago.turno_responsable == 'Mañana', Pago.monto_pagado > 0).all()]
    
    total = sum(p.monto_pagado for p in pagos)

    try:
        todos_gastos = Gasto.query.all()
    except Exception:
        todos_gastos = []
    
    gastos = [g for g in todos_gastos if getattr(g, 'estado', 'Activo') != 'Anulado']
    total_gastos = sum(g.monto for g in gastos)

    try:
        todos_personal = PagoPersonal.query.all()
    except Exception:
        todos_personal = []

    pagos_personal = [p for p in todos_personal if getattr(p, 'estado', 'Pagado') != 'Anulado']
    total_personal = sum(p.monto_neto_pagado for p in pagos_personal)

    total_egresos = total_gastos + total_personal
    balance_neto = total - total_egresos

    return render_template('reportes/economico.html', 
                           pagos=pagos,
                           gastos=gastos,
                           pagos_personal=pagos_personal,
                           total=total,
                           total_gastos=total_gastos,
                           total_personal=total_personal,
                           total_egresos=total_egresos,
                           balance_neto=balance_neto,
                           titulo='Reporte Económico - Turno Mañana',
                           turno='Mañana')

@reportes_bp.route('/economico/tarde')
def economico_tarde():
    try:
        pagos = [p for p in Pago.query.filter(Pago.turno_responsable == 'Tarde', Pago.monto_pagado > 0).order_by(Pago.fecha_pago.desc()).all() if getattr(p, 'estado', 'Pagado') != 'Anulado']
    except Exception:
        pagos = [p for p in Pago.query.filter(Pago.turno_responsable == 'Tarde', Pago.monto_pagado > 0).all()]
    
    total = sum(p.monto_pagado for p in pagos)

    try:
        todos_gastos = Gasto.query.all()
    except Exception:
        todos_gastos = []

    gastos = [g for g in todos_gastos if getattr(g, 'estado', 'Activo') != 'Anulado']
    total_gastos = sum(g.monto for g in gastos)

    try:
        todos_personal = PagoPersonal.query.all()
    except Exception:
        todos_personal = []

    pagos_personal = [p for p in todos_personal if getattr(p, 'estado', 'Pagado') != 'Anulado']
    total_personal = sum(p.monto_neto_pagado for p in pagos_personal)

    total_egresos = total_gastos + total_personal
    balance_neto = total - total_egresos

    return render_template('reportes/economico.html', 
                           pagos=pagos,
                           gastos=gastos,
                           pagos_personal=pagos_personal,
                           total=total,
                           total_gastos=total_gastos,
                           total_personal=total_personal,
                           total_egresos=total_egresos,
                           balance_neto=balance_neto,
                           titulo='Reporte Económico - Turno Tarde',
                           turno='Tarde')

@reportes_bp.route('/economico/general')
def economico_general():
    try:
        pagos = [p for p in Pago.query.filter(Pago.monto_pagado > 0).order_by(Pago.fecha_pago.desc()).all() if getattr(p, 'estado', 'Pagado') != 'Anulado']
    except Exception:
        pagos = [p for p in Pago.query.filter(Pago.monto_pagado > 0).all()]

    total_general = sum(p.monto_pagado for p in pagos)
    
    total_manana = sum(p.monto_pagado for p in pagos if p.turno_responsable == 'Mañana')
    total_tarde = sum(p.monto_pagado for p in pagos if p.turno_responsable == 'Tarde')

    try:
        todos_gastos = Gasto.query.all()
    except Exception:
        todos_gastos = []

    gastos = [g for g in todos_gastos if getattr(g, 'estado', 'Activo') != 'Anulado']
    total_gastos = sum(g.monto for g in gastos)

    try:
        todos_personal = PagoPersonal.query.all()
    except Exception:
        todos_personal = []

    pagos_personal = [p for p in todos_personal if getattr(p, 'estado', 'Pagado') != 'Anulado']
    total_personal = sum(p.monto_neto_pagado for p in pagos_personal)

    total_egresos = total_gastos + total_personal
    balance_general_neto = total_general - total_egresos
    
    return render_template('reportes/economico_general.html', 
                           pagos=pagos,
                           gastos=gastos,
                           pagos_personal=pagos_personal,
                           total_general=total_general,
                           total_manana=total_manana,
                           total_tarde=total_tarde,
                           total_gastos=total_gastos,
                           total_personal=total_personal,
                           total_egresos=total_egresos,
                           balance_general_neto=balance_general_neto,
                           titulo='Reporte Económico General')


# =========================================================================
# PANEL DE CONTROL DEL MONITOR MURAL (Soporte Masivo de Fotos)
# =========================================================================
@reportes_bp.route('/monitor-config', methods=['GET', 'POST'])
def monitor_config():
    """Formulario para ajustar velocidades, textos y subida MASIVA de fotos."""
    config_actual = cargar_configuracion_monitor()
    
    # Directorio seguro para el álbum ilimitado
    upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'monitor_album')
    os.makedirs(upload_folder, exist_ok=True)

    if request.method == 'POST':
        try:
            # 1. Guardar Configuración de Textos y Velocidades
            nueva_config = {
                'velocidad_ticker': int(request.form.get('velocidad_ticker', 150)),
                'velocidad_aeropuerto': int(request.form.get('velocidad_aeropuerto', 40)),
                'intervalo_carrusel': int(request.form.get('intervalo_carrusel', 4000)),
                'texto_ticker': request.form.get('texto_ticker', ''),
                'agenda_1': request.form.get('agenda_1', ''),
                'agenda_2': request.form.get('agenda_2', ''),
                'album_titulo': request.form.get('album_titulo', 'Galería Institucional'),
                'album_subtitulo': request.form.get('album_subtitulo', 'Momentos destacados')
            }
            guardar_configuracion_monitor(nueva_config)

            # 2. Eliminar fotos seleccionadas
            fotos_a_eliminar = request.form.getlist('eliminar_fotos')
            for foto in fotos_a_eliminar:
                try:
                    os.remove(os.path.join(upload_folder, foto))
                except Exception as e:
                    print(f"Error eliminando foto {foto}: {e}")

            # 3. Procesar subida masiva de imágenes (Nuevas fotos)
            if 'fotos_album' in request.files:
                for file in request.files.getlist('fotos_album'):
                    if file and file.filename != '':
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(upload_folder, filename))

            flash('✅ Configuración y álbum actualizados con éxito. El monitor reflejará los cambios.', 'success')
            return redirect(url_for('reportes.monitor_config'))
            
        except ValueError:
            flash('❌ Error: Asegúrese de ingresar números válidos para las velocidades.', 'danger')

    # Leer todas las fotos actuales para mostrarlas en el panel
    fotos_actuales = [f for f in os.listdir(upload_folder) if os.path.isfile(os.path.join(upload_folder, f))]
    
    return render_template('reportes/monitor_config.html', configuracion=config_actual, fotos_actuales=fotos_actuales)


# =========================================================================
# RUTAS DE SERVICIO PARA ARCHIVOS DEL MONITOR
# =========================================================================
@reportes_bp.route('/album/<path:filename>')
def imagen_album(filename):
    """Fuerza la entrega de la imagen evitando fallos de configuración de static_folder."""
    upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'monitor_album')
    return send_from_directory(upload_folder, filename)


# =========================================================================
# PANTALLA PÚBLICA: MONITOR EXTERNO DE DIRECCIÓN
# =========================================================================
@reportes_bp.route('/monitor-direccion')
def monitor_direccion():
    """Pantalla pública en tiempo real."""
    from datetime import date
    hoy = date.today()
    configuracion = cargar_configuracion_monitor()
    
    # 1. Leer todas las fotos del directorio de forma dinámica
    upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'monitor_album')
    os.makedirs(upload_folder, exist_ok=True)
    fotos_album = [f for f in os.listdir(upload_folder) if os.path.isfile(os.path.join(upload_folder, f))]
    
    # 2. Consultar ausencias
    ausencias_hoy = Falta.query.filter(
        Falta.tipo_sujeto == 'Estudiante',
        Falta.fecha == hoy,
        Falta.tipo_falta.in_(['Falta Injustificada', 'Ausente', 'Falta'])
    ).all()
    
    est_ids = [a.sujeto_id for a in ausencias_hoy]
    estudiantes_ausentes = Estudiante.query.filter(Estudiante.id.in_(est_ids)).all() if est_ids else []
    mapa_est = {e.id: e for e in estudiantes_ausentes}
    
    lista_ausentes = []
    for aus in ausencias_hoy:
        est = mapa_est.get(aus.sujeto_id)
        if est:
            lista_ausentes.append({
                'apellidos': est.apellidos,
                'nombres': est.nombres,
                'curso': est.curso
            })

    lista_ausentes = sorted(lista_ausentes, key=lambda x: (x['curso'], x['apellidos']))

    return render_template(
        'reportes/monitor.html',
        ausentes=lista_ausentes,
        fecha_hoy=hoy.strftime('%d/%m/%Y'),
        configuracion=configuracion,
        fotos_album=fotos_album
    )