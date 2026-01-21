"""
PyInstaller hook for tkinter to ensure proper DLL loading
"""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import sys
import os

# Collect all tkinter submodules
hiddenimports = collect_submodules('tkinter')

# Add specific imports that might be missed
hiddenimports += [
    'tkinter',
    'tkinter.ttk',
    'tkinter.scrolledtext',
    'tkinter.messagebox',
    '_tkinter',
]

# Collect tkinter data files
datas = collect_data_files('tkinter')

# Add TCL/TK runtime files
python_dir = os.path.dirname(sys.executable)
tcl_dir = os.path.join(python_dir, 'tcl')
if os.path.exists(tcl_dir):
    datas += [(tcl_dir, 'tcl')]