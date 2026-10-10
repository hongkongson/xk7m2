@echo off
rem ============================================================
rem  Record what the computer is PLAYING (WASAPI loopback).
rem
rem  ASCII only on purpose: cmd parses .bat as GBK on Chinese
rem  Windows, so UTF-8 Chinese comments get mangled into broken
rem  commands. All Chinese messages live in rec.py.
rem
rem  NOTE: this machine has several Pythons (system + doclib venv).
rem  'soundcard' is only installed in ONE of them. So we do NOT
rem  guess by path -- we TEST each candidate with `import soundcard`
rem  and use the first one that actually works. Guessing by path is
rem  exactly what broke this launcher the first time.
rem
rem  Double-click, then switch to the browser and play the video.
rem  Records 20 seconds and stops by itself.
rem ============================================================
setlocal
cd /d "%~dp0"

set "PY="
set "CAND1=D:\00_navigation\python\python.exe"
set "CAND2=%~dp0..\doclib\.venv\Scripts\python.exe"

rem ---- 1. try each known Python, keep the first that has soundcard ----
if not defined PY if exist "%CAND1%" (
  "%CAND1%" -c "import soundcard" >nul 2>&1 && set "PY=%CAND1%"
)
if not defined PY if exist "%CAND2%" (
  "%CAND2%" -c "import soundcard" >nul 2>&1 && set "PY=%CAND2%"
)
if not defined PY (
  python -c "import soundcard" >nul 2>&1 && set "PY=python"
)

rem ---- 2. none of them has it: install it, then retry ----
if not defined PY (
  echo.
  echo   No Python with 'soundcard' found. Trying to install it...
  echo.
  if exist "%CAND1%" (
    "%CAND1%" -m pip install --quiet soundcard numpy
    "%CAND1%" -c "import soundcard" >nul 2>&1 && set "PY=%CAND1%"
  )
)
if not defined PY if exist "%CAND2%" (
  "%CAND2%" -m pip install --quiet soundcard numpy
  "%CAND2%" -c "import soundcard" >nul 2>&1 && set "PY=%CAND2%"
)

if not defined PY (
  echo.
  echo   Could not find or install a Python with 'soundcard'.
  echo   Run this by hand and send the output:
  echo.
  echo       python -m pip install soundcard numpy
  echo.
  pause
  exit /b 1
)

echo.
echo   Using Python: %PY%
echo   Recorder starting. Play the video when the countdown ends.
echo.

set PYTHONIOENCODING=utf-8
"%PY%" "%~dp0rec.py" 20 "%~dp0laugh-raw.wav"

echo.
echo   Done. File: %~dp0laugh-raw.wav
echo.
pause
endlocal
