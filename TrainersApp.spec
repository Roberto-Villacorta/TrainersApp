# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Añadir carpetas del proyecto
added_files = [
    ('bbdd', 'bbdd'),
    ('logica', 'logica'),
    ('pantallas', 'pantallas'),
    ('utils', 'utils'),
    ('GUIA_DE_USO.md', '.'),
    ('README.md', '.'),
]

# Recopilar datos de dependencias pesadas si es necesario
# Por ejemplo, customtkinter necesita sus archivos de tema
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
datas = added_files + collect_data_files('customtkinter')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['sqlalchemy.ext.baked', 'gliner', 'transformers', 'torch', 'torchvision', 'timm', 'bitsandbytes', 'accelerate', 'einops'],
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
    name='TrainersApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TrainersApp',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='TrainersApp.app',
        icon=None, # Puedes añadir un archivo .icns aquí
        bundle_identifier='com.robertovillacorta.trainersapp',
    )


