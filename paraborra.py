import os

def investigar_bloque():
    ruta_api = r"D:\colegio_vaca_diez\routes\superadmin_api.py"
    ruta_super = r"D:\colegio_vaca_diez\routes\superadmin.py"
    
    print("=== CONTENIDO DE buscar_calificaciones en superadmin_api.py ===")
    if os.path.exists(ruta_api):
        with open(ruta_api, "r", encoding="utf-8", errors="ignore") as f:
            lineas = f.readlines()
            for i, l in enumerate(lineas[21:70], start=22):
                print(f"Línea {i}: {l.rstrip()}")

    print("\n=== BÚSQUEDA DE superadmin_autorizado() ===")
    for ruta in [ruta_api, ruta_super]:
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                for num, linea in enumerate(f, 1):
                    if "def superadmin_autorizado" in linea:
                        print(f"Definido en {os.path.basename(ruta)} (Línea {num}):")
                        f.seek(0)
                        todas = f.readlines()
                        for j in range(num-1, min(num+15, len(todas))):
                            print(f"  {todas[j].rstrip()}")

investigar_bloque()