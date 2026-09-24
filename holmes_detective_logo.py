# -*- coding: utf-8 -*-
"""
==============================================================================
Script Detective Forense: Escáner de Referencias al Logo e Identidad
==============================================================================
"""

import os

# Palabras clave que el detective buscará en todo el código
PALABRAS_CLAVE = [
    'institucion_logo',
    'logo_institucion',
    'institucion_linea1',
    'institucion_linea2',
    'institucion_linea3',
    'configs.institucion_logo',
    'config.institucion_logo',
    'institucion.institucion_logo',
    'logo_url'
]

# Extensiones de archivos que vamos a auditar
EXTENSIONES_PERMITIDAS = {'.py', '.html', '.js', '.css'}

# Directorios a excluir para no saturar el reporte (entornos virtuales, git, etc.)
DIRECTORIOS_EXCLUIDOS = {'venv', '.git', '__pycache__', 'env', 'node_modules'}

def escanear_proyecto():
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    hallazgos = 0
    
    print("\n" + "="*80)
    print("🔍 [INICIO DEL ESCANEO FORENSE] Buscando referencias a la identidad y logos...")
    print("="*80 + "\n")

    for root, dirs, files in os.walk(ruta_base):
        # Modificar dirs in-place para saltar directorios excluidos
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
                        for palabra in PALABRAS_CLAVE:
                            if palabra in linea_lower:
                                hallazgos += 1
                                print(f"📄 Archivo: {ruta_relativa} | Línea: {num_linea}")
                                print(f"   🎯 Coincidencia ('{palabra}'):")
                                print(f"   {linea.strip()}")
                                print("-" * 60)
                                break # Evitar duplicar la misma línea por múltiples palabras
                except Exception as e:
                    print(f"⚠️ No se pudo leer el archivo {ruta_relativa}: {e}")

    print("\n" + "="*80)
    print(f"🏁 [ESCANEO FINALIZADO] Total de referencias encontradas: {hallazgos}")
    print("="*80 + "\n")

if __name__ == '__main__':
    escanear_proyecto()