#!/usr/bin/env python3
"""
Uma Musume Auto Train - Executable Builder
This script creates a standalone executable file from the Python source code.
"""

import subprocess
import sys
import os
import shutil
import json
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text, color=Colors.OKBLUE):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.ENDC}")

def print_header(text):
    """Print section header"""
    print_colored(f"\n{'='*60}", Colors.HEADER)
    print_colored(f"{text}", Colors.HEADER)
    print_colored(f"{'='*60}", Colors.HEADER)

def print_success(text):
    """Print success message"""
    print_colored(f"✅ {text}", Colors.OKGREEN)

def print_warning(text):
    """Print warning message"""
    print_colored(f"⚠️  {text}", Colors.WARNING)

def print_error(text):
    """Print error message"""
    print_colored(f"❌ {text}", Colors.FAIL)

def print_info(text):
    """Print info message"""
    print_colored(f"ℹ️  {text}", Colors.OKCYAN)

def check_pyinstaller():
    """Check if PyInstaller is installed, install if not"""
    print_header("Checking PyInstaller")

    try:
        import PyInstaller
        print_success("PyInstaller is already installed")
        return True
    except ImportError:
        print_info("PyInstaller not found, installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"],
                           check=True, capture_output=True)
            print_success("PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install PyInstaller: {e}")
            return False

def create_spec_file():
    """Create PyInstaller spec file with improved window detection support"""
    print_header("Creating PyInstaller Spec File")

    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include
added_files = [
    ('assets', 'assets'),
    ('config.json', '.'),
    ('bot_settings.json', '.'),
    ('region_settings.json', '.'),
]

# Hidden imports that PyInstaller might miss
hidden_imports = [
    'PIL._tkinter_finder',
    'cv2',
    'numpy',
    'pytesseract',
    'mss',
    'pygetwindow',
    'pygetwindow._pygetwindow_win',
    'pygetwindow._pygetwindow_macos', 
    'pygetwindow._pygetwindow_linux',
    'keyboard',
    'requests',
    'tkinter',
    'tkinter.ttk',
    'tkinter.scrolledtext',
    'tkinter.messagebox',
    'json',
    'threading',
    'time',
    'datetime',
    're',
    'os',
    'sys',
    'pathlib',
    'ctypes',
    'ctypes.wintypes',
    'win32gui',
    'win32con',
    'win32api',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'pandas', 'IPython'],
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
    name='Uma_Musume_Auto_Train',
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
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
"""

    try:
        with open('uma_auto_train.spec', 'w', encoding='utf-8') as f:
            f.write(spec_content)
        print_success("Created PyInstaller spec file: uma_auto_train.spec")
        return True
    except Exception as e:
        print_error(f"Failed to create spec file: {e}")
        return False

def check_required_files():
    """Check if all required files exist"""
    print_header("Checking Required Files")

    required_files = [
        'main.py',
        'config.json',
        'bot_settings.json'
    ]

    required_directories = [
        'assets',
        'core',
        'utils'
    ]

    missing_files = []

    # Check files
    for file in required_files:
        if os.path.exists(file):
            print_success(f"Found: {file}")
        else:
            print_error(f"Missing: {file}")
            missing_files.append(file)

    # Check directories
    for directory in required_directories:
        if os.path.exists(directory):
            print_success(f"Found directory: {directory}")
        else:
            print_error(f"Missing directory: {directory}")
            missing_files.append(directory)

    if missing_files:
        print_error("Some required files/directories are missing!")
        return False

    return True

def create_default_files():
    """Create default configuration files if they don't exist"""
    print_header("Creating Default Configuration Files")

    # Create config.json if missing
    if not os.path.exists('config.json'):
        config_content = {
            "priority_stat": ["spd", "pwr", "sta", "wit", "guts"],
            "maximum_failure": 15,
            "minimum_energy_percentage": 40,
            "critical_energy_percentage": 20,
            "stat_caps": {
                "spd": 1120,
                "sta": 1120,
                "pwr": 1120,
                "guts": 500,
                "wit": 500
            },
            "key": "jJ10uNHDwuPW9LGNWWZ2"
        }

        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config_content, f, indent=2)
            print_success("Created default config.json")
        except Exception as e:
            print_error(f"Failed to create config.json: {e}")
            return False

    # Create bot_settings.json if missing
    if not os.path.exists('bot_settings.json'):
        bot_settings_content = {
            "track": {
                "turf": True,
                "dirt": False
            },
            "distance": {
                "sprint": False,
                "mile": False,
                "medium": True,
                "long": True
            },
            "grade": {
                "g1": True,
                "g2": True,
                "g3": False,
                "op": False,
                "unknown": False
            },
            "minimum_mood": "NORMAL",
            "priority_strategy": "Train Score 2.5+",
            "allow_continuous_racing": True,
            "manual_event_handling": False
        }

        try:
            with open('bot_settings.json', 'w', encoding='utf-8') as f:
                json.dump(bot_settings_content, f, indent=2)
            print_success("Created default bot_settings.json")
        except Exception as e:
            print_error(f"Failed to create bot_settings.json: {e}")
            return False

    return True

def build_executable():
    """Build the executable using PyInstaller"""
    print_header("Building Executable")

    print_info("Starting PyInstaller build process...")
    print_info("This may take several minutes depending on your system...")

    try:
        # Use the spec file for building
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "uma_auto_train.spec"
        ], check=True, capture_output=True, text=True)

        print_success("Executable built successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print_error("Failed to build executable")
        print_error(f"Error output: {e.stderr}")
        return False

def create_distribution_package():
    """Create a distribution package with all necessary files"""
    print_header("Creating Distribution Package")

    dist_dir = "Uma_Musume_Auto_Train_Distribution"

    # Clean previous distribution
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)

    try:
        # Create distribution directory
        os.makedirs(dist_dir, exist_ok=True)

        # Copy executable
        exe_path = "dist/Uma_Musume_Auto_Train.exe"
        if os.path.exists(exe_path):
            shutil.copy2(exe_path, os.path.join(dist_dir, "Uma_Musume_Auto_Train.exe"))
            print_success("Copied executable")
        else:
            print_error("Executable not found in dist folder")
            return False

        # Copy assets folder
        if os.path.exists("assets"):
            shutil.copytree("assets", os.path.join(dist_dir, "assets"))
            print_success("Copied assets folder")

        # Copy configuration files
        config_files = ["config.json", "bot_settings.json"]
        for config_file in config_files:
            if os.path.exists(config_file):
                shutil.copy2(config_file, os.path.join(dist_dir, config_file))
                print_success(f"Copied {config_file}")

        # Create README file for users
        readme_content = """Uma Musume Auto Train

System Requirements:
- Windows 10/11
- Screen resolution: 1920x1080
- Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
- Tesseract OCR installed at: C:\\Program Files\\Tesseract-OCR\\
- Run Uma Musume game in fullscreen mode
- Due to the tool's mouse control functionality, please add the exe file to Exclusions under Windows Security > Virus & threat protection to prevent interference.

How to Use
1. Double-click "Uma_Musume_Auto_Train.exe" to start
2. Configure strategy settings in the GUI
3. Set up race filters according to your preferences
4. Press F1 to start the bot

Keyboard Shortcuts:
- F1: Start Bot
- F2: Pause/Resume Bot
- F3: Stop Bot
- F5: Force Exit Program

Configuration Files:
- config.json: Basic bot configuration
- bot_settings.json: Strategy and filter settings
- region_settings.json: OCR region coordinates (auto-generated)

Troubleshooting:
- If OCR detection fails, use "Region Settings" in the GUI to adjust coordinates
- Make sure Tesseract is installed correctly
- Ensure game window title contains "Umamusume"
- Check that screen resolution is 1920x1080
- Note: each time the game starts, the position of MOOD may change, leading to incorrect MOOD reading, so you will need to recheck the region position of MOOD.
"""

        with open(os.path.join(dist_dir, "README.txt"), "w", encoding="utf-8") as f:
            f.write(readme_content)
        print_success("Created README.txt")

        print_success(f"Distribution package created in: {dist_dir}")
        return True

    except Exception as e:
        print_error(f"Failed to create distribution package: {e}")
        return False

def cleanup_build_files():
    """Clean up build artifacts"""
    print_header("Cleaning Up Build Files")

    cleanup_items = [
        "build",
        "dist",
        "__pycache__",
        "uma_auto_train.spec"
    ]

    for item in cleanup_items:
        try:
            if os.path.exists(item):
                if os.path.isdir(item):
                    shutil.rmtree(item)
                else:
                    os.remove(item)
                print_success(f"Removed: {item}")
        except Exception as e:
            print_warning(f"Could not remove {item}: {e}")

def main():
    """Main build process"""
    print_colored("""
    ╔══════════════════════════════════════════════════════════════╗
    ║            Uma Musume Auto Train - Executable Builder        ║
    ║                   Developed by LittleKai                     ║
    ╚══════════════════════════════════════════════════════════════╝
    """, Colors.HEADER)

    print_info("This script will create a standalone executable (.exe) file")
    print_info("The executable can be distributed without source code")

    # Wait for user confirmation
    response = input(f"\n{Colors.OKCYAN}Continue with build? (y/N): {Colors.ENDC}").strip().lower()
    if response not in ['y', 'yes']:
        print_info("Build cancelled by user")
        return

    # Build steps
    build_steps = [
        ("PyInstaller", check_pyinstaller),
        ("Required Files", check_required_files),
        ("Default Files", create_default_files),
        ("Spec File", create_spec_file),
        ("Executable", build_executable),
        ("Distribution Package", create_distribution_package)
    ]

    failed_steps = []

    for step_name, step_function in build_steps:
        try:
            if not step_function():
                failed_steps.append(step_name)
                break  # Stop on first failure for build process
        except Exception as e:
            print_error(f"Unexpected error in {step_name}: {e}")
            failed_steps.append(step_name)
            break

    # Print results
    print_header("Build Results")

    if failed_steps:
        print_error(f"Build failed at step: {failed_steps[0]}")
        print_info("Please fix the issue and try again")
    else:
        print_success("🎉 Executable build completed successfully!")

        print_colored("\n📦 Distribution Package Created:", Colors.BOLD)
        print_info("Folder: Uma_Musume_Auto_Train_Distribution/")
        print_info("Contains:")
        print_info("  - Uma_Musume_Auto_Train.exe (main executable)")
        print_info("  - assets/ (required game assets)")
        print_info("  - config.json (configuration file)")
        print_info("  - bot_settings.json (bot settings)")
        print_info("  - README.txt (user instructions)")

        print_colored("\n🚀 How to Distribute:", Colors.BOLD)
        print_info("1. Zip the 'Uma_Musume_Auto_Train_Distribution' folder")
        print_info("2. Send the zip file to users")
        print_info("3. Users extract and run Uma_Musume_Auto_Train.exe")
        print_info("4. Users need to install Tesseract OCR separately")

    # Clean up build files
    response = input(f"\n{Colors.OKCYAN}Clean up build files? (Y/n): {Colors.ENDC}").strip().lower()
    if response not in ['n', 'no']:
        cleanup_build_files()

    print_colored(f"\n{Colors.BOLD}Press Enter to exit...{Colors.ENDC}")
    input()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\nBuild interrupted by user")
    except Exception as e:
        print_error(f"Unexpected error during build: {e}")
        print_info("Please report this error to the developer")