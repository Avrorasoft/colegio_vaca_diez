# -*- coding: utf-8 -*-
import os
import random
from datetime import date
from app import app
import sqlite3

NOMBRES_M = ["Carlos", "Luis", "José", "Juan", "Miguel", "Alejandro", "Daniel", "Mateo", "Lucas", "David", "Fernando", "Rodrigo", "Marco", "Diego", "Esteban"]
NOMBRES_F = ["Ana", "María", "Carmen", "Lucía", "Sofía", "Valeria", "Gabriela", "Daniela", "Camila", "Mariana", "Elena", "Patricia", "Fernanda", "Jimena", "Paola"]
APELLIDOS = ["Rivero", "Pinto", "Suárez", "Rosellón", "Chávez", "Vaca", "Salvatierra", "Mendoza", "Rojas", "Flores", "Gutiérrez", "Montaño", "Justiniano", "Alvarez", "Téllez"]

NIVELES_CURSOS = [
    "1ro de Primaria", "2do de Primaria", "3ro de Primaria", 
    "4to de Primaria", "5to de Primaria", "6to de Primaria",
    "1ro de Secundaria", "2do de Secundaria", "3ro de Secundaria",
    "4to de Secundaria", "5to de Secundaria", "6to de Secundaria"
]

TURNOS = ["Mañana", "Tarde"]

with app.app_context():
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    db_path = db_uri.replace('sqlite:///', '')
    if not os.path.isabs(db_path):
        db_path = os.path.join(app.root_path, db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🧹 Limpiando registros anteriores de pruebas...")
    cursor.execute("DELETE FROM estudiantes;")
    cursor.execute("DELETE FROM padres;")
    cursor.execute("DELETE FROM profesores;")
    cursor.execute("DELETE FROM personal_administrativo;")
    conn.commit()

    print("👨‍🏫 Creando 40 profesores y administrativos...")
    for i in range(1, 41):
        es_fem = random.choice([True, False])
        nombres = random.choice(NOMBRES_F if es_fem else NOMBRES_M)
        apellidos = f"{random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
        ci = f"5{i:03d}{random.randint(100, 999)}" # CI único garantizado
        telefono = f"7{random.randint(1000000, 9999999)}"
        turno = random.choice(TURNOS)

        if i <= 25: # Profesores
            cursor.execute(
                "INSERT INTO profesores (nombres, apellidos, ci, telefono, turno, estado, especialidad) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (nombres, apellidos, ci, telefono, turno, 'Activo', 'General')
            )
        else: # Administrativos
            cursor.execute(
                "INSERT INTO personal_administrativo (nombres, apellidos, ci, telefono, estado, cargo) VALUES (?, ?, ?, ?, ?, ?)",
                (nombres, apellidos, ci, telefono, 'Activo', random.choice(['Secretaría', 'Contabilidad', 'Regencia']))
            )

    print("👦 Creando 200 estudiantes con padres y kardex de salud completo...")
    tipos_sangre = ["O+", "O-", "A+", "B+", "AB+"]
    alergias_posibles = ["Ninguna", "Polen", "Penicilina", "Lácteos", "Polvo"]

    for i in range(1, 201):
        es_fem = random.choice([True, False])
        nombres = random.choice(NOMBRES_F if es_fem else NOMBRES_M)
        apellidos = f"{random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
        ci_est = f"8{i:03d}{random.randint(100, 999)}" # CI único garantizado para estudiante
        rude = f"892{i:06d}"
        curso = random.choice(NIVELES_CURSOS)
        turno = random.choice(TURNOS)

        # 1. Insertar Estudiante con Kardex de salud lleno
        cursor.execute(
            """INSERT INTO estudiantes (
                nombres, apellidos, ci, rude, curso, turno, estado, pension,
                tipo_sangre, alergias, enfermedades_cronicas, medicamentos_actuales,
                medico_nombre, medico_telefono, clinica_habitual, seguro_medico,
                observaciones_salud, fecha_actualizacion_salud
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                nombres, apellidos, ci_est, rude, curso, turno, 'Activo', 350.0,
                random.choice(tipos_sangre), random.choice(alergias_posibles), 
                "Ninguna reportada", "Ninguno", "Dr. Guardia", f"7{random.randint(1000000, 9999999)}",
                "Clínica Vaca Díez", "Seguro Escolar", "Estudiante apto y saludable.", str(date.today())
            )
        )
        estudiante_id = cursor.lastrowid

        # 2. Insertar Padre asociado con CI único garantizado
        ci_padre = f"4{i:03d}{random.randint(100, 999)}"
        nombre_padre = f"{random.choice(NOMBRES_M)} {apellidos.split()[0]}"
        cursor.execute(
            """INSERT INTO padres (
                estudiante_id, ci, ci_estudiante, rude_estudiante, parentesco,
                nombres, telefono1, ocupacion, email
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                estudiante_id, ci_padre, ci_est, rude, "Padre/Tutor",
                nombre_padre, f"7{random.randint(1000000, 9999999)}", "Independiente", "tutor@colegio.com"
            )
        )

    conn.commit()
    conn.close()
    print("✅ ¡Base de datos poblada exitosamente con 200 estudiantes, padres, kardex de salud y 40 docentes/administrativos!")