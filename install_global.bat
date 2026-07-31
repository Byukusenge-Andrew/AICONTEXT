@echo off
echo Installing AIContext globally for your user environment...
python -m pip install --user -e %~dp0
echo.
echo AIContext is now installed globally!
echo You can now open ANY project in your terminal or IDE and run:
echo   aicontext init
echo   aicontext visualize
echo   aicontext mcp
pause
