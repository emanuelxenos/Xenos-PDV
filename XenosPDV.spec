# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

ctk_path = os.path.dirname(customtkinter.__file__)

datas = [
    (ctk_path, 'customtkinter'),
    ('assets', 'assets'),
]
datas += collect_data_files('reportlab')

hiddenimports = [
    'PIL._tkinter_finder',
    'sqlalchemy.sql.default_comparator',
    'sqlite3',
    'core.caminhos',
]
hiddenimports += collect_submodules('reportlab')
hiddenimports += collect_submodules('customtkinter')

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
    [],
    exclude_binaries=True,
    name='XenosPDV',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icone.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='XenosPDV',
)
