import os
import sqlite3

db_path = os.path.join('instance', 'colegio_vaca_diez.db')
if not os.path.exists(db_path):
    db_path = 'colegio_vaca_diez.db'

print(f"📄 Usando base de datos: {db_path}")

try:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    
    # Listar tablas
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cur.fetchall()]
    print("Tablas encontradas:", tables)
    
    # Revisar usuarios si existe la tabla
    if 'personal_administrativo' in tables:
        cur.execute("SELECT id, usuario, correo FROM personal_administrativo")
        usuarios = cur.fetchall()
        print("Usuarios en personal_administrativo:", usuarios)
    else:
        print("⚠️ La tabla 'personal_administrativo' no existe.")
        
    con.close()
except Exception as e:
    print("❌ Error:", e)