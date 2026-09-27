# -*- coding: utf-8 -*-
"""
Script de auditoría profunda del módulo de caja y turnos.
"""
import os

def revisar_archivo(ruta):
    print("=" * 60)
    print(f"ARCHIVO: {ruta}")
    print("=" * 60)
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            lineas = f.readlines()
            for i, linea in enumerate(lineas, 1):
                l_lower = linea.lower()
                if any(k in l_lower for k in ['session', 'turno', 'caja', 'activo', 'login', 'redirect']):
                    print(f"Línea {i}: {linea.strip()}")
    else:
        print(f"El archivo {ruta} no existe.")
    print("\n")

if __name__ == '__main__':
    revisar_archivo('routes/caja.py')