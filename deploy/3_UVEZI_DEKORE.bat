@echo off
chcp 65001 >nul
rem  NA VM-u: uvoz kataloga dobavljača (slike dekora, podaci o pločama, predložene ABS trake) u Hub.
rem  Prvi argument je mapa s katalogom; bez argumenta uzima C:\Paneli\dekori.
rem  Slike se umanjuju i spremaju u C:\Paneli\Hub\dekori (ne idu u Git, ulaze u noćnu kopiju).
setlocal
set MAPA=%~1
if "%MAPA%"=="" set MAPA=C:\Paneli\dekori
if not exist "%MAPA%" (echo GRESKA: nema mape "%MAPA%" — kopiraj CLAUDE_COWORK\dekori na VM ili navedi putanju & pause & exit /b 1)
cd /d C:\Paneli\Hub
set HUB_DB=C:\Paneli\Hub\hub.db
echo Uvozim katalog iz "%MAPA%" ... (nekoliko minuta, kopiraju se i umanjuju slike)
py -m hub.sifrarnici.dekori --db %HUB_DB% --uvoz "%MAPA%" --tko IGOR || (echo GRESKA pri uvozu & pause & exit /b 1)
echo.
echo Gotovo. Slike su u C:\Paneli\Hub\dekori, potvrde dekora su na ekranu Šifrarnik - Slike dekora.
pause
