
import os
import shutil
import datetime

def realizar_respaldo_db():
    db_path = r"D:\colegio_vaca_diez\instance\colegio_vaca_diez.db"
    backup_dir = r"D:\colegio_vaca_diez\instance\backups"
    
    if not os.path.exists(db_path):
        return
        
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"colegio_respaldo_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"[✔] Respaldo automático creado con éxito: {backup_filename}")
        
        # Mantener solo los últimos 10 respaldos para evitar saturar el disco
        backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir)], key=os.path.getmtime)
        if len(backups) > 10:
            for old_backup in backups[:-10]:
                os.remove(old_backup)
    except Exception as e:
        print(f"[x] Error al generar respaldo de base de datos: {e}")

