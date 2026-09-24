# -*- coding: utf-8 -*-
import sqlite3
import os

def limpiar_bd_definitivo():
    db_path = os.path.join('instance', 'colegio_vaca_diez.db')
    if not os.path.exists(db_path):
        print(f"⚠️ No se encontró la base de datos en {db_path}")
        return

    print(f"\n🔍 Limpiando y saneando la base de datos oficial: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Limpiar tabla configuracion_superadmin (clave-valor)
        try:
            cursor.execute("UPDATE configuracion_superadmin SET valor = 'logo_institucion.png' WHERE clave = 'institucion_logo';")
            print("   -> Tabla 'configuracion_superadmin' saneada con éxito.")
        except Exception as e:
            print(f"   Note (superadmin): {e}")

        # 2. Limpiar tabla configuracion_institucion (si existe y tiene columnas de logo)
        try:
            # Revisar las columnas de la tabla configuracion_institucion
            cursor.execute("PRAGMA table_info(configuracion_institucion);")
            columnas = [col[1] for col in cursor.fetchall()]
            
            if 'institucion_logo' in columnas:
                cursor.execute("UPDATE configuracion_institucion SET institucion_logo = 'logo_institucion.png';")
                print("   -> Tabla 'configuracion_institucion' (columna institucion_logo) saneada con éxito.")
            elif 'logo' in columnas:
                cursor.execute("UPDATE configuracion_institucion SET logo = 'logo_institucion.png';")
                print("   -> Tabla 'configuracion_institucion' (columna logo) saneada con éxito.")
        except Exception as e:
            print(f"   Note (institucion): {e}")

        conn.commit()
        conn.close()
        print("\n✅ ¡Base de datos purgada y blindada correctamente!")
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == '__main__':
    limpiar_bd_definitivo()