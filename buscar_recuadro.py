import os

# Directorio base de tu proyecto Flask (asume que la carpeta templates está en la misma ruta)
DIRECTORIO_TEMPLATES = "templates"

# Palabras clave a buscar (puedes ajustar o añadir términos)
PALABRAS_CLAVE = [
    "VACA DÍEZ",
    "BENI",
    "border",
    "dashed",
    "dotted",
    "COLEGIO"
]

def buscar_en_archivos():
    print(f"[*] Buscando en la carpeta '{DIRECTORIO_TEMPLATES}'...")
    encontrados = 0

    if not os.path.exists(DIRECTORIO_TEMPLATES):
        print(f"[!] No se encontró la carpeta '{DIRECTORIO_TEMPLATES}'. Asegúrate de ejecutar el script en la raíz del proyecto Flask.")
        return

    for root, dirs, files in os.walk(DIRECTORIO_TEMPLATES):
        for file in files:
            if file.endswith(".html"):
                ruta_completa = os.path.join(root, file)
                try:
                    with open(ruta_completa, "r", encoding="utf-8") as f:
                        lineas = f.readlines()
                        
                    for num_linea, linea in enumerate(lineas, 1):
                        # Buscamos coincidencias insensibles a mayúsculas/minúsculas
                        linea_upper = linea.upper()
                        for palabra in PALABRAS_CLAVE:
                            if palabra.upper() in linea_upper:
                                encontrados += 1
                                print(f"\n[ENCUENTRO #{encontrados}]")
                                print(f"  Archivo : {ruta_completa}")
                                print(f"  Línea   : {num_linea}")
                                print(f"  Contenido: {linea.strip()}")
                                break
                except Exception as e:
                    print(f"[!] Error leyendo {ruta_completa}: {e}")

    print(f"\n[*] Búsqueda finalizada. Se encontraron {encontrados} coincidencias.")

if __name__ == "__main__":
    buscar_en_archivos()