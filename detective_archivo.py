# -*- coding: utf-8 -*-
import os
from app import app

with app.app_context():
    print("=== 🕵️‍♂️ INSPECTOR DEL ARCHIVO CARGAR_NOTAS.HTML ===" )
    path = os.path.join(app.root_path, 'templates', 'calificaciones', 'cargar_notas.html')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            for idx, linea in enumerate(lineas, 1):
                # Imprimimos líneas que contengan inputs, selects o botones
                if any(k in linea.lower() for k in ['input', 'select', 'form', 'button', 'type', 'name']):
                    print(f"Línea {idx}: {linea.strip()}")
    else:
        print("No se encontró el archivo cargar_notas.html en la ruta esperada.")