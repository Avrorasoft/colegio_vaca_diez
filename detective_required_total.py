# -*- coding: utf-8 -*-
import os

def buscar_palabra_en_proyecto():
    print("=== 🕵️‍♂️ BUSCADOR TOTAL DE 'REQUIRED' EN EL PROYECTO ===")
    raiz = os.path.dirname(os.path.abspath(__file__))
    
    total_encontrados = 0
    
    for root, dirs, files in os.walk(raiz):
        # Excluir la carpeta virtualenv y git para no saturar
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
            
        for file in files:
            # Revisar archivos HTML, Python y JS
            if file.endswith(('.html', '.py', '.js')):
                ruta_completa = os.path.join(root, file)
                rel_path = os.path.relpath(ruta_completa, raiz)
                
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        lineas = f.readlines()
                        for idx, linea in enumerate(lineas, 1):
                            if 'required' in linea.lower():
                                total_encontrados += 1
                                print(f"📄 [{rel_path}] Línea {idx}: {linea.strip()}")
                except Exception as e:
                    pass
                    
    print(f"\n=== FIN DEL ESCANEO: Se encontraron {total_encontrados} coincidencias de 'required' ===")

if __name__ == '__main__':
    buscar_palabra_en_proyecto()