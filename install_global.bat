@echo off
echo Installing AIContext globally for your user environment...

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -m pip install --user -e "%~dp0."
    powershell -Command "[Environment]::SetEnvironmentVariable('PATH', [Environment]::GetEnvironmentVariable('PATH', 'User') + ';C:\Users\user\AppData\Roaming\Python\Python314\Scripts', 'User')" >nul 2>&1
) else if defined VIRTUAL_ENV (
    echo [Notice] Active virtualenv detected. Installing into active environment...
    python -m pip install -e "%~dp0."
) else (
    python -m pip install --user -e "%~dp0."
)

echo.
echo AIContext is now installed!
echo.
echo NOTE: If running 'aicontext' in a new PowerShell window fails, restart your terminal or run:
echo   py -m aicontext.cli init
echo.
echo You can now open ANY project in your terminal or IDE and run:
echo   aicontext init  (or: py -m aicontext.cli init)
echo   aicontext visualize
echo   aicontext mcp
pause
