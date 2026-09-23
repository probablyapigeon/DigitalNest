# Build from the repository root with: python -m PyInstaller DigitalNest.spec
from pathlib import Path

root = Path(SPECPATH)
analysis = Analysis(
    [str(root / 'desktop.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / 'web'), 'web'),
        (str(root / 'vendor' / 'lumina_core.xc'), 'vendor'),
        (str(root / 'vendor' / 'lonkworld' / 'LonkWorld.xc'), 'vendor/lonkworld'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz, analysis.scripts, [], exclude_binaries=True,
    name='DigitalNest', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False,
)
bundle = COLLECT(exe, analysis.binaries, analysis.datas, strip=False, upx=False, name='DigitalNest')
