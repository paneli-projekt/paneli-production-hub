@echo off
chcp 65001 >nul
rem  Paneli Production Hub -> VM 192.168.5.201 (C:\Paneli\Hub). Pokrenuti NA IGOROVOM PC-u (cmd), kao i Knjigu.
rem  Prijava na VM racunom PANELI-PC\Igor (isti kao za Knjigu) - skripta trazi lozinku VM korisnika Igor.
rem  Kopira kod + hub.db (prvi put) + smtp_lozinka.txt; NE kopira .git, __pycache__, _to_delete, ulaz, backup.
setlocal
set "VM=192.168.5.201"
set "VMUSER=PANELI-PC\Igor"
set "SRC=%~dp0.."
set "DST=\\%VM%\c$\Paneli\Hub"
if not "%~1"=="" set "DST=%~1"

echo Zatvaram stare veze prema \\%VM% ...
net use \\%VM%\c$ /delete /y >nul 2>&1
net use \\%VM%\IPC$ /delete /y >nul 2>&1
echo Prijava na \\%VM%\c$ kao %VMUSER%  (upisi lozinku VM korisnika Igor):
net use \\%VM%\c$ /user:%VMUSER% *
if errorlevel 1 (echo GRESKA: prijava na VM nije uspjela - provjeri lozinku korisnika Igor na VM-u. & pause & exit /b 1)

echo Kopiram %SRC%  ->  %DST%
robocopy "%SRC%" "%DST%" /E /XO /R:2 /W:3 /NP /NFL /NDL /XJ /COPY:DAT /DCOPY:T /XD .git __pycache__ _to_delete .pytest_cache ulaz backup NARUDZBENICE /XF hub.db-wal hub.db-shm
if errorlevel 8 (echo GRESKA pri kopiranju & pause & exit /b 1)
echo.
echo Gotovo. Dalje NA VM-u (RDP, cmd kao administrator):  C:\Paneli\Hub\deploy\2_VM_HUB_POSTAVI.bat
pause
