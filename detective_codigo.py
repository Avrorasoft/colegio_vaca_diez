# -*- coding: utf-8 -*-
import os

print("=" * 70)
print("[ DETECTIVE TOTAL: BUSCANDO 'gastos' EN TODO EL PROYECTO ]")
print("=" * 70)

contador = 0
extensiones_validas = ('.py', '.json', '.txt', '.yaml', '.html', '.js')

for root, dirs, files in os.walk('.'):
    # Ignorar entornos virtuales y respaldos
    if 'venv' in root or '__pycache__' in root or '.git' in root:
        continue
        
    for file in files:
        if file.endswith(extensiones_validas):
            ruta_completa = os.path.join(root, file)
            try:
                with open(ruta_completa, 'r', encoding='utf-8', errors='ignore') as f:
                    contenido = f.read()
                    if 'gastos' in contenido.lower() or '/gastos' in contenido.lower():
                        contador += 1
                        print(f"[{contador}] Encontrado ({file}): {ruta_completa}")
            except Exception as e:
                pass

print("=" * 70)
print(f"Búsqueda finalizada. Se encontraron {contador} archivos con referencias a gastos.")