@echo off
REM =============================================
REM Inicio automático del ERP Aeropostale
REM Ubicado en: %USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\
REM =============================================
cd /d "C:\Users\wilso\Downloads\kpi-system-main"
start /min "" "C:\Program Files\nodejs\node.exe" "C:\Users\wilso\AppData\Roaming\npm\node_modules\openclaw\dist\cli.js" status
timeout /t 10 /nobreak >nul
start /min "" streamlit run app.py --server.port 8501 --server.headless true
