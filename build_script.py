#!/usr/bin/env python3
"""
Simple build script for Uma Musume Auto Train executable
Creates a standalone executable that users can run without Python
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Execute a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"🔄 {description}")
    print(f"{'='*50}")

    try:
        result = subprocess.run(command, shell=True, check=True,
                                capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}:")
        print(f"Command: {command}")
        print(f"Return code: {e.returncode}")
        print(f"Error: {e.stderr}")
        return False

def create_simple_spec():
    """Create a simple PyInstaller spec file without splash"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

datas = [
    ('assets', 'assets'),
    ('config.json', '.'),
    ('race_filters.json', '.'),
]

hiddenimports = [
    'PIL._tkinter_finder',
    'tkinter', 'tkinter.ttk', 'tkinter.scrolledtext',
    'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL.ImageEnhance',
    'cv2', 'numpy', 'pyautogui', 'pytesseract',
    'pygetwindow', 'keyboard', 'mss'
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='UmaMusumeAutoTrain',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''

    with open('simple_uma.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("✅ Created simple spec file: simple_uma.spec")

def build_executable():
    """Build executable using simple method"""
    print("🔨 Building executable...")

    # Clean previous builds
    for folder in ['dist', 'build']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"🧹 Cleaned {folder} directory")

    # Build with simple spec
    if not run_command("pyinstaller --clean simple_uma.spec", "Building with simple spec"):
        return False

    # Check result
    exe_path = "dist/UmaMusumeAutoTrain.exe"
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"✅ Executable created: {exe_path} ({size_mb:.1f} MB)")
        return True
    else:
        print("❌ Executable not found after build")
        return False

def create_user_package():
    """Create package for end users with install instructions"""
    package_dir = "UmaAutoTrain_Package"

    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)

    os.makedirs(package_dir)

    # Copy executable and essential files
    shutil.copy2("dist/UmaMusumeAutoTrain.exe", package_dir)

    for file in ["config.json", "race_filters.json"]:
        if os.path.exists(file):
            shutil.copy2(file, package_dir)

    if os.path.exists("assets"):
        shutil.copytree("assets", os.path.join(package_dir, "assets"))

    # Create setup instructions
    setup_instructions = """# Uma Musume Auto Train - Setup Instructions

## Required Software (Users Must Install)

### 1. Python 3.8+ (Required)
Download from: https://www.python.org/downloads/
- ✅ Add Python to PATH during installation
- ✅ Install pip (included by default)

### 2. Required Python Packages
Open Command Prompt (cmd) and run:
```
pip install tkinter pygetwindow Pillow opencv-python numpy pyautogui pytesseract keyboard mss
```

### 3. Tesseract OCR (Required)
Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Install to: `C:\\Program Files\\Tesseract-OCR\\`
- Add to PATH or update path in core/ocr.py

## How to Run

1. Ensure Uma Musume game is running
2. Set game window title to "Umamusume"
3. Double-click `UmaMusumeAutoTrain.exe`

## Troubleshooting

### Python Not Found
- Reinstall Python with "Add to PATH" checked
- Or run: `python --version` to verify installation

### Package Installation Errors
Try these commands:
```
python -m pip install --upgrade pip
pip install --user [package_name]
```

### OCR Not Working
- Verify Tesseract installation path
- Update path in core/ocr.py if needed

### Game Not Detected
- Check window title is exactly "Umamusume"
- Run game in windowed mode (not fullscreen)

## System Requirements
- Windows 10/11
- 4GB RAM minimum
- Uma Musume Pretty Derby game

## File Description
- `UmaMusumeAutoTrain.exe` - Main program
- `config.json` - Energy and stat settings
- `assets/` - Game UI images and icons
- `race_filters.json` - Race filter settings (auto-created)

## Support
This tool automates training in Uma Musume.
Use responsibly and ensure compliance with game terms.
"""

    with open(os.path.join(package_dir, "SETUP_INSTRUCTIONS.txt"), 'w', encoding='utf-8') as f:
        f.write(setup_instructions)

    # Create requirements file for users
    requirements = """# Uma Musume Auto Train - User Requirements
# Run: pip install -r requirements.txt

tkinter
pygetwindow==0.0.9
Pillow==10.0.1
opencv-python==4.8.1.78
numpy==1.24.3
pyautogui==0.9.54
pytesseract==0.3.10
keyboard==0.13.5
mss==9.0.1
"""

    with open(os.path.join(package_dir, "requirements.txt"), 'w', encoding='utf-8') as f:
        f.write(requirements)

    # Create install script for users
    install_script = """@echo off
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
"""

    with open(os.path.join(package_dir, "install_requirements.bat"), 'w', encoding='utf-8') as f:
        f.write(install_script)

    print(f"✅ User package created: {package_dir}/")

    # Show package contents
    print("\n📦 Package contents:")
    for root, dirs, files in os.walk(package_dir):
        level = root.replace(package_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

    return True

def main():
    """Main build process"""
    print("🚀 Uma Musume Auto Train - Simple Build")
    print("="*50)

    # Check if main.py exists
    if not os.path.exists("main.py"):
        print("❌ main.py not found!")
        return False

    # Install PyInstaller if needed
    try:
        import PyInstaller
        print("✅ PyInstaller found")
    except ImportError:
        print("📦 Installing PyInstaller...")
        if not run_command("pip install pyinstaller", "Installing PyInstaller"):
            return False

    # Create simple spec file
    create_simple_spec()

    # Build executable
    if not build_executable():
        return False

    # Create user package
    if not create_user_package():
        return False

    print("\n" + "="*50)
    print("🎉 BUILD COMPLETED!")
    print("="*50)
    print("📦 User Package: UmaAutoTrain_Package/")
    print("📋 Setup Instructions: UmaAutoTrain_Package/SETUP_INSTRUCTIONS.txt")
    print("💾 Requirements File: UmaAutoTrain_Package/requirements.txt")
    print("⚡ Install Script: UmaAutoTrain_Package/install_requirements.bat")
    print("\n🎯 Users need to:")
    print("  1. Install Python 3.8+")
    print("  2. Run install_requirements.bat")
    print("  3. Install Tesseract OCR")
    print("  4. Run UmaMusumeAutoTrain.exe")

    return True

if __name__ == "__main__":
    success = main()
    print("\nPress Enter to exit...")
    input()
    sys.exit(0 if success else 1)