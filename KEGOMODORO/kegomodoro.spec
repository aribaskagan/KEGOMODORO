# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import tkinter

block_cipher = None

datas = [
    ('dependencies/images', 'dependencies/images'),
    ('dependencies/audios', 'dependencies/audios'),
]

# Explicitly bundle the complete Tcl/Tk script libraries.  The automatic
# tkinter hook can omit init.tcl in this Conda environment, which makes a
# one-file Windows build fail at startup after extraction.
tcl_library = Path(tkinter.Tcl().eval('info library'))
tk_library = tcl_library.parent / 'tk8.6'
datas.extend([
    (str(tcl_library), '_tcl_data'),
    (str(tk_library), '_tk_data'),
])

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=['kegomodoro', 'PIL', 'pygame', 'requests'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'pytest',
        'tests',
    ],
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
    name='KEGOMODORO',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['dependencies/images/tomato_window.png'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='KEGOMODORO',
)
