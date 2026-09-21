# -*- coding: utf-8 -*-
"""
==============================================================================
Script Detective-Auditor: ASestud-Konetz
Desarrollado para diagnóstico interno de entorno, base de datos y configuración.
==============================================================================
"""

import os
import sys
import sqlite3
from datetime import datetime

print("=" * 70)
print("🔍 INICIANDO AUDITORÍA TÉCNICA DEL SISTEMA ASestud-Konetz")
print("=" * 70)

# 1. Auditoría del Entorno de Ejecución
print("\n[1] AUDITORÍA DE ENTORNO PYTHON Y ARCHIVOS:")
print(f"  - Versión de Python: {sys.version}")
print(f"  - Directorio de trabajo: {os.getcwd()}")

archivos_criticos = ['app.py', 'config.py', 'models.py', '.secret_key']
for archivo in archivos_criticos:
    existe = os.path.exists(archivo)
    estado = "✅ Presente" if existe else "❌ Faltante"
    print(f"  - Archivo '{archivo}': {estado}")

# 2. Localización y Auditoría de la Base de Datos SQLite
print("\n[2] AUDITORÍA DE BASE DE DATOS:")
db_path = None
# Intentamos buscar archivos .db en la raíz
archivos_db = [f for f in os.listdir('.') if f.endswith('.db')]
if archivos_db:
    print(f"  - Bases de datos encontradas en raíz: {archivos_db}")
    db_path = archivos_db[0]
else:
    print("  - ⚠️ No se encontró ningún archivo .db directo en la raíz.")

if db_path and os.path.exists(db_path):
    print(f"  - Analizando base de datos activa: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listar tablas existentes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = [row[0] for row in cursor.fetchall()]
        print(f"  - Tablas registradas en SQLite: {tablas}")
        
        # Verificar tabla de configuración institucional / superadmin
        tabla_config = None
        if 'configuracion_superadmin' in tablas:
            tabla_config = 'configuracion_superadmin'
        elif 'configuracion' in tablas:
            tabla_config = 'configuracion'
            
        if tabla_config:
            print(f"  - Tabla de configuración detectada: '{tabla_config}'")
            cursor.execute(f"SELECT clave, valor FROM {tabla_config};")
            filas = cursor.fetchall()
            print(f"  - Registros de configuración encontrados ({len(filas)}):")
            for clave, valor in filas:
                # Ocultar contraseñas largas por seguridad en consola
                val_mostrar = "********" if 'password' in clave.lower() else valor
                print(f"    * {clave} = {val_mostrar}")
        else:
            print("  - ❌ ALERTA: No se encontró la tabla de configuración institucional en la base de datos.")
            
        conn.close()
    except Exception as e:
        print(f"  - ❌ Error al leer la base de datos SQLite: {e}")
else:
    print("  - ❌ No hay archivo de base de datos accesible para auditar.")

# 3. Auditoría de Activos Estáticos y Subidas (Logos)
print("\n[3] AUDITORÍA DE CARPETAS Y ACTIVOS ESTÁTICOS:")
static_dir = os.path.join(os.getcwd(), 'static')
uploads_dir = os.path.join(static_dir, 'uploads')

if os.path.exists(static_dir):
    print("  - Carpeta 'static/': ✅ Presente")
    if os.path.exists(uploads_dir):
        archivos_subidos = os.listdir(uploads_dir)
        print(f"  - Carpeta 'static/uploads/': ✅ Presente (Archivos: {archivos_subidos})")
    else:
        print("  - ⚠️ Carpeta 'static/uploads/': No existe (necesaria para guardar logos institucionales).")
else:
    print("  - ❌ Carpeta 'static/': No encontrada en la raíz del proyecto.")

print("\n" + "=" * 70)
print("🏁 AUDITORÍA FINALIZADA. Copie el resultado impreso arriba para analizarlo.")
print("=" * 70)