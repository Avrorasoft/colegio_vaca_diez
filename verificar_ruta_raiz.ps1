
# Buscamos en qué archivo está definida la ruta principal "/"
$archivos = Get-ChildItem -Path . -Recurse -Filter "*.py" | Select-String -Pattern "@app\.route\(\xq/\xq\)" -SimpleMatch
foreach ($match in $archivos) {
    Write-Host "[*] Ruta raíz encontrada en: $($match.Path) en la línea $($match.LineNumber)" -ForegroundColor Cyan
    Write-Host "    Contenido: $($match.Line)" -ForegroundColor DarkGray
}

