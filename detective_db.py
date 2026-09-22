# -*- coding: utf-8 -*-
import sqlite3
import os
from app import app

with app.app_context():
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    db_path = db_uri.replace('sqlite:///', '')
    if not os.path.isabs(db_path):
        db_path = os.path.join(app.root_path, db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = cursor.fetchall()

    print("=== ESTRUCTURA REAL DE LA BASE DE DATOS ===")
    for (tabla,) in tablas:
        print(f"\n Tabla: {tabla}")
        cursor.execute(f"PRAGMA table_info(`{tabla}`);")
        columnas = cursor.fetchall()
        for col in columnas:
            print(f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else ''}")

    conn.close()