# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

block_cipher = None

excludes = [
    'onnx',
    'onnxruntime',
    'transformers',
    'tensorrt',
    'cupy',
]

datas = []
binaries = []
hiddenimports = ['logging', 'logging.handlers', 'pathlib', 'platform', 'threading', 'yaml']

extra_runtime_packages = [
    'yaml',
    'psutil',
    'numpy',
    'pandas',
    'pymcprotocol',
    'pymodbus',
    'pymysql',
    'tqdm',
    'pyqtgraph',
]

for package_name in extra_runtime_packages:
    package_datas, package_binaries, package_hiddenimports = collect_all(package_name)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

hiddenimports = sorted(set(hiddenimports))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name='DRB-OCR-AI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Đổi thành False nếu muốn ẩn console
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
    name='DRB-OCR-AI',
)
