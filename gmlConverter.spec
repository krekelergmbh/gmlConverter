# -*- mode: python ; coding: utf-8 -*-
# PyInstaller-Spec für gmlConverter (Windows + macOS).
# Build:  pyinstaller gmlConverter.spec --noconfirm
import os
import sys
from PyInstaller.utils.hooks import collect_all

# Ressourcen (germany_bundeslaender.json, Logo, Icons) -> _MEIPASS/__files__
datas = [("citygml_converter/__files__", "__files__")]
binaries = []
hiddenimports = []

# Pakete mit Datendateien / kompilierten Modulen vollständig einsammeln
for pkg in ["ifcopenshell", "pyvista", "vtkmodules", "ttkbootstrap", "PIL", "shapely"]:
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

# macOS: zusätzlich ein .app-Bundle erzeugen
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="gmlConverter.app",
        icon=icon_file,
        bundle_identifier="de.krekeler-architekten.gmlconverter",
        info_plist={
            "CFBundleName": "gmlConverter",
            "CFBundleDisplayName": "gmlConverter",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
        },
    )
