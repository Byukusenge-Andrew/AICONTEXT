@echo off
echo Installing AIContext globally for your user environment...

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -m pip install --user -e "%~dp0."
) else if defined VIRTUAL_ENV (
    echo [Notice] Active virtualenv detected. Installing into active environment...
    python -m pip install -e "%~dp0."
) else (
    python -m pip install --user -e "%~dp0."
)

echo.
echo AIContext is now installed!
echo You can now open ANY project in your terminal or IDE and run:
echo   aicontext init
echo   aicontext visualize
echo   aicontext mcp
pause
