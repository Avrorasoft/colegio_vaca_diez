
$ruta = "app.py"
$contenido = Get-Content $ruta -Raw -Encoding utf8

# Reemplazamos el login_turno por el login principal o directo en la ruta raíz
$busqueda = "return redirect(url_for(\x27auth.login_turno\x27))"
$reemplazo = "return redirect(url_for(\x27auth.login\x27))"

if ($contenido -match "auth\.login_turno") {
    $contenido = $contenido -replace [regex]::Escape($busqueda), $reemplazo
    Set-Content -Path $ruta -Value $contenido -Encoding utf8
    Write-Host "[✔] ¡Ruta raíz actualizada para dirigir de forma natural al login principal!" -ForegroundColor Green
} else {
    Write-Host "[!] No se encontró la coincidencia exacta, revisando alternativa..." -ForegroundColor Yellow
}

