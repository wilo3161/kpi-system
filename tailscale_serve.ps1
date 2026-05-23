# Configurar Tailscale Serve para OpenClaw Dashboard + ERP Streamlit
# Ejecutar como administrador
# Este script configura que los servicios sean accesibles via Tailscale (solo tus dispositivos)

# 1. Abrir puertos en firewall para Tailscale
New-NetFirewallRule -DisplayName "Tailscale-OpenClaw-Dashboard" -Direction Inbound -Protocol TCP -LocalPort 18789 -Action Allow -RemoteAddress "100.0.0.0/8"
New-NetFirewallRule -DisplayName "Tailscale-Streamlit-ERP" -Direction Inbound -Protocol TCP -LocalPort 8501 -Action Allow -RemoteAddress "100.0.0.0/8"

# 2. Configurar Tailscale Serve para ambos servicios
# Serve hace que los servicios corran en el puerto 443 de Tailscale (https)
& "C:\Program Files\Tailscale\tailscale.exe" serve --bg --https=443 http://127.0.0.1:18789
& "C:\Program Files\Tailscale\tailscale.exe" serve --bg --https=8501 http://127.0.0.1:8501

Write-Host "`n✅ Tailscale Serve configurado!"
Write-Host "🔗 OpenClaw Dashboard: https://100.75.176.112/"
Write-Host "🔗 ERP Streamlit:      https://100.75.176.112:8501/"
Write-Host ""
Write-Host "Accede desde tu movil/otro PC con Tailscale:"
Write-Host "Dashboard: http://100.75.176.112:18789"
Write-Host "ERP:       http://100.75.176.112:8501"
