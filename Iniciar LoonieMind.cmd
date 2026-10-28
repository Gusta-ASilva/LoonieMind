@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  where py >nul 2>nul
  if errorlevel 1 (
    python -m venv .venv
  ) else (
    py -3.12 -m venv .venv
  )
  if errorlevel 1 goto :fail
  .venv\Scripts\python.exe -m pip install -r requirements-lock.txt
  if errorlevel 1 goto :fail
)
.venv\Scripts\python.exe run.py
if errorlevel 1 goto :fail
exit /b 0
:fail
echo Nao foi possivel iniciar. Consulte o guia em docs\GUIA-DE-USO.md.
pause
exit /b 1
