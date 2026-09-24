import os
from config_paths import DB_PATH

# Destruye el archivo viejo
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("-> Base de datos vieja destruida")

# Crea las tablas en blanco
from app import app, db
with app.app_context():
    db.create_all()
    print("-> Base de datos virgen creada exitosamente")