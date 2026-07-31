@echo off
echo ==============================================
echo   Publishing AIContext to PyPI (pip)
echo ==============================================
echo.

echo 1. Installing build tools (build & twine)...
python -m pip install --upgrade build twine

echo.
echo 2. Cleaning old build artifacts...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.egg-info rmdir /s /q *.egg-info

echo.
echo 3. Building source distribution and wheel...
python -m build

echo.
echo 4. Uploading package to PyPI...
python -m twine upload dist/*

echo.
echo Done! Anyone can now run: pip install aicontext-engine
pause
