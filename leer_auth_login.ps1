
$lineas = Get-Content "routes/auth.py" -Encoding utf8
for ($i = 18; $i -le 60; $i++) {
    Write-Host "$($i): $($lineas[$i-1])"
}

