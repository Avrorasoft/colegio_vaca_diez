import os

def limpiar_bom_directorio(ruta):
    archivos_limpiados = 0
    # Recorrer todas las carpetas y archivos
    for root, dirs, files in os.walk(ruta):
        for file in files:
            # Solo revisar plantillas HTML y scripts de Python
            if file.endswith(('.html', '.py')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'rb') as f:
                        content = f.read()
                    
                    # Si el archivo empieza con el código hexadecimal del BOM (\xef\xbb\xbf)
                    if content.startswith(b'\xef\xbb\xbf'):
                        # Reescribir el archivo saltando los 3 primeros bytes (el BOM)
                        with open(filepath, 'wb') as f:
                            f.write(content[3:])
                        print(f"[✔] BOM eliminado de: {filepath}")
                        archivos_limpiados += 1
                except Exception as e:
                    print(f"No se pudo leer {filepath}: {e}")
                    
    print(f"\nLimpieza terminada. Se eliminó el BOM de {archivos_limpiados} archivo(s).")

if __name__ == '__main__':
    print("Iniciando escaneo de BOM en el proyecto...")
    # Ejecutar en el directorio actual
    limpiar_bom_directorio('.')