# -*- coding: utf-8 -*-
import os
import sys

print("=" * 70)
print("🔍 VERIFICACIÓN DE LOGOS INSTITUCIONALES - ASestud")
print("=" * 70)

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

print(f"📁 Directorio Base: {BASE_DIR}")

# 1. Verificar icono de la aplicación (.ico)
ruta_ico = os.path.join(BASE_DIR, "asestud_icon.ico")
existe_ico = os.path.exists(ruta_ico)
print(f"\n[1] Icono de Ventana y Ejecutable (.ico):")
print(f"    Ruta esperada: {ruta_ico}")
print(f"    Estado: {'✅ ¡ENCONTRADO!' if existe_ico else '❌ FALTA (Colócalo en la raíz)'}")

# 2. Verificar logotipo institucional (.png)
ruta_png = os.path.join(BASE_DIR, "static", "uploads", "logo_institucion.png")
existe_png = os.path.exists(ruta_png)
print(f"\n[2] Logotipo Institucional (logo_institucion.png):")
print(f"    Ruta esperada: {ruta_png}")
print(f"    Estado: {'✅ ¡ENCONTRADO!' if existe_png else '❌ FALTA (Colócalo en static/uploads/)'}")

print("=" * 70)
if existe_ico and existe_png:
    print("🎉 ¡Todo está en orden! Ambos archivos están listos para la compilación.")
else:
    print("⚠️ Por favor, asegúrate de colocar el archivo faltante en su carpeta correspondiente.")
print("=" * 70)