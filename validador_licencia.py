# -*- coding: utf-8 -*-
import os
import hashlib

ARCHIVO_LICENCIA = "licencia.key"

class ValidadorLicencia:
    def __init__(self, serial_ingresado):
        self.serial = serial_ingresado.strip().upper()
        self.valido = False
        self.app_code = ""
        self.tiempo = ""
        self.terminales = 1
        self.hash_interno = ""

    def verificar(self):
        # Formato esperado: AVRO-[APP]-[TIEMPO]-[XX]PC-[HASH]
        # Ejemplo: AVRO-EST-1A-01PC-A1B2C3D4
        partes = self.serial.split("-")
        
        if len(partes) != 5:
            return {"valido": False, "mensaje": "Estructura de licencia inválida. Verifique el código."}
        
        prefijo, self.app_code, self.tiempo, str_pcs, self.hash_interno = partes
        
        if prefijo != "AVRO":
            return {"valido": False, "mensaje": "Prefijo de licencia desconocido."}
        
        # Extraer número de PCs permitidas (ej. '01PC' -> 1)
        try:
            self.terminales = int(str_pcs.replace("PC", ""))
        except ValueError:
            self.terminales = 1

        # Reconstruir los posibles hashes válidos para comprobar contra el lote generado
        encontrado = False
        for i in range(50):
            semilla = f"AVRORA-SOFT-{self.app_code}-{self.tiempo}-{str_pcs}-SECURE-2026-LOTE-{i}"
            h_calculado = hashlib.sha256(semilla.encode("utf-8")).hexdigest()[:8].upper()
            
            if h_calculado == self.hash_interno:
                encontrado = True
                break

        if encontrado:
            self.valido = True
            return {
                "valido": True,
                "mensaje": "¡Licencia válida y autenticada con éxito!",
                "app": self.app_code,
                "vigencia": self.tiempo,
                "pcs": self.terminales
            }
        else:
            return {"valido": False, "mensaje": "Firma de seguridad inválida o serial falso."}

def comprobar_licencia_local():
    """Verifica si existe el archivo individual de licencia ('licencia.key') y si su contenido es válido."""
    if not os.path.exists(ARCHIVO_LICENCIA):
        return False, "No se encontró el archivo de licencia local."
    
    try:
        with open(ARCHIVO_LICENCIA, "r", encoding="utf-8") as f:
            serial_guardado = f.read().strip()
    except Exception as e:
        return False, f"Error al leer el archivo de licencia: {str(e)}"
    
    validador = ValidadorLicencia(serial_guardado)
    resultado = validador.verificar()
    return resultado["valido"], resultado["mensaje"]

def guardar_licencia_local(serial_ingresado):
    """Valida el serial ingresado y lo guarda en el archivo 'licencia.key'."""
    validador = ValidadorLicencia(serial_ingresado)
    resultado = validador.verificar()
    
    if resultado["valido"]:
        try:
            with open(ARCHIVO_LICENCIA, "w", encoding="utf-8") as f:
                f.write(serial_ingresado.strip().upper())
            return True, "¡Licencia registrada y guardada exitosamente!"
        except Exception as e:
            return False, f"Error al guardar el archivo de licencia: {str(e)}"
    else:
        return False, resultado["mensaje"]

# --- Prueba local ---
if __name__ == "__main__":
    valido, mensaje = comprobar_licencia_local()
    print(f"Estado: {mensaje}")