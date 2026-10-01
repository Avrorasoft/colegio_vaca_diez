# -*- coding: utf-8 -*-
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from app import app

print("=" * 70)
print("[ SCRIPT DETECTIVE: RUTA REAL DE PLANTILLAS DE GASTOS ]")
print("=" * 70)

with app.app_context():
    # Inspeccionar dónde busca el loader de Jinja2
    print("\n1. Directorios de búsqueda configurados en Jinja2:")
    for loader in app.jinja_loader.loaders if hasattr(app.jinja_loader, 'loaders') else [app.jinja_loader]:
        if hasattr(loader, 'searchpath'):
            for p in loader.searchpath:
                print(f"   -> {p}")

    # Forzar la resolución de las plantillas que usa el blueprint de gastos
    print("\n2. Intentando resolver plantillas para el endpoint de gastos:")
    for endpoint_name in ['gastos.index', 'gastos.nuevo']:
        if endpoint_name in app.view_functions:
            func = app.view_functions[endpoint_name]
            print(f"   Endpoint '{endpoint_name}' apunta a la función: {func.__name__}")
            
            # Verificamos qué archivos de plantilla existen en las rutas comunes
            print("   Buscando archivos físicos candidatos:")
            candidatos = [
                'gastos/index.html', 'gastos/form.html',
                'gastos.html', 'form_gasto.html', 'nuevo_gasto.html',
                'index_gastos.html', 'gastos_index.html'
            ]
            for c in candidatos:
                try:
                    app.jinja_env.get_template(c)
                    print(f"      [✔ ENCONTRADO Y VÁLIDO]: templates/{c}")
                except Exception:
                    pass

print("=" * 70)