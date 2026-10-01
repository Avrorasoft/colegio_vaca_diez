
$archivos = Get-ChildItem -Path . -Recurse -Include "*.py","*.html","*.js"
foreach ($archivo in $archivos) {
    $lineas = Get-Content $archivo.FullName -Encoding utf8 -ErrorAction SilentlyContinue
    $num = 1
    foreach ($linea in $lineas) {
        if ($linea -match "login_turno") {
            Write-Host "[✔] Archivo: $($archivo.Name) (Línea $num) -> $linea" -ForegroundColor Green
        }
        $num++
    }
}

