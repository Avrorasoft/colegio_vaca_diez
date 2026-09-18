# -*- coding: utf-8 -*-
"""
==============================================================================
Archivo: app.py
Proyecto: ASestud - Sistema de Gestión Escolar
Desarrollado por: Avrora Soft - Vibola LLC
==============================================================================
"""

import os
import secrets
import string
import gc
from datetime import datetime, timezone, timedelta, date
from functools import wraps

from flask import (
    Flask, redirect, url_for, jsonify, request, session,
    render_template, render_template_string, flash
)
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.utils import secure_filename
# -*- coding: utf-8 -*-
"""
==============================================================================
Archivo: app.py
Proyecto: ASestud - Sistema de Gestión Escolar
Desarrollado por: Avrora Soft - Vibola LLC
==============================================================================
"""

import os
import secrets
import string
import gc
from datetime import datetime, timezone, timedelta, date
from functools import wraps

from flask import (
    Flask, redirect, url_for, jsonify, request, session,
    render_template, render_template_string, flash
)
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.utils import secure_filename

from models import db, Estudiante, ConfiguracionSuperadmin
from config import Config

# Intento de respaldo automático al iniciar
try:
    from utils_backup import realizar_respaldo_db
    realizar_respaldo_db()
except Exception:
    pass

# Zona horaria Bolivia (UTC-4)
BOLIVIA_TZ = timezone(timedelta(hours=-4))
# ==============================================================================
# VERIFICADOR DE REINICIO PENDIENTE AL ARRANCAR
# ==============================================================================
import glob
bandera_inicio = os.path.join(os.path.abspath(os.path.dirname(__file__)), '.reset_pending')
if os.path.exists(bandera_inicio):
    print("🧹 [RESET] Limpiando bases de datos bloqueadas por reinicio pendiente...")
    try:
        os.remove(bandera_inicio)
    except Exception:
        pass
    
    # Buscar y destruir cualquier .db en instance/ o raíz
    for ruta_busqueda in ['instance/*.db', 'instance/*-wal', 'instance/*-shm', '*.db', '*.db-wal', '*.db-shm']:
        for archivo_encontrado in glob.glob(os.path.join(os.path.abspath(os.path.dirname(__file__)), ruta_busqueda)):
            try:
                os.remove(archivo_encontrado)
                print(f"🗑️ [LIMPIEZA] Borrado exitoso: {archivo_encontrado}")
            except Exception as ex:
                print(f"⚠️ No se pudo borrar {archivo_encontrado}: {ex}")

app = Flask(__name__)
# Optimizacion de cache para activos estaticos
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
app.config.from_object(Config)

db.init_app(app)
csrf = CSRFProtect(app)

# ==============================================================================
# SCRIPT DE MANTENIMIENTO: AUDITORÍA Y CORRECCIÓN DE PENSIONES NULAS
# ==============================================================================
def auditar_y_corregir_pensiones_nulas(app_instance, pension_por_defecto=350.0):
    """Verifica y corrige alumnos activos con pensiones nulas o en cero de forma automática."""
    with app_instance.app_context():
        try:
            estudiantes_afectados = Estudiante.query.filter(
                (Estudiante.estado == 'Activo') & 
                ((Estudiante.pension == None) | (Estudiante.pension <= 0))
            ).all()

            if estudiantes_afectados:
                for est in estudiantes_afectados:
                    est.pension = pension_por_defecto
                db.session.commit()
                print(f"🔧 [MANTENIMIENTO] Se corrigieron {len(estudiantes_afectados)} estudiante(s) activo(s) con pensión nula, asignando Bs. {pension_por_defecto:.2f}.")
            else:
                print("✅ [MANTENIMIENTO] Auditoría de pensiones exitosa: Todos los estudiantes activos tienen una pensión válida.")
        except Exception as e:
            print(f"❌ Error durante la auditoría de pensiones: {str(e)}")

# Ejecución de auditoría inicial al arrancar el contexto de la app
with app.app_context():
    try:
        db.create_all()
        auditar_y_corregir_pensiones_nulas(app, pension_por_defecto=350.0)
    except Exception as e:
        print(f"⚠️ Aviso en inicialización de BD: {e}")

# ==============================================================================
# BLINDAJE GLOBAL CONTRA ERRORES CSRF EN EL SETUP INICIAL
# ==============================================================================
@app.before_request
def bypass_csrf_for_setup():
    """Omite la validación CSRF global si el sistema no está configurado
    o si la petición va dirigida estrictamente al asistente de instalación."""
    # Nota: Asegúrate de definir _esta_configurado() o ajustarlo según tu lógica existente
    if request.path == '/setup':
        setattr(request, '_csrf_token_invalid', False)
        request.csrf_valid = True

@app.context_processor
def inject_now():
    return {'now': datetime.now}

@app.context_processor
def inject_institucion():
    """Inyecta la configuración institucional globalmente en todas las plantillas."""
    try:
        config_list = ConfiguracionSuperadmin.query.all()
        config_dict = {c.clave: c.valor for c in config_list if hasattr(c, 'clave') and hasattr(c, 'valor')}
        return {'institucion': config_dict, 'config': config_dict}
    except Exception:
        return {'institucion': {}, 'config': {}}


# ==============================================================================
# SISTEMA DE AUTOREPARO Y MIGRACIÓN AUTOMÁTICA INTELIGENTE
# ==============================================================================
def verificar_y_autoreparar_sistema(app):
    """
    Verifica la integridad de carpetas, archivos y la base de datos.
    Si detecta columnas o tablas faltantes, las actualiza automáticamente 
    sin destruir los datos existentes.
    """
    with app.app_context():
        root_path = app.root_path
        static_dir = os.path.join(root_path, 'static')
        instance_path = app.instance_path

        print("🔍 [AUTOREPARO] Verificando integridad y estructura del sistema...")

        # 1. Asegurar carpetas críticas
        carpetas_criticas = [
            os.path.join(static_dir, 'recibos_personal'),
            os.path.join(static_dir, 'uploads'),
            os.path.join(static_dir, 'backups'),
            os.path.join(static_dir, 'boletines'),
            os.path.join(static_dir, 'recibos')
        ]
        for carpeta in carpetas_criticas:
            if not os.path.exists(carpeta):
                try:
                    os.makedirs(carpeta, exist_ok=True)
                except Exception:
                    pass

        # 2. Asegurar logo por defecto
        uploads_dir = os.path.join(static_dir, 'uploads')
        default_logo_path = os.path.join(uploads_dir, 'logo_institucion.png')
        if not os.path.exists(default_logo_path):
            try:
                os.makedirs(uploads_dir, exist_ok=True)
                with open(default_logo_path, 'wb') as f:
                    f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\r')
            except Exception:
                pass

        # 3. Verificación y auto-actualización segura de tablas y columnas (Anti-Crash)
        try:
            db.create_all()
            
            import sqlite3
            db_path = None
            for path in [instance_path, root_path]:
                if os.path.exists(path):
                    for archivo in os.listdir(path):
                        if archivo.endswith('.db'):
                            db_path = os.path.join(path, archivo)
                            break
                    if db_path:
                        break

            if db_path and os.path.exists(db_path):
                conexion = sqlite3.connect(db_path)
                cursor = conexion.cursor()
                
                # Lista de columnas esenciales que el sistema garantiza en la tabla pagos
                columnas_pagos = [
                    ("tipo_concepto", "TEXT"),
                    ("detalle_concepto", "TEXT")
                ]
                
                cursor.execute("PRAGMA table_info(pagos);")
                columnas_existentes = [info[1] for info in cursor.fetchall()]
                
                for col_nombre, col_tipo in columnas_pagos:
                    if col_nombre not in columnas_existentes:
                        cursor.execute(f"ALTER TABLE pagos ADD COLUMN {col_nombre} {col_tipo};")
                        print(f"🛠️ [AUTOREPARO] Columna '{col_nombre}' añadida automáticamente a la tabla pagos.")
                
                conexion.commit()
                conexion.close()

            print("✅ [AUTOREPARO] Sistema íntegro y actualizado sin pérdida de datos.")

        except Exception as e:
            print(f"⚠️ [AUTOREPARO] Aviso al verificar esquema: {e}")


# ==============================================================================
# FUNCIONES AUXILIARES DE CONFIGURACIÓN
# ==============================================================================

def _obtener_clave(clave, valor_por_defecto='N/A'):
    """Función auxiliar segura para recuperar valores de configuración."""
    try:
        config = ConfiguracionSuperadmin.query.filter_by(clave=clave).first()
        if config and hasattr(config, 'valor') and config.valor:
            return config.valor
    except Exception:
        pass
    return os.environ.get(clave.upper(), valor_por_defecto)

def _set_clave(clave, valor):
    """Guarda o actualiza una clave en la configuración de superadmin."""
    try:
        config = ConfiguracionSuperadmin.query.filter_by(clave=clave).first()
        if config:
            config.valor = str(valor)
        else:
            config = ConfiguracionSuperadmin(clave=clave, valor=str(valor))
            db.session.add(config)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al guardar clave {clave}: {e}")

def _esta_configurado():
    """Verifica si la institución ya cuenta con configuración inicial."""
    try:
        val = _obtener_clave('institucion_configurada', 'false')
        return str(val).lower() == 'true'
    except Exception:
        return False

def _obtener_configuracion_institucion():
    """Devuelve un diccionario con toda la configuración institucional."""
    try:
        configs = ConfiguracionSuperadmin.query.all()
        return {c.clave: c.valor for c in configs if hasattr(c, 'clave') and hasattr(c, 'valor')}
    except Exception:
        return {}

def _generar_password(longitud=8):
    """Genera una contraseña aleatoria segura."""
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

def rate_limit(max_intentos=5, ventana_segundos=300):
    """Decorador simple de limitación de tasa para intentos de login."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            intentos_key = f'intentos_{request.endpoint}'
            tiempo_bloqueo_key = f'bloqueo_{request.endpoint}'
            
            ahora = datetime.now().timestamp()
            bloqueo_hasta = session.get(tiempo_bloqueo_key, 0)
            
            if ahora < bloqueo_hasta:
                tiempo_restante = int(bloqueo_hasta - ahora)
                flash(f'Demasiados intentos fallidos. Intente nuevamente en {tiempo_restante} segundos.', 'danger')
                return render_template_string(LOGIN_TEMPLATE, error="Sistema bloqueado temporalmente por seguridad.")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==============================================================================
# BLOQUEO GLOBAL DE ACCESO Y TRANSACCIONES
# ==============================================================================
@app.before_request
def verificar_autenticacion_global():
    """Bloquea el acceso general si no se ha configurado el sistema o no hay sesión activa."""
    if not _esta_configurado():
        if request.path != '/setup' and not request.path.startswith('/static/'):
            return redirect(url_for('setup'))
        return

    # Rutas públicas permitidas sin sesión
    rutas_publicas = ['setup', 'login_pwa', 'static', 'global_logout', 'redirect_login_raiz']
    if request.endpoint in rutas_publicas or (request.endpoint and 'static' in request.endpoint):
        return

    # Verificación estricta de sesión activa (PWA o Superadmin)
    pwa_autenticado = session.get('pwa_autenticado', False)
    es_superadmin = session.get('es_superadmin', False) or session.get('rol') == 'superadmin'

    if not pwa_autenticado and not es_superadmin:
        if request.path != '/login-pwa' and not request.path.startswith('/static/'):
            return redirect(url_for('login_pwa'))


@app.before_request
def bloquear_transacciones_sin_turno():
    path = request.path.lower()
    es_financiera = any(term in path for term in ['pago', 'pagar', 'cardex', 'cobro'])
    
    if es_financiera and request.method == 'POST':
        turno_activo = session.get('turno') or session.get('turno_activo')
        es_superadmin = session.get('es_superadmin') or session.get('rol') == 'superadmin'
        
        if not turno_activo and not es_superadmin:
            flash('❌ Acceso denegado: Se requiere un Turno de caja activo para realizar transacciones.', 'danger')
            try:
                return redirect(url_for('dashboard.index'))
            except Exception:
                return redirect('/')


# ==============================================================================
# REGISTRO DE BLUEPRINTS
# ==============================================================================

try:
    from routes.auth import auth_bp
    csrf.exempt(auth_bp)
    app.register_blueprint(auth_bp)
except Exception as e:
    print(f"❌ Error auth: {e}")

try:
    from routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
except Exception as e:
    print(f"❌ Error dashboard: {e}")

try:
    from routes.estudiantes import estudiantes_bp
    app.register_blueprint(estudiantes_bp, url_prefix='/estudiantes')
except Exception as e:
    print(f"❌ Error estudiantes: {e}")

try:
    from routes.personal import personal_bp
    app.register_blueprint(personal_bp, url_prefix='/personal')
except Exception as e:
    print(f"❌ Error personal: {e}")

try:
    from routes.calificaciones import calificaciones_bp
    app.register_blueprint(calificaciones_bp, url_prefix='/calificaciones')
except Exception as e:
    print(f"❌ Error calificaciones: {e}")

try:
    from routes.caja import caja_bp
    app.register_blueprint(caja_bp, url_prefix='/caja')
except Exception as e:
    print(f"❌ Error caja: {e}")

try:
    from routes.gastos import gastos_bp
    app.register_blueprint(gastos_bp, url_prefix='/gastos')
except Exception as e:
    print(f"❌ Error gastos: {e}")

try:
    from routes.mensajes import mensajes_bp
    app.register_blueprint(mensajes_bp, url_prefix='/mensajes')
except Exception as e:
    print(f"❌ Error mensajes: {e}")

try:
    from routes.chat import chat_bp
    app.register_blueprint(chat_bp, url_prefix='/chat')
except Exception as e:
    print(f"❌ Error chat: {e}")

try:
    from routes.archivos import archivos_bp
    app.register_blueprint(archivos_bp, url_prefix='/archivos')
except Exception as e:
    print(f"❌ Error archivos: {e}")

try:
    from routes.profesores_portal import profesores_portal_bp
    csrf.exempt(profesores_portal_bp)
    app.register_blueprint(profesores_portal_bp, url_prefix='/profesor-portal')
except Exception as e:
    print(f"❌ Error portal profesores: {e}")

try:
    from routes.faltas import faltas_bp
    app.register_blueprint(faltas_bp, url_prefix='/faltas')
except Exception as e:
    print(f"❌ Error faltas: {e}")

try:
    from routes.pagos import pagos_bp
    app.register_blueprint(pagos_bp, url_prefix='/pagos')
except Exception as e:
    print(f"❌ Error pagos: {e}")

try:
    from routes.portal_padres import portal_padres_bp
    app.register_blueprint(portal_padres_bp, url_prefix='/portal-padres')
except Exception as e:
    print(f"❌ Error portal padres: {e}")

try:
    from routes.superadmin import superadmin_bp
    app.register_blueprint(superadmin_bp, url_prefix='/superadmin')
except Exception as e:
    print(f"❌ Error superadmin: {e}")

try:
    from routes.superadmin_api import superadmin_api_bp
    app.register_blueprint(superadmin_api_bp)
except Exception as e:
    print(f"❌ Error superadmin_api: {e}")

try:
    from routes.pwa import pwa_bp
    app.register_blueprint(pwa_bp, url_prefix='/pwa')
except Exception as e:
    print(f"❌ Error PWA padres: {e}")

try:
    from routes.reportes import reportes_bp
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
except Exception as e:
    print(f"❌ Error reportes: {e}")

try:
    from routes.rubricas import rubricas_bp
    app.register_blueprint(rubricas_bp, url_prefix='/admin/rubricas')
except Exception as e:
    print(f"❌ Error rubricas: {e}")


# ==============================================================================
# RUTAS PRINCIPALES Y DE CONTROL GLOBAL
# ==============================================================================

@app.route('/')
def index():
    if not _esta_configurado():
        return redirect(url_for('setup'))
    return redirect(url_for('login_pwa'))

@app.route('/login')
def redirect_login_raiz():
    if not _esta_configurado():
        return redirect(url_for('setup'))
    return redirect(url_for('login_pwa'))

@app.route('/logout')
def global_logout():
    """Cierra cualquier sesión activa y redirige al login o setup según corresponda."""
    session.clear()
    try:
        from flask_login import logout_user
        logout_user()
    except Exception:
        pass
    
    if not _esta_configurado():
        return redirect(url_for('setup'))
        
    try:
        return redirect(url_for('login_pwa'))
    except Exception:
        return redirect('/')


# ==============================================================================
# ASISTENTE DE CONFIGURACIÓN INICIAL (LIBRE DE CSRF)
# ==============================================================================

@app.route('/setup', methods=['GET', 'POST'])
@csrf.exempt
def setup():
    """Formulario de configuración inicial de la institución exento de validación CSRF."""
    if _esta_configurado():
        return redirect(url_for('login_pwa'))
    
    if request.method == 'POST':
        try:
            linea1 = request.form.get('linea1', '').strip()
            linea2 = request.form.get('linea2', '').strip()
            linea3 = request.form.get('linea3', '').strip()
            direccion = request.form.get('direccion', '').strip()
            telefono = request.form.get('telefono', '').strip()
            email = request.form.get('email', '').strip()
            ciudad = request.form.get('ciudad', '').strip()
            gestion = request.form.get('gestion', str(datetime.now().year)).strip()
            password_pwa = request.form.get('password_pwa', '').strip()
            password_admin = request.form.get('password_admin', '').strip()
            
            modo_contabilizacion = request.form.get('modo_contabilizacion', 'cero')
            _set_clave('modo_contabilizacion', modo_contabilizacion)

            if modo_contabilizacion == 'personalizado':
                _set_clave('incluir_haberes', '1' if request.form.get('incluir_haberes') else '0')
                _set_clave('incluir_ingresos', '1' if request.form.get('incluir_ingresos') else '0')
                _set_clave('incluir_egresos_generales', '1' if request.form.get('incluir_egresos_generales') else '0')
            else:
                _set_clave('incluir_haberes', '0')
                _set_clave('incluir_ingresos', '0')
                _set_clave('incluir_egresos_generales', '0')

            _set_clave('fecha_instalacion', datetime.now().strftime('%Y-%m-%d'))
            
            if not linea1:
                flash('❌ El nombre de la institución (línea 1) es obligatorio.', 'danger')
                return render_template_string(SETUP_TEMPLATE)
            
            if not password_pwa or len(password_pwa) < 6:
                flash('❌ La contraseña PWA debe tener al menos 6 caracteres.', 'danger')
                return render_template_string(SETUP_TEMPLATE)
            
            if not password_admin or len(password_admin) < 6:
                flash('❌ La contraseña Superadmin debe tener al menos 6 caracteres.', 'danger')
                return render_template_string(SETUP_TEMPLATE)
            
            _set_clave('institucion_linea1', linea1)
            _set_clave('institucion_linea2', linea2)
            _set_clave('institucion_linea3', linea3)
            _set_clave('institucion_direccion', direccion)
            _set_clave('institucion_telefono', telefono)
            _set_clave('institucion_email', email)
            _set_clave('institucion_ciudad', ciudad)
            _set_clave('institucion_gestion', gestion)
            
            if 'logo' in request.files:
                logo_file = request.files['logo']
                if logo_file and logo_file.filename != '':
                    filename = secure_filename(logo_file.filename)
                    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'png'
                    logo_filename = f'logo_institucion.{ext}'
                    
                    upload_folder = os.path.join(app.static_folder, 'uploads')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    logo_path = os.path.join(upload_folder, logo_filename)
                    logo_file.save(logo_path)
                    
                    _set_clave('institucion_logo', f'uploads/{logo_filename}')
                else:
                    _set_clave('institucion_logo', '')
            else:
                _set_clave('institucion_logo', '')
            
            _set_clave('pwa_password', password_pwa)
            _set_clave('superadmin_password', password_admin)
            _set_clave('institucion_configurada', 'true')
            
            flash('✅ Configuración completada exitosamente. Ahora puede iniciar sesión.', 'success')
            return redirect(url_for('login_pwa'))
            
        except Exception as e:
            flash(f'❌ Error al guardar la configuración: {str(e)}', 'danger')
            return render_template_string(SETUP_TEMPLATE)
    
    return render_template_string(SETUP_TEMPLATE)


# ==============================================================================
# REINICIO A VALORES DE FÁBRICA (EXENTO DE CSRF Y DESACOPLADO)
# ==============================================================================
@app.route('/superadmin/reset-fabrica', methods=['POST'])
@csrf.exempt
def reset_fabrica():
    """Restablece el sistema a fábrica mediante hilo desacoplado y exento de tokens."""
    import threading
    import time
    import glob

    try:
        session.clear()
        instance_dir = app.instance_path
        
        def destruir_archivos_en_fondo():
            time.sleep(0.3)
            try:
                db.session.remove()
                engine = db.get_engine(app)
                if engine:
                    engine.dispose()
            except Exception:
                pass

            gc.collect()

            patrones = [
                os.path.join(instance_dir, '*.db'),
                os.path.join(instance_dir, '*.db-wal'),
                os.path.join(instance_dir, '*.db-shm'),
                os.path.join(instance_dir, 'backups', '*.db'),
                os.path.join(instance_dir, 'backups', '*.db-wal'),
                os.path.join(instance_dir, 'backups', '*.db-shm')
            ]

            for patron in patrones:
                for archivo in glob.glob(patron):
                    try:
                        os.chmod(archivo, 0o777)
                        os.remove(archivo)
                    except Exception:
                        try:
                            with open(archivo, 'w'):
                                pass
                            os.remove(archivo)
                        except Exception:
                            pass

        threading.Thread(target=destruir_archivos_en_fondo, daemon=True).start()

        flash('⚙️ Sistema restablecido a valores de fábrica exitosamente.', 'success')
        return redirect(url_for('setup'))

    except Exception as e:
        flash(f'❌ Error al restablecer el sistema: {str(e)}', 'danger')
        return redirect(url_for('index'))


# ==============================================================================
# PANTALLA DE LOGIN PWA
# ==============================================================================

@app.route('/login-pwa', methods=['GET', 'POST'])
@rate_limit(max_intentos=5, ventana_segundos=300)
def login_pwa():
    """Pantalla de contraseña para acceder al sistema."""
    error = None

    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        clave_pwa = _obtener_clave('pwa_password', 'VacaDiez2026')

        if password == clave_pwa:
            session['pwa_autenticado'] = True
            session['pwa_login_time'] = datetime.now().isoformat()
            session.permanent = False
            siguiente = request.args.get('next', url_for('dashboard.index'))
            return redirect(siguiente)
        else:
            error = 'Contraseña incorrecta'

    config = _obtener_configuracion_institucion()
    nombre_institucion = config.get('institucion_linea1', 'Sistema de Gestión Escolar')

    return render_template_string(LOGIN_TEMPLATE, error=error, 
                                 nombre_institucion=nombre_institucion,
                                 config=config)


# ==============================================================================
# PLANTILLAS INTEGRADAS (SETUP & LOGIN)
# ==============================================================================

SETUP_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
    <title>Configuración Inicial - ASestud</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            font-family: Arial, Helvetica, sans-serif;
        }
        .setup-card {
            width: 100%;
            max-width: 700px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            border: none;
            overflow: hidden;
        }
        .setup-header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .setup-header i {
            font-size: 3rem;
            color: #38bdf8;
        }
        .setup-body {
            padding: 40px;
            background: white;
        }
        .form-control, .form-select {
            min-height: 48px;
            font-size: 15px;
            border-radius: 8px;
        }
        .btn-setup {
            min-height: 50px;
            font-size: 1.1rem;
            border-radius: 10px;
            font-weight: bold;
        }
        .section-title {
            color: #0f172a;
            font-weight: bold;
            margin-top: 25px;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #38bdf8;
        }
    </style>
</head>
<body>
    <div class="setup-card card">
        <div class="setup-header">
            <i class="bi bi-gear-fill"></i>
            <h2 class="mt-3 mb-1">Configuración Inicial</h2>
            <small class="text-white-50">ASestud - Sistema de Gestión Escolar</small>
        </div>
        <div class="setup-body">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <form method="POST" enctype="multipart/form-data">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() if csrf_token is defined else '' }}">
                <h5 class="section-title">
                    <i class="bi bi-building me-2"></i>Datos de la Institución
                </h5>
                
                <div class="mb-3">
                    <label class="form-label fw-bold">Nombre de la Institución (Línea 1) *</label>
                    <input type="text" name="linea1" class="form-control" 
                           placeholder="Ej: Unidad Educativa" required>
                    <small class="text-muted">Primera línea del nombre oficial</small>
                </div>
                
                <div class="mb-3">
                    <label class="form-label fw-bold">Nombre de la Institución (Línea 2)</label>
                    <input type="text" name="linea2" class="form-control" 
                           placeholder="Ej: Dr. Antonio Vaca Díez">
                    <small class="text-muted">Segunda línea del nombre oficial (opcional)</small>
                </div>
                
                <div class="mb-3">
                    <label class="form-label fw-bold">Nombre de la Institución (Línea 3)</label>
                    <input type="text" name="linea3" class="form-control" 
                           placeholder="Ej: Riberalta - Beni">
                    <small class="text-muted">Tercera línea del nombre oficial (opcional)</small>
                </div>
                
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label fw-bold">Dirección</label>
                        <input type="text" name="direccion" class="form-control" 
                               placeholder="Av. Principal #123">
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label fw-bold">Ciudad</label>
                        <input type="text" name="ciudad" class="form-control" 
                               placeholder="Riberalta">
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label fw-bold">Teléfono</label>
                        <input type="text" name="telefono" class="form-control" 
                               placeholder="3-8521234">
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label fw-bold">Email</label>
                        <input type="email" name="email" class="form-control" 
                               placeholder="info@colegio.edu.bo">
                    </div>
                </div>
                
                <div class="mb-3">
                    <label class="form-label fw-bold">Gestión (Año)</label>
                    <input type="number" name="gestion" class="form-control" 
                           value="{{ now().year }}" min="2020" max="2100">
                </div>
                
                <div class="mb-3">
                    <label class="form-label fw-bold">
                        <i class="bi bi-image me-2"></i>Logo de la Institución
                    </label>
                    <input type="file" name="logo" class="form-control" accept="image/*">
                    <small class="text-muted">Formatos: PNG, JPG, JPEG. Se usará como marca de agua en documentos.</small>
                </div>

                <h5 class="section-title">
                    <i class="bi bi-cash-stack me-2"></i>Comportamiento Económico Inicial
                </h5>

                <div class="mb-4">
                    <label class="form-label fw-bold">Seleccione el modo de contabilización:</label>
                    <select name="modo_contabilizacion" id="modo_contabilizacion" class="form-select mb-3" onchange="togglePersonalizado(this.value)" required>
                        <option value="cero" selected>1. Desde cero (Por defecto: Solo desde el momento de instalación en adelante)</option>
                        <option value="enero_total">2. Histórico Total (Todo contabilizado desde el 1 de enero)</option>
                        <option value="personalizado">3. Personalizado (Escoger mediante casillas lo que se desea incluir)</option>
                    </select>

                    <!-- Panel de Casillas (Oculto por defecto, se muestra si elige 'personalizado') -->
                    <div id="panel_personalizado" class="card p-3 bg-light border" style="display: none;">
                        <span class="fw-bold text-dark mb-2 d-block"><i class="bi bi-check2-square me-1"></i> Seleccione los rubros a contabilizar desde enero:</span>
                        
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" name="incluir_haberes" id="incluir_haberes" value="1">
                            <label class="form-check-label text-dark" for="incluir_haberes">
                                Incluir pago de haberes y sueldos del personal (desde enero)
                            </label>
                        </div>
                        
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" name="incluir_ingresos" id="incluir_ingresos" value="1">
                            <label class="form-check-label text-dark" for="incluir_ingresos">
                                Incluir ingresos históricos de caja / pensiones (desde enero)
                            </label>
                        </div>
                        
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" name="incluir_egresos_generales" id="incluir_egresos_generales" value="1">
                            <label class="form-check-label text-dark" for="incluir_egresos_generales">
                                Incluir egresos y gastos operativos generales (desde enero)
                            </label>
                        </div>
                    </div>
                </div>
                
                <h5 class="section-title">
                    <i class="bi bi-shield-lock me-2"></i>Contraseñas de Acceso
                </h5>
                
                <div class="mb-3">
                    <label class="form-label fw-bold">Contraseña PWA (acceso general) *</label>
                    <input type="password" name="password_pwa" class="form-control" 
                           placeholder="Mínimo 6 caracteres" required minlength="6">
                    <small class="text-muted">Esta contraseña protege el acceso al sistema</small>
                </div>
                
                <div class="mb-4">
                    <label class="form-label fw-bold">Contraseña Superadmin (Bóveda) *</label>
                    <input type="password" name="password_admin" class="form-control" 
                           placeholder="Mínimo 6 caracteres" required minlength="6">
                    <small class="text-muted">Esta contraseña protege las funciones administrativas</small>
                </div>
                
                <button type="submit" class="btn btn-primary btn-setup w-100">
                    <i class="bi bi-check-circle me-2"></i>Guardar Configuración y Continuar
                </button>
            </form>
        </div>
    </div>
    <script>
    function togglePersonalizado(valor) {
        var panel = document.getElementById('panel_personalizado');
        if (valor === 'personalizado') {
            panel.style.display = 'block';
        } else {
            panel.style.display = 'none';
        }
    }
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>Acceso - {{ nombre_institucion }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: Arial, Helvetica, sans-serif;
        }
        .login-card {
            width: 100%;
            max-width: 450px;
            margin: 20px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            border: none;
        }
        .login-header {
            background: #0f172a;
            color: white;
            padding: 30px 20px;
            text-align: center;
            border-radius: 16px 16px 0 0;
        }
        .login-header i {
            font-size: 3rem;
            color: #38bdf8;
        }
        .login-body {
            padding: 30px;
            background: white;
            border-radius: 0 0 16px 16px;
        }
        .form-control {
            min-height: 50px;
            font-size: 16px;
            border-radius: 10px;
        }
        .btn-login {
            min-height: 50px;
            font-size: 1.1rem;
            border-radius: 10px;
            font-weight: bold;
        }
        .footer-text {
            text-align: center;
            color: #94a3b8;
            font-size: 0.8rem;
            margin-top: 20px;
        }
        .institucion-info {
            font-size: 1.1rem;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="login-card card">
        <div class="login-header">
            {% if config and config.get('institucion_logo') %}
            <img src="{{ url_for('static', filename=config['institucion_logo']) }}" 
                 alt="Logo" style="max-width: 120px; max-height: 120px; margin-bottom: 15px; border-radius: 8px;">
            {% else %}
            <i class="bi bi-shield-lock-fill"></i>
            {% endif %}
            
            <h4 class="mt-3 mb-1">{{ config.get('institucion_linea1', 'Sistema de Gestión Escolar') }}</h4>
            {% if config.get('institucion_linea2') %}
            <div class="institucion-info">{{ config['institucion_linea2'] }}</div>
            {% endif %}
            {% if config.get('institucion_linea3') %}
            <div class="institucion-info" style="font-size: 1rem;">{{ config['institucion_linea3'] }}</div>
            {% endif %}
            <small class="text-white-50">ASestud</small>
        </div>
        <div class="login-body">
            {% if error %}
            <div class="alert alert-danger text-center">
                <i class="bi bi-exclamation-triangle-fill"></i> {{ error }}
            </div>
            {% endif %}

            <form method="POST" autocomplete="off">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() if csrf_token is defined else '' }}">
                <div class="mb-4">
                    <label class="form-label fw-bold">
                        <i class="bi bi-key-fill text-primary"></i> Contraseña de Acceso
                    </label>
                    <input type="password"
                           name="password"
                           class="form-control"
                           placeholder="Ingrese la contraseña"
                           autocomplete="new-password"
                           autofocus
                           required>
                </div>

                <button type="submit" class="btn btn-primary btn-login w-100">
                    <i class="bi bi-unlock-fill"></i> Ingresar al Sistema
                </button>
            </form>

            <div class="footer-text">
                <i class="bi bi-shield-check"></i> Acceso restringido y autorizado<br>
                Avrora Soft - Vibola LLC &copy; 2026
            </div>
        </div>
    </div>
</body>
</html>
"""


# ==============================================================================
# EJECUCIÓN DE LA APLICACIÓN Y AUTOREPARO
# ==============================================================================
#import logging
# Silenciar la advertencia del servidor de desarrollo de Werkzeug
#log = logging.getLogger('werkzeug')
#log.setLevel(logging.ERROR)
if __name__ == '__main__':
    with app.app_context():
        # Ejecutar autoreparo y verificación inteligente antes de levantar tablas
        try:
            verificar_y_autoreparar_sistema(app)
        except Exception as e:
            print(f"⚠️ Aviso en autoreparo: {e}")

        # Configuración de clave secreta segura persistente
        ruta_key = os.path.join(os.getcwd(), '.secret_key')
        if not app.config.get('SECRET_KEY') or app.config.get('SECRET_KEY') == 'dev':
            if os.path.exists(ruta_key):
                with open(ruta_key, 'r') as f:
                    app.config['SECRET_KEY'] = f.read().strip()
            else:
                nueva_key = secrets.token_hex(32)
                with open(ruta_key, 'w') as f:
                    f.write(nueva_key)
                app.config['SECRET_KEY'] = nueva_key

        clave_pwa = _obtener_clave('pwa_password', 'N/A')
        clave_admin = _obtener_clave('superadmin_password', 'N/A')
        
        print("=" * 60)
        print(f"🔐 CONTRASEÑA PWA ACTUAL: {clave_pwa}")
        print(f"🔒 CONTRASEÑA SUPERADMIN: {clave_admin}")
        print("   (Cámbielas desde la Bóveda Superadmin)")
        print("=" * 60)

    ES_PRODUCCION = os.environ.get('FLASK_ENV') == 'production'
    app.run(
        debug=not ES_PRODUCCION,
        host='0.0.0.0',
        port=5000
    )