# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

block_cipher = None

python_dir = Path(sys.executable).parent
is_conda = (python_dir / 'Library').exists()

print(f"Building from: {python_dir}")
print(f"Conda environment: {is_conda}")

all_binaries = []
all_datas = []

if is_conda:
    library_bin = python_dir / 'Library' / 'bin'
    library_lib = python_dir / 'Library' / 'lib'
    dlls_dir = python_dir / 'DLLs'
    
    # Copy ALL DLLs from Library/bin to avoid missing dependencies
    if library_bin.exists():
        dll_count = 0
        for dll_file in library_bin.glob('*.dll'):
            all_binaries.append((str(dll_file), '.'))
            dll_count += 1
        print(f"  Added {dll_count} DLLs from Library/bin")
    
    # Copy ALL PYD files from DLLs directory
    if dlls_dir.exists():
        pyd_count = 0
        for pyd_file in dlls_dir.glob('*.pyd'):
            all_binaries.append((str(pyd_file), '.'))
            pyd_count += 1
        print(f"  Added {pyd_count} PYD files from DLLs")
    
    # Add TCL/TK libraries
    if library_lib.exists():
        for lib_name in ['tcl8.6', 'tk8.6', 'tcl8', 'tk8']:
            lib_path = library_lib / lib_name
            if lib_path.exists():
                all_datas.append((str(lib_path), os.path.join('tcl', lib_name)))
                print(f"  Added library: {lib_name}")

else:
    # Standard Python
    tk_libs = python_dir / 'DLLs'
    if tk_libs.exists():
        for file in tk_libs.glob('*'):
            if file.is_file():
                all_binaries.append((str(file), '.'))

added_files = all_datas

hidden_imports = [
    'PIL._tkinter_finder',
    'cv2', 'numpy', 'pytesseract', 'mss',
    'pygetwindow', 'pygetwindow._pygetwindow_win',
    'keyboard', 'keyboard._winkeyboard',
    'requests',
    'tkinter', 'tkinter.ttk', 'tkinter.scrolledtext', 
    'tkinter.messagebox', 'tkinter.filedialog',
    '_tkinter', '_ctypes', 'ctypes', 'ctypes.wintypes',
    'json', 'threading', 'time', 'datetime',
]

if sys.platform == 'win32':
    try:
        import win32gui
        hidden_imports.extend(['win32gui', 'win32con', 'win32api'])
    except:
        pass

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=all_binaries,
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
