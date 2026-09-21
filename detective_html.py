# -*- coding: utf-8 -*-
import os, sqlite3

def auditar():
    db = os.path.join('instance', 'colegio_vaca_diez.db')
    print('DB:', os.path.exists(db))
    if os.path.exists(db):
        con = sqlite3.connect(db)
        print('Claves DB:', con.cursor().execute('SELECT clave, valor FROM configuracion_superadmin').fetchall())
        con.close()
    print('Uploads:', os.listdir('static/uploads') if os.path.exists('static/uploads') else 'No existe')
    for p in ['base.html', 'superadmin/configuracion_institucion.html']:
        ruta = os.path.join('templates', p)
        print(f'Plantilla {p}:', os.path.exists(ruta))
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [l.strip() for l in f if 'institucion' in l.lower() or 'configs' in l.lower()]
                print('  Coincidencias:', lines[:3])

if __name__ == '__main__':
    auditar()
