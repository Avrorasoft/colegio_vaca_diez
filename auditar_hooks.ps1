
$archivos = Get-ChildItem -Path . -Recurse -Include "*.py"
foreach ($archivo in $archivos) {
    $lineas = Get-Content $archivo.FullName -Encoding utf8 -ErrorAction SilentlyContinue
    $num = 1
    foreach ($linea in $lineas) {
        if ($linea -match "before_request" -or $linea -match "bloquear" -or $linea -match "turno" -or $linea -match "requerir") {
            Write-Host "[!] $($archivo.Name) (Línea $num) -> $linea" -ForegroundColor Yellow
        }
        $num++
    }
}

