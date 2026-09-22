# -*- coding: utf-8 -*-
import os
from app import app

with app.app_context():
    templates_dir = os.path.join(app.root_path, 'templates')
    busquedas = ['generar_avr', 'restaurar_avr', 'archivo_avr', '.avr']
    
    print("=== 🕵️‍♂️ DETECTIVE DE PLANTILLAS Y REFERENCIAS OBSOLETAS ===")
    encontrados = 0

    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(('.html', '.htm', '.js')):
                ruta_completa = os.path.join(root, file)
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                        
                    for termino in busquedas:
                        if termino in contenido:
                            encontrados += 1
                            rel_path = os.path.relpath(ruta_completa, app.root_path)
                            print(f"\n📄 Archivo encontrado: {rel_path}")
                            print(f"   ⚠️ Contiene la referencia obsoleta: '{termino}'")
                            
                            # Mostrar las líneas específicas con la referencia
                            lineas = contenido.splitlines()
                            for num, linea in enumerate(lineas, 1):
                                if termino in linea:
                                    print(f"      Línea {num}: {linea.strip()}")
                except Exception as e:
                    pass

    if encontrados == 0:
        print("\n✨ ¡Excelente! No se encontraron referencias obsoletas en las plantillas.")
    else:
        print(f"\n🔍 Total de archivos con referencias obsoletas encontrados: {encontrados}")