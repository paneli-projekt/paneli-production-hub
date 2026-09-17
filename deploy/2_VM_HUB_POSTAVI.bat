@echo off
chcp 65001 >nul
rem  NA VM-u (cmd kao administrator), jednom: Python paketi, firewall 8766 samo LAN, probni start Huba.
cd /d C:\Paneli\Hub
echo [1/3] Python paketi (fastapi, uvicorn, reportlab, openpyxl, matplotlib...)
py -m pip install -q -r requirements.txt || (echo GRESKA: pip & pause & exit /b 1)
echo [2/3] Firewall: TCP 8766 samo iz LAN-a
netsh advfirewall firewall show rule name="Paneli - Hub 8766 (LAN)" >nul 2>&1 || netsh advfirewall firewall add rule name="Paneli - Hub 8766 (LAN)" dir=in action=allow protocol=TCP localport=8766 remoteip=192.168.5.0/24
echo [3/3] Start Huba (ovaj prozor ostaje otvoren; Ctrl+C gasi). Ekrani: http://192.168.5.201:8766/
set HUB_DB=C:\Paneli\Hub\hub.db
py -m uvicorn hub.api.app:app --host 0.0.0.0 --port 8766
