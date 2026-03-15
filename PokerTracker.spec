# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['poker_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('poker.ico', '.')],
    hiddenimports=['PIL._tkinter_finder', 'matplotlib', 'matplotlib.backends.backend_tkagg', 'numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PokerTracker',
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
    icon=['poker.ico'],
)
