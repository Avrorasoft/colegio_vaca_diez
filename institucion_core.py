# -*- coding: utf-8 -*-
"""
==============================================================================
Santuario de Identidad Institucional (Motor Exclusivo de Logo y Textos)
==============================================================================
"""

import os
from flask import url_for, current_app, flash

def obtener_identidad_institucional():
    """Única fuente de verdad en todo el sistema para leer y sanitizar la identidad."""
    identidad = {
        'institucion_linea1': 'Sistema de Gestión Escolar',
        'institucion_linea2': '',
        'institucion_linea3': '',
        'institucion_direccion': '',
        'institucion_telefono': '',
        'institucion_email': '',
        'institucion_ciudad': '',
        'institucion_gestion': '2026',
        'institucion_logo': 'logo_institucion.png'
    }
    
    try:
        from models import ConfiguracionSuperadmin
        registros = ConfiguracionSuperadmin.query.all()
        for reg in registros:
            if reg.clave in identidad and reg.valor is not None:
                val = str(reg.valor).strip()
                if reg.clave == 'institucion_logo':
                    if val:
                        # Sanitización radical: extraer solo el nombre plano
                        val = val.replace('\\', '/').split('?')[0].split('/')[-1]
                    else:
                        val = 'logo_institucion.png'
                identidad[reg.clave] = val
    except Exception:
        pass

    # Generar la URL oficial absoluta y blindada para el navegador
    nombre_logo = identidad.get('institucion_logo', 'logo_institucion.png')
    if not nombre_logo:
        nombre_logo = 'logo_institucion.png'
        
    logo_url_oficial = url_for('servir_archivo_subido', filename=nombre_logo)
    
    identidad['institucion_logo'] = logo_url_oficial
    identidad['institucion_logo_url'] = logo_url_oficial
    
    return identidad


def guardar_logo_institucional(archivo_logo):
    """Única función autorizada para validar, limpiar y guardar el logo en disco y BD."""
    if not archivo_logo or not archivo_logo.filename:
        return False
        
    extensiones_permitidas = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    extension = archivo_logo.filename.rsplit('.', 1)[-1].lower() if '.' in archivo_logo.filename else ''
    
    if extension not in extensiones_permitidas:
        flash('❌ Formato de imagen inválido. Use: PNG, JPG, JPEG, GIF, WEBP o SVG.', 'danger')
        return False
        
    archivo_logo.seek(0, os.SEEK_END)
    tamano = archivo_logo.tell()
    archivo_logo.seek(0)
    
    if tamano > 5 * 1024 * 1024:
        flash('❌ El logo excede el tamaño máximo permitido (5MB).', 'danger')
        return False
        
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Limpiar logos anteriores físicamente en disco
    for ext_posible in extensiones_permitidas:
        archivo_antiguo = os.path.join(upload_dir, f'logo_institucion.{ext_posible}')
        if os.path.exists(archivo_antiguo):
            try:
                os.remove(archivo_antiguo)
            except Exception:
                pass

    # Guardar con nombre estándar seguro (ej: logo_institucion.png)
    nombre_seguro = 'logo_institucion.png'
    ruta_destino = os.path.join(upload_dir, nombre_seguro)
    archivo_logo.save(ruta_destino)
    
    # Registrar el nombre plano en la base de datos
    try:
        from models import db, ConfiguracionSuperadmin
        cfg_logo = ConfiguracionSuperadmin.query.filter_by(clave='institucion_logo').first()
        if cfg_logo:
            cfg_logo.valor = 'logo_institucion.png'
        else:
            nuevo_logo = ConfiguracionSuperadmin(
                clave='institucion_logo',
                valor='logo_institucion.png',
                descripcion='Logo oficial de la institución'
            )
            db.session.add(nuevo_logo)
        db.session.commit()
        flash('✅ Logo actualizado correctamente.', 'success')
        return True
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error al registrar el logo en la base de datos: {str(e)}', 'danger')
        return False