# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include
datas = [
    ('assets', 'assets'),
    ('config.json', '.'),
    ('race_filters.json', '.'),
]

# Hidden imports for modules that PyInstaller might miss
hiddenimports = [
    'PIL._tkinter_finder',
    'tkinter',
    'tkinter.ttk',
    'tkinter.scrolledtext',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageEnhance',
    'cv2',
    'numpy',
    'pyautogui',
    'pytesseract',
    'pygetwindow',
    'keyboard',
    'mss',
    'json',
    're',
    'threading',
    'time',
    'datetime',
    'sys',
    'os',
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

pyi_splash = Splash(
    'assets/splash.png' if os.path.exists('assets/splash.png') else None,
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
)

pyi_splash_target = Target(
    a.scripts,
    pyi_splash,
    exclude_binaries=True,
    name='UmaMusumeAutoTrain',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True if you want console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

pyi_splash_exclude = Exclude(pyi_splash_target)

pyi_splash_a = Analysis(
    [],
    pathex=[],
    binaries=a.binaries,
    datas=a.datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=pyi_splash_exclude.excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

exe = EXE(
    pyi_splash.binaries,
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
    console=False,  # Set to True if you want console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)
