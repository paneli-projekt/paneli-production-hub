@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo ================================================================
echo  Paneli Production Hub - prvi commit i push na GitHub
echo  Mapa: %cd%
echo ================================================================
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo Git nije instaliran ili nije na PATH-u. Instaliraj Git for Windows ^(https://git-scm.com^) pa pokreni ponovno.
  pause
  exit /b 1
)

if not exist ".git" (
  echo [1/5] git init
  git init -b main
) else (
  echo [1/5] repozitorij vec postoji, preskacem init
)

echo [2/5] postavke autora
git config user.name "Igor"
git config user.email "superbia.osijek@gmail.com"
git config core.autocrlf true

echo [3/5] commit
git add -A
git commit -m "Faza 1 (audit) zatvorena: formati CPO/CIX/CPW, kalkulator PW-metodom, optimizator, dokumentacija D-01..D-28" || echo (nema novih promjena za commit)

echo [4/5] remote
git remote get-url origin >nul 2>nul
if errorlevel 1 (
  git remote add origin https://github.com/paneli-projekt/paneli-production-hub.git
) else (
  git remote set-url origin https://github.com/paneli-projekt/paneli-production-hub.git
)

echo [5/5] push - ako se otvori prozor za prijavu na GitHub, prijavi se u pregledniku ^(jednom^)
git push -u origin main
if errorlevel 1 (
  echo.
  echo Push nije prosao - pokusavam preuzeti postojece stanje s GitHuba i ponoviti...
  git pull --rebase origin main --allow-unrelated-histories
  git push -u origin main
)

echo.
echo Gotovo. Provjeri: https://github.com/paneli-projekt/paneli-production-hub
pause
