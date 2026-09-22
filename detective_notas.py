# -*- coding: utf-8 -*-
import os
from app import app

with app.app_context():
    routes_dir = os.path.join(app.root_path, 'routes')
    print("=== 🕵️‍♂️ DETECTIVE DE CONSULTAS DE CALIFICACIONES ===")
    
    for root, dirs, files in os.walk(routes_dir):
        for file in files:
            if file.endswith('.py'):
                ruta_completa = os.path.join(root, file)
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                        if 'Calificacion' in contenido or 'calificaciones' in contenido.lower():
                            rel_path = os.path.relpath(ruta_completa, app.root_path)
                            print(f"\n📄 Archivo: {rel_path}")
                            for num, linea in enumerate(contenido.splitlines(), 1):
                                if 'calificacion' in linea.lower() or 'query' in linea.lower() or 'join' in linea.lower():
                                    print(f"      Línea {num}: {linea.strip()}")
                except Exception:
                    pass