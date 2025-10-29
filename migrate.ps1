Write-Host "🔄 Copiando archivos a la nueva estructura..." -ForegroundColor Cyan

if (Test-Path "templates") {
    Write-Host "📁 Copiando templates..." -ForegroundColor Yellow
    Copy-Item -Path "templates\*" -Destination "web\templates\" -Recurse -Force
    Write-Host "✅ Templates copiados" -ForegroundColor Green
} else {
    Write-Host "⚠️  Carpeta templates no encontrada" -ForegroundColor Red
}

if (Test-Path "static\css") {
    Write-Host "📁 Copiando CSS..." -ForegroundColor Yellow
    Copy-Item -Path "static\css\*" -Destination "web\static\css\" -Recurse -Force
    Write-Host "✅ CSS copiados" -ForegroundColor Green
}

if (Test-Path "static\js\main.js") {
    Write-Host "ℹ️  main.js ya fue refactorizado como app.js" -ForegroundColor Blue
}

Write-Host ""
Write-Host "🎉 Migración completada!" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Ejecuta: python main.py" -ForegroundColor White
Write-Host "2. Accede a: http://localhost:5000" -ForegroundColor White
Write-Host ""
