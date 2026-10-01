# -*- coding: utf-8 -*-
"""
Monitor de Rescate y Restauración de Emergencia - ASestud-Konetz
Desarrollado por: Avrora Soft - Vibola LLC
"""

import os
import shutil
from flask import Flask, render_template_string, request, redirect

app_rescate = Flask("RescateEmergencia")

EMERGENCIA_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Monitor de Rescate - ASestud-Konetz</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
</head>
<body class="bg-dark text-light py-5">
    <div class="container" style="max-width: 650px;">
        <div class="card shadow-lg bg-secondary text-light border-warning">
            <div class="card-header bg-warning text-dark py-3">
                <h4 class="mb-0 fw-bold"><i class="bi bi-shield-exclamation me-2"></i>Monitor de Rescate y Emergencia</h4>
            </div>
            <div class="card-body p-4 bg-dark">
                <p class="text-light">Utilice esta consola independiente para restaurar el sistema a cualquier punto de respaldo anterior en caso de fallos críticos o incompatibilidades:</p>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for cat, msg in messages %}
                            <div class="alert alert-{{ cat }} py-2"><small>{{ msg }}</small></div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}

                <form action="/restaurar" method="POST" onsubmit="return confirm('⚠️ ADVERTENCIA: Se sobrescribirá la base de datos con el punto seleccionado. ¿Desea continuar?');">
                    <div class="mb-3">
                        <label class="form-label fw-bold text-warning">Puntos de Restauración Disponibles:</label>
                        <select name="backup_elegido" class="form-select bg-secondary text-white border-0" required>
                            <option value="" disabled selected>-- Seleccione un punto de restauración --</option>
                            {% for b in backups %}
                            <option value="{{ b }}">{{ b }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <button type="submit" class="btn btn-warning btn-lg w-100 fw-bold text-dark">
                        <i class="bi bi-arrow-counterclockwise me-2"></i> Revertir Sistema a este Punto
                    </button>
                </form>
            </div>
            <div class="card-footer text-center text-muted small py-3 bg-secondary">
                Avrora Soft - Vibola LLC &bull; Sistema de Autodefensa Académica
            </div>
        </div>
    </div>
</body>
</html>
"""

@app_rescate.route('/')
def index():
    backup_dir = os.path.join(os.getcwd(), 'static', 'backups')
    backups = []
    if os.path.exists(backup_dir):
        backups = sorted([f for f in os.listdir(backup_dir) if f.endswith('.db') or f.endswith('.avr')], reverse=True)
    return render_template_string(EMERGENCIA_TEMPLATE, backups=backups)

@app_rescate.route('/restaurar', methods=['POST'])
def restaurar():
    backup_elegido = request.form.get('backup_elegido')
    backup_dir = os.path.join(os.getcwd(), 'static', 'backups')
    instance_path = os.path.join(os.getcwd(), 'instance')
    db_path = os.path.join(instance_path, 'colegio_vaca_diez.db')
    
    origen = os.path.join(backup_dir, backup_elegido)
    if os.path.exists(origen):
        try:
            os.makedirs(instance_path, exist_ok=True)
            if backup_elegido.endswith('.db'):
                shutil.copy2(origen, db_path)
            print("✅ Sistema restaurado con éxito desde el monitor de emergencia.")
            return redirect('/')
        except Exception as ex:
            return f"Error al restaurar: {ex}"
    return "Respaldo no encontrado", 404

if __name__ == '__main__':
    print("\n🚨 [MONITOR DE RESCATE ACTIVADO]")
    print("🌐 Acceda a la consola de recuperación en: http://127.0.0.1:5001\n")
    app_rescate.run(host='0.0.0.0', port=5001, debug=False)