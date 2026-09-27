# -*- coding: utf-8 -*-
from app import app

with app.app_context():
    print("=" * 70)
    print("MAPA OFICIAL DE RUTAS REGISTRADAS EN FLASK")
    print("=" * 70)
    for regla in app.url_map.iter_rules():
        if 'gasto' in regla.rule.lower():
            print(f"Ruta: {regla.rule} --> Endpoint: {regla.endpoint} --> Métodos: {list(regla.methods)}")
    print("=" * 70)