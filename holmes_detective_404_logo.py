# -*- coding: utf-8 -*-
"""
==============================================================================
Script Detective Forense 2.0: Buscador de Patrones de Error 404 en Logos
==============================================================================
"""

import os

# Patrones de riesgo a buscar en las plantillas HTML
PATRONES_RIESGO = [
    "url_for('static'",
    'url_for("static"',
    "static/uploads/",
    "uploads/logo_",
    "configs.institucion_logo",
    "config.institucion_logo"
]

EXTENSIONES_PERMITIDAS = {'.html'}
DIRECTORIOS_EXCLUIDOS = {'venv', '.git', '__pycache__', 'env', 'node_modules', 'dist'}

def escanear_riesgos():
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    hallazgos = 0
    
    print("\n" + "="*80)
    print("🔍 [ESCANEO FORENSE 2.0] Buscando patrones propensos a Error 404 y rutas rotas...")
    print("="*80 + "\n")

    for root, dirs, files in os.walk(ruta_base):
        dirs[:] = [d for d in dirs if d not in DIRECTORIOS_EXCLUIDOS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in EXTENSIONES_PERMITIDAS:
                ruta_archivo = os.path.join(root, file)
                ruta_relativa = os.path.relpath(ruta_archivo, ruta_base)
                
                try:
                    with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
                        lineas = f.readlines()
                        
                    for num_linea, linea in enumerate(lineas, 1):
                        linea_lower = linea.lower()
                        for patron in PATRONES_RIESGO:
                            if patron in linea_lower and ('logo' in linea_lower or 'institucion' in linea_lower):
                                hallazgos += 1
                                print(f"📄 Archivo: {ruta_relativa} | Línea: {num_linea}")
                                print(f"   ⚠️ Patrón detectado ('{patron}'):")
                                print(f"   {linea.strip()}")
                                print("-" * 60)
                                break
                except Exception as e:
                    print(f"⚠️ No se pudo leer {ruta_relativa}: {e}")

    print("\n" + "="*80)
    print(f"🏁 [ESCANEO FINALIZADO] Total de puntos de riesgo detectados: {hallazgos}")
    print("="*80 + "\n")

if __name__ == '__main__':
    escanear_riesgos()