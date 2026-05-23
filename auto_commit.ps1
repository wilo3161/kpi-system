# auto_commit.ps1 - Script para commit automático
# Se ejecuta desde el agente después de hacer cambios

param(
    [string]$Mensaje = "fix: actualizacion automatica"
)

$repoPath = "C:\Users\wilso\Downloads\kpi-system-main"
$git = "C:\Program Files\Git\bin\git.exe"

Set-Location $repoPath

# Verificar si hay cambios
$status = & $git status --porcelain
if (-not $status) {
    Write-Output "No hay cambios para commit"
    exit 0
}

# Add, Commit, Push
& $git add -A
& $git commit -m $Mensaje
& $git push origin master

if ($LASTEXITCODE -eq 0) {
    Write-Output "✅ Cambios subidos exitosamente: $Mensaje"
} else {
    Write-Output "❌ Error al subir cambios"
    exit 1
}
