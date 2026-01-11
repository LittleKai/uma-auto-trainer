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

def remove_old_spec_files():
    """Remove old spec files that need to be cleaned up"""
    old_spec_files = ["simple_uma.spec", "uma_auto.spec", "uma_auto_train.spec"]

    for spec_file in old_spec_files:
        if os.path.exists(spec_file):
            try:
                os.remove(spec_file)
                print_success(f"Removed old spec file: {spec_file}")
            except Exception as e:
                print_warning(f"Could not remove {spec_file}: {e}")

def create_spec_file():
    """Create PyInstaller spec file for multi-file build with tkinter support"""
    print_header("Creating PyInstaller Spec File")

    spec_content = """# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

block_cipher = None

# Find Python installation directory for tkinter DLLs
python_dir = Path(sys.executable).parent
tcl_dir = python_dir / 'tcl'
tk_libs = python_dir / 'DLLs'

# Collect tkinter related files
tkinter_binaries = []
tkinter_datas = []

# Add TCL/TK DLLs
if tk_libs.exists():
    for dll in tk_libs.glob('tcl*.dll'):
        tkinter_binaries.append((str(dll), '.'))
    for dll in tk_libs.glob('tk*.dll'):
        tkinter_binaries.append((str(dll), '.'))
    for dll in tk_libs.glob('_tkinter*.pyd'):
        tkinter_binaries.append((str(dll), '.'))

# Add TCL library files
if tcl_dir.exists():
    tkinter_datas.append((str(tcl_dir), 'tcl'))

# Data files to include
added_files = [
    ('assets', 'assets'),
]

# Add tkinter data files
added_files.extend(tkinter_datas)

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
    '_tkinter',
    'json',
    'threading',
    'time',
    'datetime',
    're',
    'os',
    'sys',
    'ctypes',
    'ctypes.wintypes',
    'win32gui',
    'win32con',
    'win32api',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=tkinter_binaries,
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
    [],
    exclude_binaries=True,
    name='Uma_Musume_Auto_Train',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Uma_Musume_Auto_Train',
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
        'README.txt'
    ]

    required_directories = [
        'assets',
        'core',
        'utils',
        'gui'
    ]

    missing_files = []

    for file in required_files:
        if os.path.exists(file):
            print_success(f"Found: {file}")
        else:
            print_error(f"Missing: {file}")
            missing_files.append(file)

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

def create_default_config():
    """Create default bot_settings.json if it doesn't exist"""
    print_header("Creating Default Configuration Files")

    config_content = {
        "track": {
            "turf": True,
            "dirt": False
        },
        "distance": {
            "sprint": False,
            "mile": True,
            "medium": True,
            "long": True
        },
        "grade": {
            "g1": True,
            "g2": False,
            "g3": False
        },
        "minimum_mood": "NORMAL",
        "priority_strategy": "Train Score 3+",
        "allow_continuous_racing": False,
        "manual_event_handling": False,
        "enable_stop_conditions": False,
        "stop_on_infirmary": True,
        "stop_on_need_rest": False,
        "stop_on_low_mood": True,
        "stop_on_race_day": False,
        "stop_mood_threshold": "GREAT",
        "stop_before_summer": True,
        "stop_at_month": False,
        "target_month": "Junior Year Dec 1",
        "stop_on_ura_final": False,
        "stop_on_warning": True,
        "event_choice": {
            "auto_event_map": True,
            "auto_first_choice": False,
            "uma_musume": "None",
            "support_cards": ["None"] * 6,
            "unknown_event_action": "Search in other special events",
            "current_set": 1,
            "preset_names": {str(i): f"Preset {i}" for i in range(1, 21)},
            "preset_sets": {
                str(i): {
                    "uma_musume": "None",
                    "support_cards": ["None"] * 6
                } for i in range(1, 21)
            }
        },
        "team_trials": {
            "daily_activity_type": "Team Trial",
            "opponent_type": "Opponent 2",
            "use_parfait_gift_pvp": True,
            "stop_if_shop": False,
            "legend_race_use_parfait": False,
            "legend_race_stop_if_shop": False
        },
        "window": {
            "width": 700,
            "height": 900,
            "x": 100,
            "y": 20
        },
        "scenario": "URA Final"
    }

    try:
        with open('bot_settings_default.json', 'w', encoding='utf-8') as f:
            json.dump(config_content, f, indent=2)
        print_success("Created default bot_settings_default.json")
        return True
    except Exception as e:
        print_error(f"Failed to create bot_settings_default.json: {e}")
        return False

def build_executable():
    """Build the executable using PyInstaller"""
    print_header("Building Executable")

    print_info("Starting PyInstaller build process...")
    print_info("This may take several minutes depending on your system...")

    # Remove old dist folder if exists
    dist_folder = "dist/Uma_Musume_Auto_Train"
    if os.path.exists(dist_folder):
        try:
            shutil.rmtree(dist_folder)
            print_success(f"Removed old dist folder: {dist_folder}")
        except Exception as e:
            print_warning(f"Could not remove old dist folder: {e}")

    try:
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "-y",  # Add this flag to remove output directory without confirmation
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

    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)

    try:
        os.makedirs(dist_dir, exist_ok=True)

        # Copy the entire build folder
        build_folder = "dist/Uma_Musume_Auto_Train"
        if os.path.exists(build_folder):
            shutil.copytree(build_folder, os.path.join(dist_dir, "Uma_Musume_Auto_Train"))
            print_success("Copied executable folder")
        else:
            print_error("Executable folder not found in dist")
            return False

        # Copy README.txt
        if os.path.exists("README.txt"):
            shutil.copy2("README.txt", os.path.join(dist_dir, "README.txt"))
            print_success("Copied README.txt")
        else:
            print_warning("README.txt not found")

        # Copy default config
        if os.path.exists("bot_settings_default.json"):
            shutil.copy2("bot_settings_default.json",
                         os.path.join(dist_dir, "Uma_Musume_Auto_Train", "bot_settings.json"))
            print_success("Copied default bot_settings.json")

        print_success(f"Distribution package created in: {dist_dir}")
        return True

    except Exception as e:
        print_error(f"Failed to create distribution package: {e}")
        return False

def cleanup_build_files():
    """Clean up build artifacts including spec files automatically"""
    print_header("Cleaning Up Build Files")

    cleanup_items = [
        "build",
        "uma_auto_train.spec",
        "bot_settings_default.json"
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

    remove_old_spec_files()

    build_steps = [
        ("PyInstaller", check_pyinstaller),
        ("Required Files", check_required_files),
        ("Default Config", create_default_config),
        ("Spec File", create_spec_file),
        ("Executable", build_executable),
        ("Distribution Package", create_distribution_package)
    ]

    failed_steps = []

    for step_name, step_function in build_steps:
        try:
            if not step_function():
                failed_steps.append(step_name)
                break
        except Exception as e:
            print_error(f"Unexpected error in {step_name}: {e}")
            failed_steps.append(step_name)
            break

    print_header("Build Results")

    if failed_steps:
        print_error(f"Build failed at step: {failed_steps[0]}")
        print_info("Please fix the issue and try again")
    else:
        print_success("🎉 Executable build completed successfully!")

        print_colored("\n📦 Distribution Package Created:", Colors.BOLD)
        print_info("Folder: Uma_Musume_Auto_Train_Distribution/")
        print_info("Contains:")
        print_info("  - Uma_Musume_Auto_Train/ (executable folder)")
        print_info("  - README.txt (user instructions)")

        print_colored("\n🚀 How to Distribute:", Colors.BOLD)
        print_info("1. Zip the 'Uma_Musume_Auto_Train_Distribution' folder")
        print_info("2. Send the zip file to users")
        print_info("3. Users extract and run Uma_Musume_Auto_Train.exe in the folder")
        print_info("4. Users need to install Tesseract OCR separately")

    cleanup_build_files()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\nBuild interrupted by user")
    except Exception as e:
        print_error(f"Unexpected error during build: {e}")
        print_info("Please report this error to the developer")