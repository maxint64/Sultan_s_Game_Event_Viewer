# -*- mode: python ; coding: utf-8 -*-
import os
import shutil
from datetime import datetime

import PyInstaller.config

# 输出 exe 到 spec 文件所在目录的上级（即主文件夹），build 缓存留在 code/ 下
APP_NAME = '苏丹的游戏事件查看器(GitHub：AC-HUB-AC)'
PROJECT_DIR = os.path.abspath(os.path.join(SPECPATH, '..'))
BACKUP_DIR = os.path.join(PROJECT_DIR, 'releases', 'backup')
PyInstaller.config.CONF['distpath'] = PROJECT_DIR
PyInstaller.config.CONF['workpath'] = os.path.join(SPECPATH, 'build')
os.makedirs(PyInstaller.config.CONF['workpath'], exist_ok=True)


def backup_existing_executable():
    """构建前备份现有 exe，避免 --noconfirm 直接覆盖后无法恢复。"""
    executable = os.path.join(PROJECT_DIR, f"{APP_NAME}.exe")
    if not os.path.isfile(executable):
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')[:-3]
    backup = os.path.join(BACKUP_DIR, f"{APP_NAME}_{timestamp}.exe")
    suffix = 1
    while os.path.exists(backup):
        backup = os.path.join(
            BACKUP_DIR, f"{APP_NAME}_{timestamp}_{suffix}.exe"
        )
        suffix += 1

    shutil.copy2(executable, backup)
    print("Existing executable backed up before build.")


backup_existing_executable()

a = Analysis(
    [os.path.join(SPECPATH, '苏丹的游戏事件查看器.py')],
    pathex=[SPECPATH],
    binaries=[],
    datas=[
        (os.path.join(SPECPATH, 'rite'), 'rite'),
        (os.path.join(SPECPATH, 'character'), 'character'),
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
    version=os.path.join(SPECPATH, 'version.txt'),
    icon=[os.path.join(SPECPATH, '图标.ico')],
)
