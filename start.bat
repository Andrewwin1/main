@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   Escape Room — Запуск системы
echo ========================================
echo.

:: 1. Проверка и запуск Mosquitto
echo [1/3] Проверка Mosquitto...
tasklist /FI "IMAGENAME eq mosquitto.exe" 2>nul | find /i "mosquitto.exe" >nul
if %ERRORLEVEL%==0 (
    echo [+] Mosquitto уже запущен
) else (
    echo [*] Запуск Mosquitto...
    start "Mosquitto MQTT Broker" /MIN "C:\Program Files\Mosquitto\mosquitto.exe" -c mosquitto.conf
    timeout /t 2 >nul
    echo [+] Mosquitto запущен
)
echo.

:: 2. Запуск MQTT-слушателя
echo [2/3] Запуск MQTT-слушателя...
start "MQTT Listener" /MIN cmd /c "cd server ^&^& python mqtt_listener.py ^&^& pause"
timeout /t 1 >nul
echo [+] Слушатель запущен
echo.

:: 3. Запуск веб-сервера
echo [3/3] Запуск веб-сервера...
echo     Откроется в браузере через несколько секунд...
start "Web Server" /MIN cmd /c "cd server ^&^& python web_server.py ^&^& pause"
timeout /t 3 >nul
start http://localhost:5000

echo.
echo ========================================
echo   Все сервисы запущены!
echo   Веб-интерфейс: http://localhost:5000
echo ========================================
echo.
echo Для остановки — закройте появившиеся окна.
pause
