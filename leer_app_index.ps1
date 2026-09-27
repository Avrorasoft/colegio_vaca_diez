
$lineas = Get-Content "app.py" -Encoding utf8
for ($i = 205; $i -le 235; $i++) {
    if ($i -le $lineas.Count) {
        Write-Host "$($i): $($lineas[$i-1])"
    }
}

