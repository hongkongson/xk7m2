@echo off
rem ============================================================
rem  Start the LAN "haha" page server. No internet needed.
rem
rem  ASCII only on purpose: cmd parses .bat as GBK on Chinese
rem  Windows, so UTF-8 Chinese comments here get mangled into
rem  broken commands. All Chinese text lives in serve.py.
rem
rem  Double-click this file. A black window opens and stays open
rem  while the server runs. Close that window to stop.
rem ============================================================
setlocal
cd /d "%~dp0"

set "PY="
rem Prefer the bundled venv python if it exists, else fall back to PATH
if exist "..\doclib\.venv\Scripts\python.exe" set "PY=..\doclib\.venv\Scripts\python.exe"
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
  where py >nul 2>&1 && set "PY=py"
)
if not defined PY (
  echo.
  echo   Python not found. Install Python 3, or run doclib's setup first.
  echo.
  pause
  exit /b 1
)

echo.
echo   Starting LAN server with: %PY%
echo.

"%PY%" "%~dp0serve.py"

echo.
echo   Server stopped.
pause
endlocal
