# -*- coding: utf-8 -*-
import os

def detective_busqueda(palabra_clave="deudores"):
    print("=" * 60)
    print(f"🕵️‍♂️ SCRIPT DETECTIVE - Buscando '{palabra_clave}' en el proyecto...")
    print("=" * 60)
    
    root_dir = "."
    total_coincidencias = 0
    
    for dirpath, _, filenames in os.walk(root_dir):
        # Omitir carpetas del sistema, venv o git
        if any(excluir in dirpath for excluir in ["venv", ".git", "__pycache__", "static"]):
            continue
            
        for file in filenames:
            if file.endswith(".py"):
                filepath = os.path.join(dirpath, file)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        for num_linea, linea in enumerate(f, 1):
                            if palabra_clave.lower() in linea.lower():
                                print(f"📁 Archivo: {filepath} (Línea {num_linea})")
                                print(f"   💡 Código: {linea.strip()}")
                                print("-" * 60)
                                total_coincidencias += 1
                except Exception as e:
                    print(f"⚠️ No se pudo leer {filepath}: {e}")
                    
    print(f"\n🎯 Búsqueda terminada. Se encontraron {total_coincidencias} coincidencias para '{palabra_clave}'.")

if __name__ == "__main__":
    # Puedes cambiar la palabra clave si deseas buscar otra cosa (ej. 'reporte_deudores', 'pensiones', etc.)
    detective_busqueda("deudores")