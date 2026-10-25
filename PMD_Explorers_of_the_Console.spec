# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

src_dir = os.path.abspath('src')

a = Analysis(
    [os.path.join(src_dir, 'visualize.py')],
    pathex=[src_dir],
    binaries=[],
    datas=[],
    hiddenimports=[
        'data_utils',
        'dungeon',
        'pokemon',
        'pokemon_db',
        'moves_db',
        'items',
        'combat',
        'targeting',
        'input',
        'message_log',
        'save_game',
        'high_scores',
        'end_screen',
        'type_chart',
        'game',
    ],
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
    name='PMD_Explorers_of_the_Console',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
