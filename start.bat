@echo off
cd /d "%~dp0"

set VP=%~dp0.venv\Scripts\python.exe
set SP=%~dp0server\

echo ========================================
echo   Escape Room Puzzle System
echo ========================================
echo:

echo [1/3] Checking Mosquitto...
tasklist /FI "IMAGENAME eq mosquitto.exe" 2>nul | find /i "mosquitto.exe" >nul
if %ERRORLEVEL%==0 (
    echo [+] Mosquitto already running
) else (
    echo [*] Starting Mosquitto...
    start "Mosquitto" /MIN "%PROGRAMFILES%\Mosquitto\mosquitto.exe" -v -c "%~dp0server\mosquitto.conf"
    timeout /t 2 >nul
    echo [+] Mosquitto started
)
echo:

echo [2/3] Starting MQTT Listener...
start "MQTT Listener" /B cmd /c ""%VP%" "%SP%mqtt_listener.py""
timeout /t 1 >nul
echo [+] Listener started
echo:

echo [3/3] Starting Web Server...
start "Web Server" /B cmd /c ""%VP%" "%SP%web_server.py""
timeout /t 4 >nul
start http://localhost:5000
echo [+] Web Server started
echo:
echo ========================================
echo   All services started!
echo   Web UI: http://localhost:5000
echo ========================================
echo:
pause
