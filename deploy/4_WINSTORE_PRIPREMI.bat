@echo off
rem Paneli Production Hub - priprema za citanje stanja iz baze Winstorea (D-98, dokument 38)
rem Instalira upravljacki program za SQL Server i provjeri vezu. Hub iz Winstorea SAMO CITA.
cd /d C:\Paneli\Hub || (echo GRESKA: nema C:\Paneli\Hub & pause & exit /b 1)
echo Instaliram pymssql...
py -m pip install -q pymssql || (echo GRESKA: pymssql se nije instalirao & pause & exit /b 1)
echo.
echo Provjeravam vezu na Winstore...
py -m hub.sifrarnici.winstore_sql --provjeri
echo.
echo Ako veza radi: ukljuci je u Hubu, Postavke - Winstore (upisi lozinku pa Spremi).
pause
