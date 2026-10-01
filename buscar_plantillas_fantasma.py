# -*- coding: utf-8 -*-
import os

print("=" * 70)
print("[ BUSCADOR DE ARCHIVOS QUE CONTIENEN LA PALABRA 'Gastos' ]")
print("=" * 70)

contador = 0
for root, dirs, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            ruta_completa = os.path.join(root, file)
            try:
                with open(ruta_completa, 'r', encoding='utf-8', errors='ignore') as f:
                    contenido = f.read()
                    if 'gastos' in contenido.lower():
                        contador += 1
                        print(f"[{contador}] Encontrado en: {ruta_completa}")
            except Exception as e:
                print(f"Error leyendo {ruta_completa}: {e}")

print("=" * 70)
print(f"Búsqueda finalizada. Se encontraron {contador} archivos con referencias a gastos.")