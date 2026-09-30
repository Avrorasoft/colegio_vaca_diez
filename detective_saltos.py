import os
import re

def ejecutar_detective():
    print("========================================================")
    print("  INICIANDO SCRIPT DETECTIVE DE SALTOS (DOM & HTML)")
    print("========================================================")
    
    directorio_templates = "templates"
    if not os.path.exists(directorio_templates):
        print("[-] Error: No se encuentra la carpeta templates.")
        return

    patrones = [
        (r'href=["\']#["\']', "Enlace con href='#' (Provoca scroll al inicio)"),
        (r'href=["\']\s*["\']', "Enlace con href vacío"),
        (r'<form[^>]*action=["\']#["\']', "Formulario con action='#'"),
        (r'onclick=["\'][^"\']*location\.reload\([^)]*\)[^"\']*["\']', "Recarga forzada de página por JS"),
        (r'role=["\']button["\'][^>]*href=["\']#["\']', "Elemento interactivo simulado con salto")
    ]

    hallazgos = 0

    for root, dirs, files in os.walk(directorio_templates):
        for file in files:
            if file.endswith('.html'):
                ruta_archivo = os.path.join(root, file)
                try:
                    with open(ruta_archivo, 'r', encoding='utf-8') as f:
                        lineas = f.readlines()
                    
                    for num_linea, linea in enumerate(lineas, 1):
                        for patron, descripcion in patrones:
                            if re.search(patron, linea, re.IGNORECASE):
                                hallazgos += 1
                                print(f"\n[!] CULPABLE DETECTADO:")
                                print(f"    Archivo: {os.path.relpath(ruta_archivo, '.')}")
                                print(f"    Línea:   {num_linea}")
                                print(f"    Causa:   {descripcion}")
                                print(f"    Código:  {linea.strip()}")
                except Exception as e:
                    print(f"[-] No se pudo leer {file}: {e}")

    print("\n========================================================")
    if hallazgos == 0:
        print("  RESULTADO: No se encontraron elementos sospechosos estándar.")
    else:
        print(f"  RESULTADO: Se encontraron {hallazgos} puntos de conflicto.")
    print("========================================================")

if __name__ == "__main__":
    ejecutar_detective()