
Write-Host "[*] Iniciando limpieza profunda del proyecto..." -ForegroundColor Cyan

# 1. Eliminar todos los scripts .ps1 temporales de un solo uso creados durante la sesión
$ScriptsTemporales = @(
    "renombrar_plantilla.ps1",
    "inyectar_cajas_controladores.ps1",
    "inyectar_select_cajas.ps1",
    "corregir_reportes_caja.ps1",
    "corregir_importacion_caja.ps1",
    "corregir_fecha.ps1",
    "corregir_foto_gasto.ps1",
    "revertir_git.ps1",
    "auditar_calidad_proyecto.ps1",
    "compilar_exe.ps1",
    "compilar_estandar.ps1",
    "compilar_con_serial.ps1"
)

foreach ($script in $ScriptsTemporales) {
    if (Test-Path $script) {
        Remove-Item -Force $script
        Write-Host "[x] Eliminado script temporal: $script" -ForegroundColor DarkGray
    }
}

# 2. Limpiar bases de datos de prueba y respaldos locales
$BasesDeDatos = @("asestud_respaldo_*.db", "asestud.db")
foreach ($db in $BasesDeDatos) {
    Get-ChildItem -Path . -Filter $db -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
}
Write-Host "[x] Bases de datos locales y respaldos depurados." -ForegroundColor DarkGray

# 3. Limpiar carpetas de compilación previas de PyInstaller
$CarpetasPyInstaller = @("build", "dist", "output_installer")
foreach ($carpeta in $CarpetasPyInstaller) {
    if (Test-Path $carpeta) {
        Remove-Item -Recurse -Force $carpeta
        Write-Host "[x] Eliminado directorio: $carpeta" -ForegroundColor DarkGray
    }
}

# 4. Limpiar archivos spec huérfanos y temporales de Python
Get-ChildItem -Path . -Filter "*.spec" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Filter "*.pyc" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "[✔] ¡Limpieza total completada con éxito! El proyecto está reluciente." -ForegroundColor Green

