# -*- mode: python ; coding: utf-8 -*-

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
