# -*- coding: utf-8 -*-
"""
==============================================================================
Archivo: app.py
Proyecto: ASestud-Konetz - Sistema de Gestión Escolar
Basado en: Colegio Dr. Antonio Vaca Díez
Desarrollado por: Avrora Soft - Vibola LLC
==============================================================================
"""

import os
import secrets
import string
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
from routes.auth import auth_bp

# Zona horaria Bolivia (UTC-4)
BOLIVIA_TZ = timezone(timedelta(hours=-4))

app = Flask(__name__)
@app.context_processor
def inject_now():
    return {'now': datetime.now}
app.config.from_object(Config)

db.init_app(app)
csrf = CSRFProtect(app)

# ==============================================================================
# BLOQUEO GLOBAL DE TRANSACCIONES SIN TURNO ACTIVO
# ==============================================================================
@app.before_request
def bloquear_transacciones_sin_turno():
    path = request.path.lower()
    # Intercepta cualquier ruta que involucre pagos, cobros o cardex financieros
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

def _obtener_clave(clave, valor_por_defecto='N/A'):
    """Función auxiliar segura para recuperar valores de configuración."""
    try:
        config = ConfiguracionSuperadmin.query.filter_by(clave=clave).first()
        if config and hasattr(config, 'valor') and config.valor:
            return config.valor
    except Exception:
        pass
    return os.environ.get(clave.upper(), valor_por_defecto)


# ==============================================================================
# REGISTRO DE BLUEPRINTS
# ==============================================================================

try:
    from routes.auth import auth_bp
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

@app.route('/')
def index():
    return redirect(url_for('dashboard.index'))



# Alias de compatibilidad global: Redirige /login a /login-turno
@app.route('/login')
def redirect_login_raiz():
    from flask import redirect, url_for
    return redirect(url_for('auth.login_turno'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

    # ==============================================================================
    # SECRET_KEY segura y persistente
    # ==============================================================================
    if not app.config.get('SECRET_KEY') or app.config.get('SECRET_KEY') == 'dev':
        ruta_key = os.path.join(os.getcwd(), '.secret_key')
        if os.path.exists(ruta_key):
            with open(ruta_key, 'r') as f:
                app.config['SECRET_KEY'] = f.read().strip()
        else:
            nueva_key = secrets.token_hex(32)
            with open(ruta_key, 'w') as f:
                f.write(nueva_key)
            app.config['SECRET_KEY'] = nueva_key

    # ==============================================================================
    # BLOQUEO GLOBAL DE TRANSACCIONES SIN TURNO ACTIVO
    # ==============================================================================
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

    # =========================================================================
    # PROTECCIÓN CSRF GLOBAL
    # =========================================================================
    csrf = CSRFProtect(app)

    # =========================================================================
    # INICIALIZAR BASE DE DATOS Y CLAVES
    # =========================================================================
    db.init_app(app)

    with app.app_context():
        db.create_all()
        _obtener_clave('pwa_password', _generar_password())
        _obtener_clave('superadmin_password', 'ADMIN2026')

    # =========================================================================
    # PROTECCIÓN GLOBAL CON CONTRASEÑA + VERIFICACIÓN DE CONFIGURACIÓN
    # =========================================================================

    @app.before_request
    def proteger_acceso_global():
        """Protege TODA la aplicación con contraseña y verifica configuración."""
        rutas_excluidas = [
            'static',
            'login_pwa',
            'logout_pwa',
            'setup',  # ⭐ Ruta de configuración inicial
            'api_estudiantes_por_curso',
            'portal_padres.',
            'pwa.',
        ]

        endpoint = request.endpoint or ''

        for excluida in rutas_excluidas:
            if excluida in endpoint or request.path.startswith('/static'):
                return None

        # ⭐ VERIFICAR SI LA INSTITUCIÓN ESTÁ CONFIGURADA
        if not _esta_configurado():
            return redirect(url_for('setup'))

        if session.get('pwa_autenticado'):
            return None

        return redirect(url_for('login_pwa'))

    # =========================================================================
    # ASISTENTE DE CONFIGURACIÓN INICIAL
    # =========================================================================

    @app.route('/setup', methods=['GET', 'POST'])
    def setup():
        """Formulario de configuración inicial de la institución."""
        
        # Si ya está configurado, redirigir al login
        if _esta_configurado():
            return redirect(url_for('login_pwa'))
        
        if request.method == 'POST':
            try:
                # Obtener datos del formulario
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
                
                # Validaciones básicas
                if not linea1:
                    flash('❌ El nombre de la institución (línea 1) es obligatorio.', 'danger')
                    return render_template_string(SETUP_TEMPLATE)
                
                if not password_pwa or len(password_pwa) < 6:
                    flash('❌ La contraseña PWA debe tener al menos 6 caracteres.', 'danger')
                    return render_template_string(SETUP_TEMPLATE)
                
                if not password_admin or len(password_admin) < 6:
                    flash('❌ La contraseña Superadmin debe tener al menos 6 caracteres.', 'danger')
                    return render_template_string(SETUP_TEMPLATE)
                
                # Guardar configuración
                _set_clave('institucion_linea1', linea1)
                _set_clave('institucion_linea2', linea2)
                _set_clave('institucion_linea3', linea3)
                _set_clave('institucion_direccion', direccion)
                _set_clave('institucion_telefono', telefono)
                _set_clave('institucion_email', email)
                _set_clave('institucion_ciudad', ciudad)
                _set_clave('institucion_gestion', gestion)
                
                # Procesar logo si se subió
                if 'logo' in request.files:
                    logo_file = request.files['logo']
                    if logo_file and logo_file.filename != '':
                        filename = secure_filename(logo_file.filename)
                        # Guardar con nombre fijo para facilitar referencia
                        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'png'
                        logo_filename = f'logo_institucion.{ext}'
                        
                        # Crear carpeta si no existe
                        upload_folder = os.path.join(app.static_folder, 'uploads')
                        os.makedirs(upload_folder, exist_ok=True)
                        
                        logo_path = os.path.join(upload_folder, logo_filename)
                        logo_file.save(logo_path)
                        
                        _set_clave('institucion_logo', f'uploads/{logo_filename}')
                    else:
                        _set_clave('institucion_logo', '')
                else:
                    _set_clave('institucion_logo', '')
                
                # Guardar contraseñas
                _set_clave('pwa_password', password_pwa)
                _set_clave('superadmin_password', password_admin)
                
                # Marcar como configurado
                _set_clave('institucion_configurada', 'true')
                
                flash('✅ Configuración completada exitosamente. Ahora puede iniciar sesión.', 'success')
                return redirect(url_for('login_pwa'))
                
            except Exception as e:
                flash(f'❌ Error al guardar la configuración: {str(e)}', 'danger')
                return render_template_string(SETUP_TEMPLATE)
        
        return render_template_string(SETUP_TEMPLATE)

    # Eximir setup del CSRF (usa render_template_string)
    csrf.exempt(setup)

    # =========================================================================
    # PANTALLA DE LOGIN PWA
    # =========================================================================

    @app.route('/login', methods=['GET', 'POST'])
    @rate_limit(max_intentos=5, ventana_segundos=300)
    def login_pwa():
        """Pantalla de contraseña para acceder a la PWA."""
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

        # Obtener configuración para mostrar en el login
        config = _obtener_configuracion_institucion()
        nombre_institucion = config.get('institucion_linea1', 'Sistema de Gestión Escolar')

        return render_template_string(LOGIN_TEMPLATE, error=error, 
                                     nombre_institucion=nombre_institucion,
                                     config=config)

    @app.route('/logout')
    def logout_pwa():
        """Cierra la sesión de la PWA."""
        session.pop('pwa_autenticado', None)
        session.pop('pwa_login_time', None)
        return redirect(url_for('login_pwa'))

    # Eximir login del CSRF (usa render_template_string)
    csrf.exempt(login_pwa)

    

    # =========================================================================
    # EXENCIONES CSRF (rutas que usan render_template_string o base_padres)
    # =========================================================================

    # Superadmin
    try:
        csrf.exempt('superadmin.auth')
        csrf.exempt('superadmin.quick_login')
        csrf.exempt('superadmin.quick_logout')
        csrf.exempt('superadmin.informes_login')
        csrf.exempt('superadmin.informes_generar')
        csrf.exempt('superadmin.informes_cambiar_password')
        csrf.exempt('superadmin.informes_eliminar')
        csrf.exempt('superadmin.cambiar_password_pwa')
        csrf.exempt('superadmin.restaurar_avr')
        csrf.exempt('superadmin.reset_fabrica')
    except Exception:
        pass

    # Portal de padres
    try:
        csrf.exempt('portal_padres.login')
        csrf.exempt('portal_padres.nuevo_mensaje')
        csrf.exempt('portal_padres.responder_mensaje')
    except Exception:
        pass

    # Portal de profesores
    try:
        csrf.exempt('profesores_portal.login')
        csrf.exempt('profesores_portal.nueva_evaluacion')
        csrf.exempt('profesores_portal.eliminar_evaluacion')
        csrf.exempt('profesores_portal.guardar_notas')
    except Exception:
        pass
    except Exception:
        pass

    # =========================================================================
    # RUTA PRINCIPAL
    # =========================================================================

    @app.route('/')
    def index():
        try:
            return redirect(url_for('dashboard.index'))
        except Exception:
            return """
            <h1>ASestud-Konetz - Sistema funcionando</h1>
            <p>Ve a <a href='/dashboard/'>/dashboard/</a></p>
            """

    # =========================================================================
    # API PARA ESTUDIANTES POR CURSO
    # =========================================================================

    @app.route('/api/estudiantes_por_curso')
    def api_estudiantes_por_curso():
        curso = request.args.get('curso', '')
        query = Estudiante.query
        if curso and curso.lower() != 'todos':
            query = query.filter(Estudiante.curso.ilike(f"%{curso}%"))
        estudiantes = query.order_by(Estudiante.apellidos.asc()).all()
        resultado = [
            {'id': e.id, 'nombres': e.nombres, 'apellidos': e.apellidos}
            for e in estudiantes
        ]
        return jsonify(resultado)

    # =========================================================================
    # CONTEXT PROCESSOR
    # =========================================================================

    @app.context_processor
    def inject_now():
        # Inyectar configuración de la institución en todas las plantillas
        config = _obtener_configuracion_institucion()
        return {
            'now': lambda: datetime.now(BOLIVIA_TZ),
            'institucion': config
        }

    # =========================================================================
    # PÁGINAS DE ERROR
    # =========================================================================

    @app.errorhandler(404)
    def error_404(e):
        return render_template_string("""
        <!DOCTYPE html>
        <html><head><title>Error 404</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head><body class="bg-dark text-white d-flex align-items-center justify-content-center" style="min-height:100vh">
        <div class="text-center"><h1 class="display-1">404</h1>
        <p class="fs-4">Página no encontrada</p>
        <a href="/" class="btn btn-primary">Volver al inicio</a></div>
        </body></html>
        """), 404

    @app.errorhandler(500)
    def error_500(e):
        return render_template_string("""
        <!DOCTYPE html>
        <html><head><title>Error 500</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head><body class="bg-dark text-white d-flex align-items-center justify-content-center" style="min-height:100vh">
        <div class="text-center"><h1 class="display-1">500</h1>
        <p class="fs-4">Error interno del servidor. Contacte al administrador.</p>
        <a href="/" class="btn btn-primary">Volver al inicio</a></div>
        </body></html>
        """), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash('⚠️ Sesión expirada. Por favor recargue la página.', 'warning')
        return redirect(request.referrer or url_for('index'))

    # EXENCION MASIVA DE CSRF POR BLUEPRINT
    for endpoint, func in list(app.view_functions.items()):
        if not endpoint.startswith(('static', 'setup', 'login_pwa')):
            try:
                csrf.exempt(func)
            except Exception:
                pass

# ==============================================================================
# PLANTILLA DE CONFIGURACIÓN INICIAL
# ==============================================================================

SETUP_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
    <title>Configuración Inicial - Sistema de Gestión Escolar</title>
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
        .logo-preview {
            max-width: 150px;
            max-height: 150px;
            margin-top: 10px;
            border-radius: 8px;
            border: 2px solid #e2e8f0;
        }
    </style>
</head>
<body>
    <div class="setup-card card">
        <div class="setup-header">
            <i class="bi bi-gear-fill"></i>
            <h2 class="mt-3 mb-1">Configuración Inicial</h2>
            <small class="text-white-50">Configure los datos de su institución</small>
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
</body>
</html>
"""


# ==============================================================================
# PLANTILLA DE LOGIN PWA
# ==============================================================================

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
            <small class="text-white-50">Sistema de Gestión Escolar</small>
        </div>
        <div class="login-body">
            {% if error %}
            <div class="alert alert-danger text-center">
                <i class="bi bi-exclamation-triangle-fill"></i> {{ error }}
            </div>
            {% endif %}

            <form method="POST">
                <div class="mb-4">
                    <label class="form-label fw-bold">
                        <i class="bi bi-key-fill text-primary"></i> Contraseña de Acceso
                    </label>
                    <input type="password"
                           name="password"
                           class="form-control"
                           placeholder="Ingrese la contraseña"
                           autocomplete="off"
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



if __name__ == '__main__':
    app = create_app()

    with app.app_context():
        db.create_all()

        clave_pwa = _obtener_clave('pwa_password', 'N/A')
        clave_admin = _obtener_clave('superadmin_password', 'N/A')
        
        # ... resto del código ...

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




