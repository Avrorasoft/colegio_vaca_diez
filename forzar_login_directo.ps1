
$ruta = "app.py"
$contenido = Get-Content$ruta -Raw -Encoding utf8

# Reemplazamos la funcion index para asegurarnos de que limpie la sesion
$bloqueNuevo = @""
@app.route(\x27/\x27)
def index():
    session.clear()
    # Si auth.login es una vista valida, redirigimos estrictamente ahi
    return redirect(url_for(\x27auth.login\x27))
@""

# Actualizamos en app.py
$contenido =$contenido -replace "def index\(\)[\s\S]*?return redirect\(url_for\(.*?\)\)", "def index():`n    session.clear()`n    return redirect(url_for(\x27auth.login\x27))"
Set-Content -Path $ruta -Value$contenido -Encoding utf8
Write-Host "[✔] index() actualizado para limpiar sesion y forzar autenticacion." -ForegroundColor Green

