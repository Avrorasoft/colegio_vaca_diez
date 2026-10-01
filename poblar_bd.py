import os
import random
from datetime import date, timedelta
from app import app, db
from models import (
    Estudiante, Padre, Profesor, PersonalAdministrativo, 
    ConfiguracionSuperadmin, ConfiguracionInstitucion
)

def poblar_base_de_datos():
    with app.app_context():
        # 1. Limpiar y recrear tablas desde cero
        db.drop_all()
        db.create_all()
        print("🧹 Base de datos limpiada y recreada correctamente.")

        # 2. CONFIGURACIONES INICIALES
        try:
            cfg_sup = ConfiguracionSuperadmin(clave='superadmin_password', valor='admin', descripcion='Contraseña de superadministrador')
            db.session.add(cfg_sup)
        except Exception:
            pass

        try:
            cfg_inst = ConfiguracionInstitucion(
                institucion_linea1='UNIDAD EDUCATIVA "AMAZONAS"',
                institucion_linea2='Riberalta - Beni - Bolivia',
                institucion_linea3='Secretaría de Educación'
            )
            db.session.add(cfg_inst)
        except Exception:
            pass
        
        db.session.commit()
        print("⚙️ Credenciales y configuraciones iniciales creadas.")

        # Listas de nombres y apellidos realistas
        nombres_m = ["Juan Carlos", "Luis Miguel", "José Antonio", "Carlos Alberto", "Miguel Ángel", "Daniel Alejandro", "Rodrigo", "Alejandro", "Diego", "Fernando", "Gabriel", "Lucas", "Mateo", "Thiago", "Samuel", "David", "Adrian", "Javier", "Marcos", "Vicente"]
        nombres_f = ["María Elena", "Ana Sofía", "Carmen Rosa", "Lucía Fernanda", "Valeria", "Camila", "Gabriela", "Daniela", "Mariana", "Victoria", "Paula", "Martina", "Sara", "Jimena", "Renata", "Florencia", "Antonella", "Bianca", "Ariana", "Elena"]
        apellidos_lista = ["Rivero", "Pinto", "Suárez", "Rosellón", "Vaca", "Díez", "Chávez", "Tineo", "Salvatierra", "Gutiérrez", "Mendoza", "Fernández", "Mamani", "Quispe", "Flores", "Rojas", "López", "Gonzáles", "Pérez", "Castillo", "Medina", "Añez", "Yabeta", "Navia", "Vargas"]
        cursos = ["1ro Secundaria", "2do Secundaria", "3ro Secundaria", "4to Secundaria", "5to Secundaria", "6to Secundaria"]
        cargos_admin = ["Secretaría", "Contabilidad", "Regencia", "Portería", "Administración"]

        # 3. GENERAR 40 PROFESORES (20 Mañana / 20 Tarde)
        print("👨‍🏫 Generando 40 profesores...")
        for i in range(40):
            turno = "Mañana" if i < 20 else "Tarde"
            es_femenino = random.choice([True, False])
            prof = Profesor(
                ci=f"P{random.randint(1000000, 9999999)}",
                nombres=random.choice(nombres_f if es_femenino else nombres_m),
                apellidos=f"{random.choice(apellidos_lista)} {random.choice(apellidos_lista)}",
                turno=turno,
                estado="Activo",
                salario_base=3500.0
            )
            db.session.add(prof)
        db.session.commit()

        # 4. GENERAR 10 ADMINISTRATIVOS
        print("💼 Generando 10 administrativos...")
        for i in range(10):
            es_femenino = random.choice([True, False])
            admin = PersonalAdministrativo(
                ci=f"A{random.randint(1000000, 9999999)}",
                nombres=random.choice(nombres_f if es_femenino else nombres_m),
                apellidos=f"{random.choice(apellidos_lista)} {random.choice(apellidos_lista)}",
                cargo=random.choice(cargos_admin),
                estado="Activo",
                salario_base=3000.0
            )
            db.session.add(admin)
        db.session.commit()

        # 5. GENERAR 200 ESTUDIANTES Y SUS PADRES (Con C.I. de tutor único garantizado)
        print("📚 Generando 200 estudiantes y sus padres...")
        estudiantes_creados = 0
        while estudiantes_creados < 200:
            es_femenino = random.choice([True, False])
            nombre = random.choice(nombres_f if es_femenino else nombres_m)
            apellidos = f"{random.choice(apellidos_lista)} {random.choice(apellidos_lista)}"
            ci = f"{random.randint(4000000, 9999999)}"
            
            if Estudiante.query.filter_by(ci=ci).first():
                continue

            rude = f"80{random.randint(1000000000, 9999999999)}"
            turno = random.choice(["Mañana", "Tarde"])
            estudiante = Estudiante(
                ci=ci,
                rude=rude,
                apellidos=apellidos,
                nombres=nombre,
                fecha_nacimiento=date.today() - timedelta(days=random.randint(365 * 12, 365 * 18)),
                curso=random.choice(cursos),
                turno=turno,
                estado="Activo",
                pension=350.0 if turno == "Mañana" else 300.0,
                direccion=f"Barrio Central, Calle {random.randint(1, 20)}",
                zona="Central",
                ciudad="Riberalta",
                tipo_sangre=random.choice(["O+", "A+", "B+"])
            )
            db.session.add(estudiante)
            db.session.flush() # Obtener estudiante.id

            # C.I. del tutor único basado en el índice y un número aleatorio seguro
            tutor_ci = f"T{random.randint(10, 99)}{ci}"
            tutor_nombre = f"Tutor {nombre.split()[0]} {apellidos.split()[0]}"
            
            padre = Padre(
                estudiante_id=estudiante.id,
                ci=tutor_ci,
                ci_estudiante=ci,
                rude_estudiante=rude,
                parentesco=random.choice(["Padre", "Madre", "Tutor/a"]),
                nombres=tutor_nombre,
                telefono1=f"7{random.randint(1000000, 9999999)}",
                ocupacion="Independiente"
            )
            db.session.add(padre)
            estudiantes_creados += 1

        db.session.commit()
        print(f"✅ ¡Base de datos poblada al 100% con éxito!")
        print(f"   • 200 Estudiantes con sus Padres")
        print(f"   • 40 Profesores")
        print(f"   • 10 Administrativos")

if __name__ == '__main__':
    poblar_base_de_datos()