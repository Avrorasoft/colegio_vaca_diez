
Get-ChildItem -Path . -Recurse -Filter "*.py" | ForEach-Object {
    $archivo = $_.FullName
    $lineas = Get-Content $archivo -Encoding utf8 -ErrorAction SilentlyContinue
    $num = 1
    foreach ($linea in $lineas) {
        if ($linea -match "before_request") {
            Write-Host "[✔] Encontrado en: $($_.Name) (Línea $num) -> $linea" -ForegroundColor Green
        }
        $num++
    }
}

