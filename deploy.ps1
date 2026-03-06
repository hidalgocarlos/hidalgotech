# deploy.ps1 - Solo tendrás que meter la contraseña cuando Git la pida (push)
Set-Location $PSScriptRoot

Write-Host "Añadiendo cambios..." -ForegroundColor Cyan
git add .
if ($LASTEXITCODE -ne 0) { exit 1 }

$msg = "Deploy " + (Get-Date -Format "yyyy-MM-dd HH:mm")
Write-Host "Commit: $msg" -ForegroundColor Cyan
git commit -m $msg
if ($LASTEXITCODE -ne 0) {
    Write-Host "Nada que commitear o error. ¿Continuar con push? (s/n)" -ForegroundColor Yellow
    $r = Read-Host
    if ($r -ne "s") { exit 1 }
}

Write-Host "Push a origin main (te pedirá usuario/contraseña si hace falta)..." -ForegroundColor Cyan
git push origin main
if ($LASTEXITCODE -eq 0) { Write-Host "Listo." -ForegroundColor Green } else { exit 1 }