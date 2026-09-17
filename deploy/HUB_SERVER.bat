@echo off
rem  Headless start Huba na VM-u (za Task Scheduler "Paneli - Hub Server": At startup, run whether logged on or not, restart on failure).
cd /d C:\Paneli\Hub
set HUB_DB=C:\Paneli\Hub\hub.db
py -m uvicorn hub.api.app:app --host 0.0.0.0 --port 8766 --log-level warning >> C:\Paneli\Hub\hub_server.log 2>&1
