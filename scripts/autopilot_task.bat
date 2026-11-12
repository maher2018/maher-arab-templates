@echo off
chcp 65001 >nul
cd /d "C:\Users\Dell\Desktop\complete_deployment.py\arab-templates"
"C:\Users\Dell\AppData\Local\Python\pythoncore-3.15-64\python.exe" "C:\Users\Dell\Desktop\complete_deployment.py\arab-templates\scripts\agents_swarm_core.py" --once --lang both --ideas 3 --templates --interval 60 --report "C:\Users\Dell\Desktop\complete_deployment.py\arab-templates\autopilot_report.json" >> "C:\Users\Dell\Desktop\complete_deployment.py\arab-templates\logs\autopilot_task.log" 2>&1
