# -*- coding: utf-8 -*-
"""
==============================================================================
Archivo: utils_pdf.py
Proyecto: ASestud-Konetz - Sistema de Gestión Escolar
Descripción: Helpers para el MEMBRETE OFICIAL (logo) en todos los PDF.
             La tabla ConfiguracionSuperadmin usa pares clave-valor.
==============================================================================
"""
import os
from reportlab.lib.units import inch


def ruta_logo():
    """Devuelve la ruta absoluta del logo oficial si existe."""
    try:
        from models import ConfiguracionSuperadmin
        cfg = ConfiguracionSuperadmin.query.filter_by(clave='institucion_logo').first()
        if cfg and cfg.valor:
            ruta = os.path.join(os.getcwd(), 'static', cfg.valor)
            if os.path.exists(ruta):
                return ruta
    except Exception:
        pass
    return None


def nombre_institucion():
    """Devuelve el nombre oficial configurado (clave institucion_linea1)."""
    try:
        from models import ConfiguracionSuperadmin
        cfg = ConfiguracionSuperadmin.query.filter_by(clave='institucion_linea1').first()
        if cfg and cfg.valor:
            return cfg.valor
    except Exception:
        pass
    return 'Colegio Dr. Antonio Vaca Díez'


def cabecera_logo(ancho=1.1 * inch):
    """
    Devuelve un flowable Image de reportlab con el logo oficial,
    centrado, listo para agregar al inicio de cualquier PDF.
    Retorna None si no hay logo configurado.
    """
    try:
        from reportlab.platypus import Image
        ruta = ruta_logo()
        if ruta:
            img = Image(ruta, width=ancho, height=ancho)
            img.hAlign = 'CENTER'
            return img
    except Exception:
        pass
    return None
