# -*- coding: utf-8 -*-
import os
from app import app

with app.app_context():
    print("=== 🕵️‍♂️ DETECTIVE GLOBAL DE JAVASCRIPT Y VALIDACIONES ===")
    static_dir = os.path.join(app.root_path, 'static')
    templates_dir = os.path.join(app.root_path, 'templates')
    
    # 1. Buscar en archivos JS estáticos
    if os.path.exists(static_dir):
        print("\n[1] Buscando en archivos JS (static/)...")
        for root, dirs, files in os.walk(static_dir):
            for file in files:
                if file.endswith('.js'):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if any(k in content.lower() for k in ['checkvalidity', 'invalid-feedback', 'needs-validation', 'submit', 'preventdefault']):
                                print(f"\n📜 Archivo JS sospechoso: {os.path.relpath(path, app.root_path)}")
                                for idx, line in enumerate(content.splitlines(), 1):
                                    if any(k in line.lower() for k in ['checkvalidity', 'needs-validation', 'invalid', 'submit']):
                                        print(f"      Línea {idx}: {line.strip()}")
                    except Exception:
                        pass

    # 2. Buscar bloques <script> dentro de las plantillas HTML (especialmente en base.html)
    print("\n[2] Buscando scripts de validación dentro de plantillas HTML...")
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'checkvalidity' in content.lower() or 'needs-validation' in content.lower() or 'novalidate' in content.lower():
                            print(f"\n📄 Plantilla con lógica de validación: {os.path.relpath(path, app.root_path)}")
                            for idx, line in enumerate(content.splitlines(), 1):
                                if any(k in line.lower() for k in ['checkvalidity', 'needs-validation', 'novalidate', 'validation']):
                                    print(f"      Línea {idx}: {line.strip()}")
                except Exception:
                    pass

    print("\n=== FIN DEL ESCANEO DETECTIVE ===")