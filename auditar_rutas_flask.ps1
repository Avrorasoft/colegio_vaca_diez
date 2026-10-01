
# Creamos un script de auditoria en Python para inspeccionar las rutas reales cargadas en Flask
$codigoPython = @'
import sys
from flask import Flask

try:
    # Intentamos importar la instancia de Flask desde app o run
    from app import app
    print("[✔] Instancia de Flask cargada correctamente desde app.py")
except Exception as e:
    print(f"[!] Error al importar la app: {e}")
    sys.exit(1)

print("\n==============================================")
print("       MAPA DE RUTAS ACTIVAS EN FLASK        ")
print("==============================================")
for rule in app.url_map.iter_rules():
    # Destacamos especialmente la ruta raiz "/"
    if rule.rule == "/":
        print(f" >>> [RAIZ DETECTADA] Ruta: {rule.rule} --> Endpoint: {rule.endpoint}")
    else:
        print(f" Ruta: {rule.rule} --> Endpoint: {rule.endpoint}")
print("==============================================\n")
'
Set-Content -Path "auditar_rutas.py" -Value $codigoPython
Write-Host "[*] Script de auditoria generado. Ejecutando analisis..." -ForegroundColor Cyan
python auditar_rutas.py

