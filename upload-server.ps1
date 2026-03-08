# upload-server.ps1 — Sube el proyecto al servidor por SCP (sin GitHub)
# Uso: .\upload-server.ps1 [usuario@IP]  o  .\upload-server.ps1 -UseZip
# Ejemplo: .\upload-server.ps1 root@46.225.166.151

param(
    [string]$Server = "root@46.225.166.151",
    [string]$RemoteDir = "hidalgotech",
    [switch]$UseZip
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$Staging = Join-Path $env:TEMP "hidalgotech"

Write-Host "=== Subiendo proyecto a $Server (carpeta: ~/$RemoteDir) ===" -ForegroundColor Cyan
Write-Host ""

# Limpiar staging anterior
if (Test-Path $Staging) {
    Remove-Item $Staging -Recurse -Force
}
New-Item -ItemType Directory -Path $Staging | Out-Null

# Carpetas/archivos a excluir (no subir al servidor)
$ExcludeDirs = @(".git", ".idea", ".vscode", "node_modules", "__pycache__", "venv", ".venv", "env", ".cache")
$ExcludeFiles = @(".env", ".env.local", ".env.*.local")

# Copiar proyecto (respeta estructura, excluye lo anterior)
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

# Convertir .sh a LF para Linux
Get-ChildItem -Path $Staging -Filter "*.sh" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
    $c = [System.IO.File]::ReadAllText($_.FullName) -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($_.FullName, $c)
}

if ($UseZip) {
    # Opción ZIP: un solo archivo, más estable en redes lentas
    $ZipPath = Join-Path $env:TEMP "hidalgotech.zip"
    if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
    Write-Host "Creando ZIP..." -ForegroundColor Yellow
    Compress-Archive -Path (Join-Path $Staging "*") -DestinationPath $ZipPath -Force
    Write-Host "Subiendo ZIP al servidor..." -ForegroundColor Yellow
    & scp -o ConnectTimeout=30 $ZipPath "${Server}:~/hidalgotech.zip"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error en SCP." -ForegroundColor Red
        Remove-Item $Staging -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue
        exit 1
    }
    Write-Host "Descomprimiendo en el servidor (via SSH)..." -ForegroundColor Yellow
    & ssh -o ConnectTimeout=30 $Server "apt-get update -qq && apt-get install -y -qq unzip >/dev/null; rm -rf ~/hidalgotech.old 2>/dev/null; mv ~/hidalgotech ~/hidalgotech.old 2>/dev/null; mkdir -p ~/hidalgotech; unzip -o -q ~/hidalgotech.zip -d ~/hidalgotech; rm ~/hidalgotech.zip"
    Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue
} else {
    # Subir carpeta completa
    Write-Host "Subiendo por SCP (puede tardar unos minutos)..." -ForegroundColor Yellow
    $Target = "${Server}:~/"
    & scp -r -o ConnectTimeout=30 $Staging $Target
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error en SCP. Prueba:" -ForegroundColor Red
        Write-Host "  1. ssh-keygen -R 46.225.166.151   (si cambió la clave del servidor)" -ForegroundColor Gray
        Write-Host "  2. Comprobar que puedes entrar: ssh $Server" -ForegroundColor Gray
        Write-Host "  3. Usar subida por ZIP: .\upload-server.ps1 -UseZip" -ForegroundColor Gray
        Remove-Item $Staging -Recurse -Force -ErrorAction SilentlyContinue
        exit 1
    }
}

Remove-Item $Staging -Recurse -Force -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "Listo. Proyecto en el servidor: ~/hidalgotech" -ForegroundColor Green
Write-Host "En el servidor ejecuta:" -ForegroundColor Cyan
Write-Host "  cd ~/hidalgotech"
Write-Host "  sudo bash setup-server.sh   # si es la primera vez (instala Docker, etc.)"
Write-Host '  # o solo levantar: export $(grep -v "^#" .env | xargs) && bash deploy.sh'
