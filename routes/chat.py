# -*- coding: utf-8 -*-
import os
from urllib.parse import urlparse
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    current_app,
    abort,
    send_file
)
from models import db, Mensaje, Estudiante, Padre, Pago, Calificacion, Materia
from datetime import datetime, timezone, timedelta
from werkzeug.utils import secure_filename
from utils.boletin_generator import generar_boletin_pdf, guardar_boletin_localmente

chat_bp = Blueprint('chat', __name__, template_folder='templates/chat')

# Zona horaria Bolivia
BOLIVIA_TZ = timezone(timedelta(hours=-4))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'mp3', 'wav', 'ogg', 'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# ==============================================================================
# FUNCIONES PARA MANEJAR ARCHIVOS ADJUNTOS LOCALES
# ==============================================================================

def extraer_adjunto(contenido):
    """
    Separa el texto del mensaje y la ruta del archivo adjunto.
    El formato usado es:
    ---ARCHIVO_ADJUNTO---/static/boletines/archivo.pdf
    """
    if not contenido or '---ARCHIVO_ADJUNTO---' not in contenido:
        return None, contenido or ''

    texto, _, adjunto = contenido.partition('---ARCHIVO_ADJUNTO---')
    return adjunto.strip(), texto.strip()


def ruta_local_segura(ruta):
    """
    Convierte una ruta /static/... o una URL local en una ruta real del disco.
    Solo permite archivos dentro de la carpeta static del proyecto.
    """
    if not ruta:
        return None

    ruta = ruta.strip()

    # Si viene como URL completa, por ejemplo:
    # http://127.0.0.1:5000/static/boletines/archivo.pdf
    parsed = urlparse(ruta)
    if parsed.scheme:
        ruta = parsed.path

    ruta = ruta.replace('\\', '/')

    # Normalizar rutas que contienen /static/
    if '/static/' in ruta:
        ruta = ruta.split('/static/', 1)[1]
    elif ruta.startswith('static/'):
        ruta = ruta[len('static/'):]

    static_root = os.path.abspath(current_app.static_folder)
    filepath = os.path.abspath(os.path.join(static_root, ruta))

    # Seguridad: evitar que se pueda acceder fuera de static
    if not filepath.startswith(static_root):
        return None

    if not os.path.isfile(filepath):
        return None

    return filepath
def ahora_bolivia():
    """Devuelve la fecha/hora actual en zona horaria Bolivia (UTC-4)"""
    return datetime.now(BOLIVIA_TZ)

def personalizar_texto_mensaje(texto_base, estudiante, padre, calificaciones=None, materias=None):
    """Reemplaza los comodines [Tutor], [Estudiante], etc. por los datos reales del alumno."""
    if not texto_base:
        return ""
        
    texto = texto_base
    nombre_tutor = padre.nombres if padre and padre.nombres else 'Padre de Familia'
    
    # 1. Corrección de saludos dobles y nombres
    texto = texto.replace('Sr./Sra. Sr./Sra. [Tutor]', f'Sr./Sra. {nombre_tutor}')
    texto = texto.replace('Sr./Sra. [Tutor]', f'Sr./Sra. {nombre_tutor}')
    texto = texto.replace('[Tutor]', nombre_tutor)
    
    # 2. Datos del estudiante
    texto = texto.replace('[Estudiante]', f"{estudiante.nombres} {estudiante.apellidos}")
    texto = texto.replace('[Curso]', estudiante.curso)
    
    # 3. Cálculos académicos precisos para el Boletín
    materias_aprobadas = 0
    materias_reprobadas = 0
    promedios = []
    
    if calificaciones and materias:
        for mat in materias:
            notas = [c.nota for c in calificaciones if c.materia_id == mat.id]
            if notas:
                prom = sum(notas) / len(notas)
                promedios.append(prom)
                if prom >= 51:
                    materias_aprobadas += 1
                else:
                    materias_reprobadas += 1
                    
        promedio_final = f"{sum(promedios)/len(promedios):.2f}" if promedios else "0.00"
    else:
        promedio_final = "0.00"

    texto = texto.replace('Promedio General: N/A', f'Promedio General: {promedio_final}')
    texto = texto.replace('Materias aprobadas: 0', f'Materias aprobadas: {materias_aprobadas}')
    texto = texto.replace('Materias reprobadas: 0', f'Materias reprobadas: {materias_reprobadas}')
    
    return texto

# =========================================================================
# PLANTILLAS PROFESIONALES CON DATOS DINÁMICOS
# =========================================================================
PLANTILLAS = {
    'General': (
        "Estimado/a Sr./Sra. {tutor}:\n\n"
        "Reciba un cordial y respetuoso saludo de parte de la Dirección del Colegio Dr. Antonio Vaca Díez.\n\n"
        "Por medio de la presente, nos dirigimos a usted para comunicarle lo siguiente:\n\n"
        "[ESCRIBA AQUÍ SU MENSAJE]\n\n"
        "Agradecemos de antemano su atención y quedamos a su entera disposición para cualquier consulta.\n\n"
        "Atentamente,\n"
        "LA DIRECCIÓN\n"
        "Colegio Dr. Antonio Vaca Díez\n"
        "Riberalta, Beni - Bolivia"
    ),
    'Citación': (
        "COLEGIO DR. ANTONIO VACA DÍEZ\n"
        "Dirección Administrativa y Académica\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "ASUNTO: Citación Obligatoria a Reunión\n\n"
        "Estimado/a Sr./Sra. {tutor}:\n\n"
        "Por medio de la presente, la Dirección del Colegio Dr. Antonio Vaca Díez tiene el agrado de dirigirse a usted para citarle a una reunión de carácter OBLIGATORIO.\n\n"
        "DATOS DEL ESTUDIANTE:\n"
        "• Nombre: {estudiante}\n"
        "• Curso: {curso}\n\n"
        "DETALLES DE LA REUNIÓN:\n"
        "• Fecha: {fecha}\n"
        "• Hora: {hora}\n"
        "• Lugar: Salón de Usos Múltiples del Colegio\n\n"
        "Su puntual asistencia es indispensable. En caso de inasistencia injustificada, se procederá conforme al Reglamento Interno.\n\n"
        "Atentamente,\n"
        "LA DIRECCIÓN\n"
        "Colegio Dr. Antonio Vaca Díez"
    ),
    'Recordatorio de Pago': (
        "COLEGIO DR. ANTONIO VACA DÍEZ\n"
        "Departamento de Administración\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "ASUNTO: Recordatorio Amistoso de Pago de Pensión\n\n"
        "Estimado/a Sr./Sra. {tutor}:\n\n"
        "Reciba un cordial saludo. Por medio de la presente, el Departamento de Administración le recuerda amablemente que el/la estudiante {estudiante} del curso {curso} presenta pendiente el pago de la pensión escolar.\n\n"
        "DETALLE DE LA DEUDA:\n"
        "• Meses adeudados: {meses}\n"
        "• Monto total pendiente: Bs. {monto}\n"
        "• Gestión: {gestion}\n\n"
        "Le solicitamos muy comedidamente regularizar esta situación a la brevedad posible en la oficina de Administración (horario: 8:00 a 12:00 y 14:00 a 18:00).\n\n"
        "Si usted ya realizó el pago, le rogamos hacer caso omiso de este mensaje.\n\n"
        "Atentamente,\n"
        "DEPARTAMENTO DE ADMINISTRACIÓN\n"
        "Colegio Dr. Antonio Vaca Díez"
    ),
    'Comprobante de Pago': (
        "COLEGIO DR. ANTONIO VACA DÍEZ\n"
        "Departamento de Administración\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "ASUNTO: Comprobante Oficial de Pago Recibido\n\n"
        "Estimado/a Sr./Sra. {tutor}:\n\n"
        "El Departamento de Administración confirma la recepción exitosa del pago realizado por concepto de pensión escolar.\n\n"
        "DETALLE DE LA TRANSACCIÓN:\n"
        "• Estudiante: {estudiante}\n"
        "• Curso: {curso}\n"
        "• Mes correspondiente: {mes}\n"
        "• Monto cancelado: Bs. {monto}\n"
        "• Fecha de registro: {fecha}\n\n"
        "Este mensaje tiene plena validez como comprobante de pago.\n\n"
        "Atentamente,\n"
        "LA DIRECCIÓN ADMINISTRATIVA\n"
        "Colegio Dr. Antonio Vaca Díez"
    ),
    'Inasistencia': (
        "COLEGIO DR. ANTONIO VACA DÍEZ\n"
        "Departamento de Disciplina y Seguimiento\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "ASUNTO: Comunicado de Inasistencia Injustificada\n\n"
        "Estimado/a Sr./Sra. {tutor}:\n\n"
        "La Dirección del Colegio Dr. Antonio Vaca Díez le informa que el/la estudiante {estudiante} del curso {curso} ha registrado inasistencia a clases el día {fecha}, sin la debida justificación.\n\n"
        "Le solicitamos atentamente:\n"
        "1. Presentar la justificación correspondiente en la oficina de Dirección dentro de las 48 horas hábiles.\n"
        "2. Coordinar una reunión con el tutor del curso.\n\n"
        "Atentamente,\n"
        "LA DIRECCIÓN\n"
        "Colegio Dr. Antonio Vaca Díez"
    ),
    'Felicitación': (
        "COLEGIO DR. ANTONIO VACA DÍEZ\n"
        "Dirección Académica\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "ASUNTO: Felicitación y Reconocimiento al Mérito Académico\n\n"
        "Estimado/a Sr./Sra. {tutor}:\n\n"
        "Es un verdadero honor para la Dirección del Colegio Dr. Antonio Vaca Díez dirigirse a usted para expresarle nuestras más sinceras felicitaciones por el excelente desempeño académico de su hijo/a {estudiante} del curso {curso}.\n\n"
        "LOGROS DESTACADOS:\n"
        "• Promedio general ponderado: {promedio}\n"
        "• Mejor materia: {mejor_materia} ({nota_mejor})\n\n"
        "Este reconocimiento refleja el compromiso, la dedicación y el esfuerzo constante del/la estudiante.\n\n"
        "Con admiración y respeto,\n"
        "LA DIRECCIÓN ACADÉMICA\n"
        "Colegio Dr. Antonio Vaca Díez"
    ),
    'Boletín': (
        "COLEGIO DR. ANTONIO VACA DÍEZ\n"
        "Departamento Académico\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "ASUNTO: Notificación de Disponibilidad de Boletín de Calificaciones\n\n"
        "Estimado/a Sr./Sra. {tutor}:\n\n"
        "Reciba un cordial saludo. Tengo el agrado de informarle que el Boletín de Calificaciones de la gestión actual del estudiante {estudiante} ya se encuentra disponible en formato PDF adjunto a este mensaje.\n\n"
        "RESUMEN ACADÉMICO:\n"
        "• Promedio General: {promedio}\n"
        "• Materias aprobadas: {materias_aprobadas}\n"
        "• Materias reprobadas: {materias_reprobadas}\n\n"
        "Le rogamos descargar el documento, revisarlo detalladamente y firmar de conformidad.\n\n"
        "Atentamente,\n"
        "LA DIRECCIÓN ACADÉMICA\n"
        "Colegio Dr. Antonio Vaca Díez"
    )
}

# =========================================================================
# LISTA DE CHATS
# =========================================================================
@chat_bp.route('/')
def index():
    mensajes = Mensaje.query.order_by(Mensaje.fecha_envio.desc()).limit(100).all()

    total_mensajes = len(mensajes)
    total_comprobantes = sum(1 for m in mensajes if 'pago' in (m.tipo_mensaje or '').lower() or 'comprobante' in (m.tipo_mensaje or '').lower())
    total_faltas = sum(1 for m in mensajes if 'falta' in (m.tipo_mensaje or '').lower() or 'inasistencia' in (m.tipo_mensaje or '').lower())
    total_citaciones = sum(1 for m in mensajes if 'citación' in (m.tipo_mensaje or '').lower() or 'citacion' in (m.tipo_mensaje or '').lower())
    total_felicitaciones = sum(1 for m in mensajes if 'felicitación' in (m.tipo_mensaje or '').lower() or 'felicitacion' in (m.tipo_mensaje or '').lower())
    total_boletines = sum(1 for m in mensajes if 'boletín' in (m.tipo_mensaje or '').lower() or 'boletin' in (m.tipo_mensaje or '').lower())

    filtro_tipo = request.args.get('tipo', '')
    if filtro_tipo:
        mensajes = [m for m in mensajes if filtro_tipo.lower() in (m.tipo_mensaje or '').lower()]

    return render_template('chat/index.html',
                         mensajes=mensajes,
                         total_mensajes=total_mensajes,
                         total_comprobantes=total_comprobantes,
                         total_faltas=total_faltas,
                         total_citaciones=total_citaciones,
                         total_felicitaciones=total_felicitaciones,
                         total_boletines=total_boletines,
                         filtro_actual=filtro_tipo)

# =========================================================================
# ENVIAR MENSAJE (Individual o Masivo con Plantillas y Archivos)
# =========================================================================
@chat_bp.route('/enviar', methods=['GET', 'POST'])
def enviar():
    if request.method == 'POST':
        try:
            tipo_mensaje = request.form.get('tipo_mensaje', 'General')
            contenido_base = request.form.get('contenido', '').strip()
            modo_envio = request.form.get('modo_envio', 'individual')
            archivo_path_manual = None

            # Manejo SEGURO de archivo adjunto subido manualmente
            if 'archivo' in request.files:
                file = request.files['archivo']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(f"chat_{int(datetime.now().timestamp())}_{file.filename}")
                    upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'chat')
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    archivo_path_manual = f"/static/uploads/chat/{filename}"

            # -------------------------------------------------------------
            # MASIVO A TODOS
            # -------------------------------------------------------------
            if modo_envio == 'masivo_todos':
                estudiantes = Estudiante.query.filter_by(estado='Activo').all()
                count = 0
                for est in estudiantes:
                    padre = Padre.query.filter_by(estudiante_id=est.id).first()
                    if padre and padre.nombres:
                        calificaciones = Calificacion.query.filter_by(estudiante_id=est.id).all()
                        materias = Materia.query.all()
                        
                        if tipo_mensaje == 'Boletín':
                            tiene_deuda = Pago.query.filter_by(estudiante_id=est.id, estado='Pendiente').first()
                            if tiene_deuda:
                                continue # FILTRO ANTI-MOROSOS
                                
                            pdf_bytes = generar_boletin_pdf(est, calificaciones, materias)
                            ruta_pdf = guardar_boletin_localmente(pdf_bytes, est.id, ahora_bolivia().year, est.rude)
                            
                            texto_limpio = personalizar_texto_mensaje(contenido_base, est, padre, calificaciones, materias)
                            contenido_final = f"{texto_limpio}\n\n---ARCHIVO_ADJUNTO---{ruta_pdf}"
                        
                        else:
                            texto_limpio = personalizar_texto_mensaje(contenido_base, est, padre, calificaciones, materias)
                            if archivo_path_manual:
                                contenido_final = f"{texto_limpio}\n\n---ARCHIVO_ADJUNTO---{archivo_path_manual}"
                            else:
                                contenido_final = texto_limpio

                        msg = Mensaje(
                            destinatario=padre.nombres,
                            estudiante_id=est.id,
                            telefono=padre.telefono1 or 'Sin teléfono',
                            tipo_mensaje=tipo_mensaje,
                            contenido=contenido_final,
                            remitente='Colegio'
                        )
                        db.session.add(msg)
                        count += 1
                db.session.commit()
                flash(f'✅ Mensaje enviado a {count} padres de familia.', 'success')

            # -------------------------------------------------------------
            # MASIVO POR CURSO
            # -------------------------------------------------------------
            elif modo_envio == 'masivo_curso':
                curso = request.form.get('curso_destino', '')
                if not curso:
                    flash('❌ Seleccione un curso', 'danger')
                    return redirect(url_for('chat.enviar'))
                
                estudiantes = Estudiante.query.filter_by(curso=curso, estado='Activo').all()
                count = 0
                for est in estudiantes:
                    padre = Padre.query.filter_by(estudiante_id=est.id).first()
                    if padre and padre.nombres:
                        calificaciones = Calificacion.query.filter_by(estudiante_id=est.id).all()
                        materias = Materia.query.all()
                        
                        if tipo_mensaje == 'Boletín':
                            tiene_deuda = Pago.query.filter_by(estudiante_id=est.id, estado='Pendiente').first()
                            if tiene_deuda:
                                continue # FILTRO ANTI-MOROSOS
                                
                            pdf_bytes = generar_boletin_pdf(est, calificaciones, materias)
                            ruta_pdf = guardar_boletin_localmente(pdf_bytes, est.id, ahora_bolivia().year, est.rude)
                            
                            texto_limpio = personalizar_texto_mensaje(contenido_base, est, padre, calificaciones, materias)
                            contenido_final = f"{texto_limpio}\n\n---ARCHIVO_ADJUNTO---{ruta_pdf}"
                            
                        else:
                            texto_limpio = personalizar_texto_mensaje(contenido_base, est, padre, calificaciones, materias)
                            if archivo_path_manual:
                                contenido_final = f"{texto_limpio}\n\n---ARCHIVO_ADJUNTO---{archivo_path_manual}"
                            else:
                                contenido_final = texto_limpio

                        msg = Mensaje(
                            destinatario=padre.nombres,
                            estudiante_id=est.id,
                            telefono=padre.telefono1 or 'Sin teléfono',
                            tipo_mensaje=tipo_mensaje,
                            contenido=contenido_final,
                            remitente='Colegio'
                        )
                        db.session.add(msg)
                        count += 1
                db.session.commit()
                flash(f'✅ Mensaje enviado a {count} padres del curso {curso}.', 'success')

            # -------------------------------------------------------------
            # MASIVO MOROSOS (Mantiene lógica original, sin PDF)
            # -------------------------------------------------------------
            elif modo_envio == 'masivo_morosos':
                pagos_pendientes = Pago.query.filter_by(estado='Pendiente').all()
                estudiante_ids = list(set(p.estudiante_id for p in pagos_pendientes))
                count = 0
                for est_id in estudiante_ids:
                    padre = Padre.query.filter_by(estudiante_id=est_id).first()
                    if padre and padre.nombres:
                        est = Estudiante.query.get(est_id)
                        deuda = sum((p.monto_total - (p.descuento or 0)) for p in pagos_pendientes if p.estudiante_id == est_id)
                        meses = ', '.join(list(set(p.mes for p in pagos_pendientes if p.estudiante_id == est_id)))
                        
                        contenido_personalizado = (
                            f"COLEGIO DR. ANTONIO VACA DÍEZ\n"
                            f"Departamento de Administración\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"AVISO DE PAGO PENDIENTE\n\n"
                            f"Estimado/a Sr./Sra. {padre.nombres}:\n\n"
                            f"Le informamos que el/la estudiante {est.nombres} {est.apellidos} del curso {est.curso} presenta los siguientes pagos pendientes:\n\n"
                            f"Meses adeudados: {meses}\n"
                            f"Monto total pendiente: Bs. {deuda:.2f}\n"
                            f"Gestión: {ahora_bolivia().year}\n\n"
                            f"Le solicitamos regularizar su situación a la brevedad.\n\n"
                            f"Atentamente,\nDEPARTAMENTO DE ADMINISTRACIÓN"
                        )
                        
                        msg = Mensaje(
                            destinatario=padre.nombres,
                            estudiante_id=est_id,
                            telefono=padre.telefono1 or 'Sin teléfono',
                            tipo_mensaje='Recordatorio de Pago',
                            contenido=contenido_personalizado,
                            remitente='Colegio'
                        )
                        db.session.add(msg)
                        count += 1
                db.session.commit()
                flash(f'✅ Recordatorio de pago enviado a {count} padres morosos.', 'success')

            # -------------------------------------------------------------
            # ENVÍO INDIVIDUAL
            # -------------------------------------------------------------
            else:
                estudiante_id = request.form.get('estudiante_id', '')
                if not estudiante_id:
                    flash('❌ Seleccione un estudiante', 'danger')
                    return redirect(url_for('chat.enviar'))
                
                est = Estudiante.query.get(int(estudiante_id))
                padre = Padre.query.filter_by(estudiante_id=int(estudiante_id)).first() if est else None
                
                if est:
                    calificaciones = Calificacion.query.filter_by(estudiante_id=est.id).all()
                    materias = Materia.query.all()
                    
                    if tipo_mensaje == 'Boletín':
                        pdf_bytes = generar_boletin_pdf(est, calificaciones, materias)
                        ruta_pdf = guardar_boletin_localmente(pdf_bytes, est.id, ahora_bolivia().year, est.rude)
                        texto_limpio = personalizar_texto_mensaje(contenido_base, est, padre, calificaciones, materias)
                        contenido_final = f"{texto_limpio}\n\n---ARCHIVO_ADJUNTO---{ruta_pdf}"
                    else:
                        texto_limpio = personalizar_texto_mensaje(contenido_base, est, padre, calificaciones, materias)
                        if archivo_path_manual:
                            contenido_final = f"{texto_limpio}\n\n---ARCHIVO_ADJUNTO---{archivo_path_manual}"
                        else:
                            contenido_final = texto_limpio
                else:
                    contenido_final = contenido_base
                
                msg = Mensaje(
                    destinatario=padre.nombres if padre else 'Padre de Familia',
                    estudiante_id=int(estudiante_id) if estudiante_id else None,
                    telefono=padre.telefono1 if padre else 'Sin teléfono',
                    tipo_mensaje=tipo_mensaje,
                    contenido=contenido_final,
                    remitente='Colegio'
                )
                db.session.add(msg)
                db.session.commit()
                flash('✅ Mensaje enviado correctamente.', 'success')

            return redirect(url_for('chat.index'))

        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
            flash(f'❌ Error al enviar: {str(e)}', 'danger')

    estudiantes = Estudiante.query.filter_by(estado='Activo').order_by(Estudiante.apellidos).all()
    cursos = db.session.query(Estudiante.curso).filter_by(estado='Activo').distinct().order_by(Estudiante.curso).all()
    cursos = [c[0] for c in cursos]
    
    return render_template('chat/enviar.html',
                         estudiantes=estudiantes,
                         cursos=cursos,
                         plantillas=PLANTILLAS)

# =========================================================================
# ENVIAR MENSAJE RÁPIDO DESDE VENTANA DE CHAT (conversacion.html)
# =========================================================================
@chat_bp.route('/enviar_mensaje/<int:estudiante_id>', methods=['POST'])
def enviar_mensaje(estudiante_id):
    try:
        estudiante = Estudiante.query.get_or_404(estudiante_id)
        padre = Padre.query.filter_by(estudiante_id=estudiante_id).first()
        contenido_base = request.form.get('contenido', '').strip()
        
        archivo_path_manual = None
        if 'archivo' in request.files:
            file = request.files['archivo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"chat_{int(datetime.now().timestamp())}_{file.filename}")
                upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'chat')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                archivo_path_manual = f"/static/uploads/chat/{filename}"
        
        # Limpieza rápida por si enviaron texto de plantilla sin editar
        texto_limpio = personalizar_texto_mensaje(contenido_base, estudiante, padre)
        
        if archivo_path_manual:
            contenido_final = f"{texto_limpio}\n\n---ARCHIVO_ADJUNTO---{archivo_path_manual}"
        else:
            contenido_final = texto_limpio
            
        msg = Mensaje(
            destinatario=padre.nombres if padre else 'Padre de Familia',
            estudiante_id=estudiante.id,
            telefono=padre.telefono1 if padre else 'Sin teléfono',
            tipo_mensaje='General',
            contenido=contenido_final,
            remitente='Colegio'
        )
        db.session.add(msg)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error al enviar mensaje: {e}', 'danger')
        
    return redirect(url_for('chat.conversacion', estudiante_id=estudiante_id))

# =========================================================================
# API: OBTENER DATOS DEL ESTUDIANTE PARA PLANTILLA (CON NOTAS Y DEUDAS)
# =========================================================================
@chat_bp.route('/api/datos_estudiante/<int:id>')
def api_datos_estudiante(id):
    est = Estudiante.query.get(id)
    if not est:
        return jsonify({'error': 'Estudiante no encontrado'}), 404
    
    padre = Padre.query.filter_by(estudiante_id=id).first()
    
    # Obtener deuda si existe
    pagos_pendientes = Pago.query.filter_by(estudiante_id=id, estado='Pendiente').all()
    deuda = sum((p.monto_total - (p.descuento or 0)) for p in pagos_pendientes)
    meses_pendientes = ', '.join(list(set(p.mes for p in pagos_pendientes)))
    
    # Obtener calificaciones para boletín
    calificaciones = Calificacion.query.filter_by(estudiante_id=id).all()
    materias = Materia.query.all()
    
    promedio = 0
    materias_aprobadas = 0
    materias_reprobadas = 0
    mejor_materia = 'N/A'
    nota_mejor = 0
    
    if calificaciones:
        notas_por_materia = {}
        for cal in calificaciones:
            if cal.materia_id not in notas_por_materia:
                notas_por_materia[cal.materia_id] = []
            notas_por_materia[cal.materia_id].append(cal.nota)
        
        promedios = []
        for mat_id, notas in notas_por_materia.items():
            prom_mat = sum(notas) / len(notas)
            promedios.append(prom_mat)
            if prom_mat >= 51:
                materias_aprobadas += 1
            else:
                materias_reprobadas += 1
            
            if prom_mat > nota_mejor:
                nota_mejor = prom_mat
                materia_obj = Materia.query.get(mat_id)
                mejor_materia = materia_obj.nombre if materia_obj else 'N/A'
        
        promedio = sum(promedios) / len(promedios) if promedios else 0
    
    return jsonify({
        'tutor': padre.nombres if padre else 'Padre de Familia',
        'estudiante': f"{est.nombres} {est.apellidos}",
        'curso': est.curso,
        'telefono': padre.telefono1 if padre else '',
        'mes': meses_pendientes or 'N/A',
        'monto': f"{deuda:.2f}" if deuda > 0 else '0.00',
        'fecha': ahora_bolivia().strftime('%d/%m/%Y'),
        'hora': ahora_bolivia().strftime('%H:%M'),
        'gestion': ahora_bolivia().year,
        'promedio': f"{promedio:.2f}",
        'materias_aprobadas': materias_aprobadas,
        'materias_reprobadas': materias_reprobadas,
        'mejor_materia': mejor_materia,
        'nota_mejor': f"{nota_mejor:.2f}"
    })
# ==============================================================================
# DESCARGAR ARCHIVO ADJUNTO DE UN MENSAJE DEL CHAT
# ==============================================================================

@chat_bp.route('/adjunto/<int:mensaje_id>/descargar')
def descargar_adjunto(mensaje_id):
    mensaje = Mensaje.query.get_or_404(mensaje_id)

    ruta_adjunto, _ = extraer_adjunto(mensaje.contenido)

    if not ruta_adjunto:
        flash('❌ Este mensaje no tiene archivo adjunto.', 'warning')
        return redirect(url_for('chat.index'))

    filepath = ruta_local_segura(ruta_adjunto)

    if not filepath:
        flash('❌ El archivo adjunto no existe en el servidor.', 'danger')
        return redirect(url_for('chat.index'))

    nombre_archivo = os.path.basename(filepath)

    if nombre_archivo.lower().endswith('.pdf'):
        mimetype = 'application/pdf'
    else:
        mimetype = 'application/octet-stream'

    return send_file(
        filepath,
        mimetype=mimetype,
        as_attachment=True,
        download_name=nombre_archivo
    )
# =========================================================================
# ELIMINAR MENSAJE
# =========================================================================
@chat_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    try:
        mensaje = Mensaje.query.get_or_404(id)
        db.session.delete(mensaje)
        db.session.commit()
        flash('✅ Mensaje eliminado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error: {str(e)}', 'danger')
    return redirect(url_for('chat.index'))

# =========================================================================
# CONVERSACIÓN CON ESTUDIANTE
# =========================================================================
@chat_bp.route('/conversacion/<int:estudiante_id>')
def conversacion(estudiante_id):
    estudiante = Estudiante.query.get_or_404(estudiante_id)
    padre = Padre.query.filter_by(estudiante_id=estudiante_id).first()
    mensajes = Mensaje.query.filter_by(estudiante_id=estudiante_id).order_by(Mensaje.fecha_envio.asc()).all()
    return render_template('chat/conversacion.html', estudiante=estudiante, padre=padre, mensajes=mensajes)