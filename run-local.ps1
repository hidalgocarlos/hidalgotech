# Modo local SIN Traefik (funciona en Windows; evita problemas con el socket de Docker).
# Ejecutar desde la raiz del proyecto: .\run-local.ps1
#
# URLs:
#   http://localhost:8000  -> Portal (login)
#   http://localhost:8001  -> TikTok Downloader
#   http://localhost:8002  -> Instagram Downloader

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "Levantando apps en modo local (puertos 8000, 8001, 8002)..." -ForegroundColor Cyan
Set-Location $root
docker compose -f docker-compose.local.yml up -d --build

Write-Host ""
Write-Host "Listo. Abre en el navegador:" -ForegroundColor Green
Write-Host "  http://localhost:8000   (login / portal)"
Write-Host "  http://localhost:8001   (TikTok)"
Write-Host "  http://localhost:8002   (Instagram)"
Write-Host ""
Write-Host "Crear usuario admin (solo la primera vez):" -ForegroundColor Yellow
Write-Host "  docker exec portal python setup_admin.py admin TuPasswordSeguro123!"
Write-Host ""
