
$ruta = "app.py"
$contenido = Get-Content $ruta -Raw -Encoding utf8

# Reemplazamos la función index completa para que sea estrictamente limpia y siempre exija login natural
$busquedaAntigua = @"
@app.route(\x27/\x27)
def index():
    # Si hay una sesion activa, entra al dashboard. Si no, va al login de turno.
    if \x27_user_id\x27 in session or \x27usuario_id\x27 in session or \x27rol\x27 in session:
        return redirect(url_for(\x27dashboard.index\x27))
    return redirect(url_for(\x27auth.login\x27))
"@

$bloqueNuevo = @"
@app.route(\x27/\x27)
def index():
    session.clear()
    return redirect(url_for(\x27auth.login\x27))
"@

if ($contenido -match "def index\(\):") {
    # Reemplazo seguro basado en regex para limpiar la ruta raíz
    $contenido = $contenido -replace "def index\(\)[\s\S]*?return redirect\(url_for\(\x27auth\.login\x27\)\)", $bloqueNuevo
    Set-Content -Path $ruta -Value $contenido -Encoding utf8
    Write-Host "[✔] ¡Ruta raíz optimizada para exigir login de forma estricta y natural!" -ForegroundColor Green
} else {
    Write-Host "[!] No se encontró la función index en app.py." -ForegroundColor Red
}

