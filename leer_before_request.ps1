
$lineas = Get-Content "app.py" -Encoding utf8
Write-Host "--- BLOQUE CERCA DE LINEA 128 ---" -ForegroundColor Cyan
for ($i = 120; $i -le 145; $i++) { Write-Host "$i: $($lineas[$i-1])" }
Write-Host "--- BLOQUE CERCA DE LINEA 270 ---" -ForegroundColor Cyan
for ($i = 265; $i -le 290; $i++) { Write-Host "$i: $($lineas[$i-1])" }

