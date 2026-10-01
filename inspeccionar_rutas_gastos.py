# -*- coding: utf-8 -*-
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from app import app

print("=" * 80)
print("[ AUDITORÍA DE RUTAS Y PLANTILLAS DE GASTOS ]")
print("=" * 80)

with app.app_context():
    for regla in app.url_map.iter_rules():
        if 'gasto' in regla.rule.lower() or 'gasto' in regla.endpoint.lower():
            func = app.view_functions.get(regla.endpoint)
            modulo = sys.modules.get(func.__module__) if func else None
            archivo_fisico = getattr(modulo, '__file__', 'Desconocido') if modulo else 'Desconocido'
            
            print(f"Ruta URL: {regla.rule}")
            print(f"Endpoint: {regla.endpoint}")
            print(f"Función:  {func.__name__ if func else 'N/A'}")
            print(f"Archivo:  {archivo_fisico}")
            print("-" * 80)