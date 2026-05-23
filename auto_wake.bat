@echo off
cd /d "C:\Users\wilso\Downloads\kpi-system-main"
timeout /t 15 /nobreak >nul
:: Arrancar Streamlit si no está corriendo
tasklist /fi "imagename eq streamlit.exe" 2>nul | find /i "streamlit.exe" >nul
if errorlevel 1 (
    start /min "" streamlit run app.py --server.port 8501 --server.headless true
)
:: Verificar Tailscale
tasklist /fi "imagename eq tailscale-ipn.exe" 2>nul | find /i "tailscale-ipn.exe" >nul
if errorlevel 1 (
    start /min "" "C:\Program Files\Tailscale\tailscale.exe" up
)
