@echo off
echo Installing Uma Musume Auto Train requirements...
echo.
echo This will install required Python packages.
echo Make sure Python is installed first!
echo.
pause

echo Installing packages...
pip install -r requirements.txt

echo.
if %errorlevel% == 0 (
    echo ✅ Installation completed successfully!
    echo You can now run UmaMusumeAutoTrain.exe
) else (
    echo ❌ Installation failed!
    echo Please check Python installation and try again.
)

echo.
pause
