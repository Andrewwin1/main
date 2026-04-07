@echo off
cd /d "%~dp0"

set MOSQUITTO_PID=
set LISTENER_PID=
set WEBSERVER_PID=

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
    start "Mosquitto" /MIN "C:\Program Files\Mosquitto\mosquitto.exe" -v
    timeout /t 2 >nul
    echo [+] Mosquitto started
)
echo:

echo [2/3] Starting MQTT Listener...
start "MQTT Listener" /MIN cmd /c "cd /d "%~dp0server" ^& python mqtt_listener.py ^& pause"
timeout /t 1 >nul
echo [+] Listener started
echo:

echo [3/3] Starting Web Server...
echo     Browser will open in a few seconds...
start "Web Server" /MIN cmd /c "cd /d "%~dp0server" ^& python web_server.py ^& pause"
timeout /t 3 >nul
start http://localhost:5000

echo:
echo ========================================
echo   All services started!
echo   Web UI: http://localhost:5000
echo ========================================
echo:
echo All services run in separate windows.
echo To stop - close those windows or press Ctrl+C here.
pause >nul

echo:
echo [*] Stopping services...
taskkill /FI "WINDOWTITLE eq MQTT Listener*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Web Server*" /T /F >nul 2>&1
echo [#] Services stopped.
