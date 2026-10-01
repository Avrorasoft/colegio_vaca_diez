import os

def buscar_texto(texto, directorio):
    # Carpetas a ignorar para que la búsqueda sea rápida
    ignorar = {'venv', '__pycache__', '.git', 'static', 'uploads'}
    
    for raiz, carpetas, archivos in os.walk(directorio):
        # Filtrar carpetas ignoradas
        carpetas[:] = [c for c in carpetas if c not in ignorar]
        
        for archivo in archivos:
            if archivo.endswith('.py') or archivo.endswith('.html'):
                ruta_completa = os.path.join(raiz, archivo)
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        for num_linea, linea in enumerate(f, 1):
                            if texto in linea:
                                print(f"\n[+] ENCONTRADO EN: {ruta_completa} (Línea {num_linea})")
                                print(f"    Código: {linea.strip()}")
                except UnicodeDecodeError:
                    pass

if __name__ == '__main__':
    print("Iniciando rastreo profundo en el proyecto...")
    buscar_texto("guardar_boletin_localmente", ".")
    print("\nRastreo finalizado.")