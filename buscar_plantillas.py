# -*- coding: utf-8 -*-
import os

print("=" * 70)
print("[ BUSCADOR DE ARCHIVOS HTML DE GASTOS ]")
print("=" * 70)

raiz_proyecto = os.path.abspath(os.path.dirname(__file__))
encontrados = 0

for root, dirs, files in os.walk(raiz_proyecto):
    for file in files:
        if 'gasto' in file.lower() and file.endswith('.html'):
            encontrados += 1
            ruta_completa = os.path.join(root, file)
            print(f"[{encontrados}] Archivo encontrado: {ruta_completa}")

if encontrados == 0:
    print("[!] No se encontró ningún archivo HTML con la palabra 'gasto' en el nombre en todo el proyecto.")
else:
    print(f"\nTotal de archivos encontrados: {encontrados}")
print("=" * 70)