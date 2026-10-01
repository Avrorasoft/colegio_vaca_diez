
$archivos = Get-ChildItem -Path . -Recurse -Include "*.py","*.html","*.js"
foreach ($archivo in $archivos) {
    $lineas = Get-Content $archivo.FullName -Encoding utf8 -ErrorAction SilentlyContinue
    $num = 1
    foreach ($linea in $lineas) {
        if ($linea -match "login_turno" -or $linea -match "login-turno") {
            Write-Host "[!] Encontrado en: $($archivo.Name) (Línea $num) -> $linea" -ForegroundColor Yellow
        }
        $num++
    }
}

