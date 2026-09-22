# -*- coding: utf-8 -*-
import os
from app import app

with app.app_context():
    print("=== 🕵️‍♂️ DETECTIVE DE VALIDACIONES Y CAMPOS OBLIGATORIOS ===")
    templates_dir = os.path.join(app.root_path, 'templates')
    
    # 1. Buscar en todas las plantillas HTML
    print("\n[1] Escaneando plantillas HTML por 'required', 'validation' o 'checkValidity'...")
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        rel_path = os.path.relpath(path, app.root_path)
                        if any(k in content.lower() for k in ['required', 'needs-validation', 'checkvalidity', 'novalidate']):
                            print(f"\n📄 Plantilla encontrada: {rel_path}")
                            for idx, line in enumerate(content.splitlines(), 1):
                                if any(k in line.lower() for k in ['required', 'validation', 'novalidate', 'checkvalidity', 'min', 'max']):
                                    print(f"      Línea {idx}: {line.strip()}")
                except Exception as e:
                    pass

    # 2. Buscar en archivos JavaScript estáticos
    static_dir = os.path.join(app.root_path, 'static')
    if os.path.exists(static_dir):
        print("\n[2] Escaneando archivos JavaScript por validaciones de formularios...")
        for root, dirs, files in os.walk(static_dir):
            for file in files:
                if file.endswith('.js'):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if any(k in content.lower() for k in ['checkvalidity', 'required', 'validate', 'submit']):
                                print(f"\n📜 Archivo JS: {os.path.relpath(path, app.root_path)}")
                                for idx, line in enumerate(content.splitlines(), 1):
                                    if any(k in line.lower() for k in ['checkvalidity', 'required', 'validate']):
                                        print(f"      Línea {idx}: {line.strip()}")
                    except Exception:
                        pass
    print("\n=== FIN DEL ESCANEO DETECTIVE ===")