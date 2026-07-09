# -*- mode: python ; coding: utf-8 -*-
# PyInstaller-Spec für gmlConverter (Windows + macOS).
# Build:  pyinstaller gmlConverter.spec --noconfirm
# Windows: EINE selbständige .exe (onefile, entpackt sich beim Start nach %TEMP%)
# macOS:   .app-Bundle (onedir, von Apple signiert/notarisiert)
import os
import re
import sys
from PyInstaller.utils.hooks import collect_all

with open("citygml_converter/__init__.py", encoding="utf-8") as _fh:
    APP_VERSION = re.search(r'__version__\s*=\s*"([^"]+)"', _fh.read()).group(1)

# Ressourcen (germany_bundeslaender.json, Logo, Icons) -> _MEIPASS/__files__
datas = [("citygml_converter/__files__", "__files__")]
binaries = []
hiddenimports = []

# Pakete mit Datendateien / kompilierten Modulen vollständig einsammeln
for pkg in ["ifcopenshell", "pyvista", "vtkmodules", "ttkbootstrap", "PIL", "shapely", "tkinterdnd2"]:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# Plattformabhängiges Icon (nur einsetzen, wenn vorhanden)
if sys.platform == "darwin":
    _icon_candidate = "citygml_converter/__files__/kgp.icns"
else:
    _icon_candidate = "citygml_converter/__files__/kgp.ico"
icon_file = _icon_candidate if os.path.exists(_icon_candidate) else None

a = Analysis(
    ["start.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    # macOS: onedir + .app-Bundle (für Signierung/Notarisierung nötig)
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="gmlConverter",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,            # GUI-App, keine Konsole
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon_file,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="gmlConverter",
    )

    app = BUNDLE(
        coll,
        name="gmlConverter.app",
        icon=icon_file,
        bundle_identifier="de.krekeler-architekten.gmlconverter",
        info_plist={
            "CFBundleName": "gmlConverter",
            "CFBundleDisplayName": "gmlConverter",
            "CFBundleShortVersionString": APP_VERSION,
            "NSHighResolutionCapable": True,
        },
    )
else:
    # Windows: EINE Datei – alles in der .exe, kein _internal-Ordner
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="gmlConverter",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,            # GUI-App, keine Konsole
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon_file,
    )
