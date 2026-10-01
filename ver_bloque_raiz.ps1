
$lineas = Get-Content "app.py" -Encoding utf8
for ($i = 200; $i -le 225; $i++) {
    Write-Host "$($i): $($lineas[$i-1])"
}

