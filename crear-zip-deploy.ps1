# crear-zip-deploy.ps1 — Crea un ZIP con todo el sitio para subir por MobaXterm
# Uso: .\crear-zip-deploy.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$Staging = Join-Path $env:TEMP "hidalgotech"
$ZipName = "hidalgotech-deploy.zip"
$ZipPath = Join-Path $ProjectRoot $ZipName

Write-Host "=== Creando ZIP del sitio ===" -ForegroundColor Cyan

if (Test-Path $Staging) { Remove-Item $Staging -Recurse -Force }
New-Item -ItemType Directory -Path $Staging | Out-Null

$ExcludeDirs = @(".git", ".idea", ".vscode", "node_modules", "__pycache__", "venv", ".venv", "env", ".cache")
$ExcludeFiles = @(".env", ".env.local", ".env.*.local")

$all = Get-ChildItem -Path $ProjectRoot -Force -Recurse -ErrorAction SilentlyContinue
foreach ($item in $all) {
    $rel = $item.FullName.Substring($ProjectRoot.Length).TrimStart("\", "/")
    if ([string]::IsNullOrWhiteSpace($rel)) { continue }
    $skip = $false
    foreach ($part in $rel -split "[\\/]") {
        if ($part -in $ExcludeDirs) { $skip = $true; break }
        if ($part -eq "data" -and $rel -match "^(portal|app-[^\\/]+)\\data") { $skip = $true; break }
    }
    if ($item.Name -in $ExcludeFiles) { $skip = $true }
    if ($item.Name -eq "acme.json") { $skip = $true }
    if ($item.Extension -match "\.(pyc|log|tmp)$") { $skip = $true }
    if ($skip) { continue }

    $dest = Join-Path $Staging $rel
    if ($item.PSIsContainer) {
        if (!(Test-Path $dest)) { New-Item -ItemType Directory -Path $dest -Force | Out-Null }
    } else {
        $destDir = Split-Path $dest -Parent
        if (!(Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
        Copy-Item $item.FullName -Destination $dest -Force
    }
}

Get-ChildItem -Path $Staging -Filter "*.sh" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
    $c = [System.IO.File]::ReadAllText($_.FullName) -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($_.FullName, $c)
}

if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path (Join-Path $Staging "*") -DestinationPath $ZipPath -Force
Remove-Item $Staging -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "ZIP creado." -ForegroundColor Green
Write-Host "Ruta local del ZIP:" -ForegroundColor Cyan
Write-Host "  $ZipPath" -ForegroundColor White
Write-Host ""
Write-Host "Sube ese archivo por MobaXterm al servidor (ej. a /root/)." -ForegroundColor Gray
Write-Host "Luego en el servidor:" -ForegroundColor Gray
Write-Host "  apt-get install -y unzip"
Write-Host "  mkdir -p ~/hidalgotech"
Write-Host "  unzip -o hidalgotech-deploy.zip -d ~/hidalgotech"
Write-Host "  cd ~/hidalgotech"
