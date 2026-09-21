# -*- coding: utf-8 -*-
"""
Script Detective: Audita la base de datos activa y muestra su contenido exacto.
"""
import os
import sqlite3

def auditar_base_datos():
    ruta_db = os.path.join('instance', 'colegio_vaca_diez.db')
    print(f"🔍 Buscando base de datos en: {os.path.abspath(ruta_db)}")
    
    if not os.path.exists(ruta_db):
        print("❌ ¡ALERTA! El archivo de base de datos NO existe en la ruta instance/.")
        return

    print("✅ ¡Archivo encontrado! Leyendo contenido...\n")
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()

    # 1. Listar todas las tablas existentes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = [t[0] for t in cursor.fetchall()]
    print(f"📋 Tablas encontradas en la BD ({len(tablas)}):")
    print(tablas)
    print("-" * 50)

    # 2. Revisar la tabla de configuración institucional / superadmin
    tabla_config = None
    for posible in ['configuracion_superadmin', 'configuracion_institucion', 'configuracion']:
        if posible in tablas:
            tabla_config = posible
            break

    if tabla_config:
        print(f"📊 Datos en la tabla '{tabla_config}':")
        try:
            cursor.execute(f"SELECT * FROM {tabla_config};")
            filas = cursor.fetchall()
            for fila in filas:
                print(f"  -> {fila}")
        except Exception as e:
            print(f"  ❌ Error al leer registros de la tabla: {e}")
    else:
        print("⚠️ No se encontró una tabla obvia de configuración en la lista.")

    conexion.close()
    print("\n🔍 Auditoría finalizada.")

if __name__ == '__main__':
    auditar_base_datos()