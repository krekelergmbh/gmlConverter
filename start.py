"""Einstiegspunkt für gmlConverter.

Liegt eine Ebene über dem Paket `citygml_converter`, damit die
absoluten Paket-Importe (from citygml_converter... ) funktionieren –
sowohl beim direkten Start (python start.py) als auch im PyInstaller-Build.
"""

from citygml_converter.gui import main

if __name__ == "__main__":
    main()
