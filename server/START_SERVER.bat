@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo تشغيل خادم Arab Templates على http://127.0.0.1:5075
start "" http://127.0.0.1:5075/
python server.py --port 5075
pause
