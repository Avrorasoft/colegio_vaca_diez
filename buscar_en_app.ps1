
$lineas = Get-Content "app.py" -Encoding utf8
$num = 1
foreach ($linea in $lineas) {
    if ($linea -match "login_turno") {
        Write-Host "[✔] app.py Línea $num -> $linea" -ForegroundColor Green
    }
    $num++
}

