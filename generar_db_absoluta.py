# -*- coding: utf-8 -*-
import os
import sqlite3
import random

instance_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
os.makedirs(instance_dir, exist_ok=True)
db_file = os.path.join(instance_dir, 'colegio_vaca_diez.db')

if os.path.exists(db_file):
    try:
        os.remove(db_file)
    except Exception:
        pass

print("🛠️ Creando base de datos con la estructura exacta que exige el ORM...")
conexion = sqlite3.connect(db_file)
cursor = conexion.cursor()

# Añadimos la columna 'descripcion' para que el ORM no lance OperationalError
cursor.executescript("""
CREATE TABLE configuracion_superadmin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clave TEXT UNIQUE NOT NULL,
    valor TEXT,
    descripcion TEXT
);

CREATE TABLE estudiante (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rude TEXT,
    nombres TEXT,
    apellidos TEXT,
    curso TEXT,
    turno TEXT,
    tutor TEXT,
    telefono TEXT,
    estado TEXT
);

CREATE TABLE profesor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombres TEXT,
    apellidos TEXT,
    especialidad TEXT,
    telefono TEXT,
    turno TEXT
);
""")

configs = [
    ("institucion_linea1", "UNIDAD EDUCATIVA VACA DÍEZ", "Línea 1"),
    ("institucion_linea2", "Distrito Riberalta", "Línea 2"),
    ("institucion_linea3", "Beni - Bolivia", "Línea 3"),
    ("institucion_configurada", "true", "Setup"),
    ("pwa_password", "VacaDiez2026", "PWA"),
    ("superadmin_password", "Admin2026*", "Admin"),
    ("modo_contabilizacion", "cero", "Modo")
]
cursor.executemany("INSERT OR REPLACE INTO configuracion_superadmin (clave, valor, descripcion) VALUES (?, ?, ?);", configs)

NOMBRES_M = ["Carlos", "José", "Luis", "Miguel", "Alejandro", "Juan", "Daniel", "David", "Javier", "Marco", "Rodrigo", "Fernando", "Diego", "Andrés", "Gabriel", "Lucas", "Mateo", "Adrián", "Samuel", "Thiago"]
NOMBRES_F = ["María", "Ana", "Carmen", "Rosa", "Lucía", "Elena", "Sofía", "Valeria", "Gabriela", "Daniela", "Camila", "Fernanda", "Paola", "Andrea", "Claudia", "Mariana", "Patricia", "Ximena", "Beatriz", "Alejandra"]
APELLIDOS = ["Rivero", "Pinto", "Suárez", "Rosellón", "Vaca", "Díez", "Chávez", "Rojas", "Mamani", "Flores", "Gonzales", "Pérez", "Gutiérrez", "Ticona", "Fernández", "Loayza", "Salvatierra", "Arze", "Mendoza", "Morales"]

TURNOS = ["Mañana", "Tarde"]
CURSOS_LISTA = [
    "1ro Primaria", "2do Primaria", "3ro Primaria", "4to Primaria", "5to Primaria", "6to Primaria",
    "1ro Secundaria", "2do Secundaria", "3ro Secundaria", "4to Secundaria", "5to Secundaria", "6to Secundaria"
]

def generar_nombre():
    sexo = random.choice(['M', 'F'])
    return f"{random.choice(NOMBRES_M if sexo == 'M' else NOMBRES_F)} {random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"

estudiantes_data = []
contador_est = 0

for turno in TURNOS:
    for curso in CURSOS_LISTA:
        lote = 200 // (len(TURNOS) * len(CURSOS_LISTA))
        for _ in range(max(1, lote)):
            if contador_est >= 200:
                break
            nombre_completo = generar_nombre()
            partes = nombre_completo.split()
            nombres = " ".join(partes[:-2]) if len(partes) > 2 else partes[0]
            apellidos = " ".join(partes[-2:]) if len(partes) >= 2 else "Pinto"
            
            estudiantes_data.append((
                f"RUDE{random.randint(10000000, 99999999)}",
                nombres,
                apellidos,
                curso,
                turno,
                generar_nombre(),
                f"7{random.randint(1000000, 9999999)}",
                "Activo"
            ))
            contador_est += 1

while len(estudiantes_data) < 200:
    curso = random.choice(CURSOS_LISTA)
    nombre_completo = generar_nombre()
    partes = nombre_completo.split()
    nombres = " ".join(partes[:-2]) if len(partes) > 2 else partes[0]
    apellidos = " ".join(partes[-2:]) if len(partes) >= 2 else "Pinto"
    estudiantes_data.append((
        f"RUDE{random.randint(10000000, 99999999)}",
        nombres,
        apellidos,
        curso,
        random.choice(TURNOS),
        generar_nombre(),
        f"7{random.randint(1000000, 9999999)}",
        "Activo"
    ))

cursor.executemany("""
INSERT INTO estudiante (rude, nombres, apellidos, curso, turno, tutor, telefono, estado)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
""", estudiantes_data)

profesores_data = []
especialidades = ["Matemáticas", "Física", "Química", "Biología", "Lenguaje", "Sociales", "Inglés", "Artes", "Educación Física", "Música"]
for i in range(40):
    nombre_completo = generar_nombre()
    partes = nombre_completo.split()
    profesores_data.append((
        " ".join(partes[:-2]) if len(partes) > 2 else partes[0],
        " ".join(partes[-2:]) if len(partes) >= 2 else "Pinto",
        random.choice(especialidades),
        f"7{random.randint(1000000, 9999999)}",
        TURNOS[i % 2]
    ))
cursor.executemany("""
INSERT INTO profesor (nombres, apellidos, especialidad, telefono, turno)
VALUES (?, ?, ?, ?, ?);
""", profesores_data)

conexion.commit()
conexion.close()

print(f"✅ ¡Base de datos regenerada con éxito en: {db_file}")