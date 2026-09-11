@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo ================================================================
echo  Paneli Production Hub - posalji izmjene na GitHub
echo ================================================================
set /p PORUKA=Opis izmjena (Enter = "azuriranje"):
if "%PORUKA%"=="" set PORUKA=azuriranje
git add -A
git commit -m "%PORUKA%" || echo (nema novih promjena za commit)
git pull --rebase origin main
git push origin main
echo.
echo Gotovo. https://github.com/paneli-projekt/paneli-production-hub
pause
