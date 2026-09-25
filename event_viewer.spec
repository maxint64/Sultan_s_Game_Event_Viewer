# -*- mode: python ; coding: utf-8 -*-
import os

# 输出目录由构建命令的 --distpath 和 --workpath 显式指定
# Keep the executable name ASCII-only so it is safe across build and release tools.
BASE_APP_NAME = 'SultansGameEventViewer'
RELEASE_TAG = os.environ.get('APP_RELEASE_TAG')
if not RELEASE_TAG:
    raise ValueError('APP_RELEASE_TAG must be set when building a release.')
if any(character in RELEASE_TAG for character in '<>:"/\\|?*'):
    raise ValueError(f'APP_RELEASE_TAG contains invalid Windows filename characters: {RELEASE_TAG!r}')

APP_NAME = f'{BASE_APP_NAME}_{RELEASE_TAG}'
PROJECT_DIR = os.path.abspath(SPECPATH)

a = Analysis(
    [os.path.join(PROJECT_DIR, 'event_viewer.py')],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=[
        (os.path.join(PROJECT_DIR, 'data', 'rite'), 'data/rite'),
        (os.path.join(PROJECT_DIR, 'data', 'character'), 'data/character'),
    ],
    hiddenimports=[],
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
    name=APP_NAME,
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
    icon=[os.path.join(PROJECT_DIR, 'sultan.ico')],
)
