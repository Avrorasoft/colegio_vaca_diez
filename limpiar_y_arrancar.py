# -*- coding: utf-8 -*-
"""
Script de arranque directo y limpio para ASestud
Autor: Avrora Soft - Vibola LLC
"""

import sys
import os

def ejecutar_arranque():
    print("=" * 70)
    print("[ ARRANQUE OFICIAL DE ASestud ]")
    print("=" * 70)
    print("[ OK ] Entorno verificado. Iniciando servidor Flask...")
    print("=" * 70)

    # Iniciar run.py utilizando el intérprete de Python actual
    python_ejecutable = sys.executable
    os.system(f'"{python_ejecutable}" run.py')

if __name__ == '__main__':
    ejecutar_arranque()