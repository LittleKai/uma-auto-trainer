# -*- mode: python ; coding: utf-8 -*-

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
