# -*- coding: utf-8 -*-
"""
Script de prueba automatizada con sesión activa para verificar el candado de caja.
Autor: Avrora Soft - Vibola LLC
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import app

def probar_candado_con_sesion():
    print("=" * 70)
    print("[ PRUEBA AUTOMATIZADA CON SESIÓN: GASTOS SIN TURNO DE CAJA ]")
    print("=" * 70)

    with app.test_client() as cliente:
        # 1. Simular inicio de sesión inyectando variables reales en la sesión de Flask
        with cliente.session_transaction() as sess:
            sess['user_id'] = 1
            sess['logged_in'] = True
            sess['rol'] = 'admin'
            # NO colocamos 'turno_activo' ni 'turno' para probar el bloqueo

        # 2. Intentar acceder a /gastos/nuevo con sesión pero sin turno
        respuesta = cliente.get('/gastos/nuevo', follow_redirects=False)

        print(f"📊 Código de estado HTTP recibido: {respuesta.status_code}")
        print(f"🔗 URL de redirección (Header Location): {respuesta.headers.get('Location', 'Ninguna')}")
        
        ubicacion = respuesta.headers.get('Location', '')
        if 'caja' in ubicacion or 'turno' in ubicacion:
            print("[ ✔ ÉXITO TOTAL ]: El candado detectó la ausencia de turno y redirigió a caja correctamente.")
        else:
            print(f"[ ❌ FALLO ]: Redirigió a '{ubicacion}' en lugar de exigir turno de caja.")
            
    print("=" * 70)

if __name__ == '__main__':
    probar_candado_con_sesion()