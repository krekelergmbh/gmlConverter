import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

import ttkbootstrap as ttkb
from ttkbootstrap.constants import SUCCESS, INFO, BOTH, YES

# Startseite
from citygml_converter.readme import create_readme_tab
# Weitere Tabs
from citygml_converter.tab_z0 import create_tab_z0
from citygml_converter.tab_ifc import create_tab_ifc
from citygml_converter.tab_combine import create_tab_combine
from citygml_converter.tab_terrain import create_tab_terrain
from citygml_converter.tab_preview import create_tab_preview
from citygml_converter.tab_map import create_tab_map

# Splash-Funktion importieren
from citygml_converter.splash import show_splash

# Geteilte UI-Helfer
from citygml_converter import ui

# Optional: Drag & Drop (tkinterdnd2). Fällt sauber zurück, wenn nicht verfügbar.
try:
    from tkinterdnd2 import TkinterDnD
    _DND_IMPORTED = True
except Exception:
    _DND_IMPORTED = False

def resource_path(relative_path):
    """
    Gibt den absoluten Pfad zur Ressource zurück.
    Wenn die Anwendung gebündelt ist, wird sys._MEIPASS verwendet.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class TextRedirector:
    """Leitet sys.stdout und sys.stderr in ein ScrolledText-Widget um."""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, s):
        self.text_widget.insert("end", s)
        self.text_widget.see("end")

    def flush(self):
        pass

def _create_main_window(themename="journal"):
    """Erzeugt das Hauptfenster, möglichst mit Drag-&-Drop-Fähigkeit.

    Gibt (fenster, dnd_aktiv) zurück. Falls tkinterdnd2 nicht verfügbar ist
    oder nicht initialisiert werden kann, wird ein normales Fenster ohne
    Drag & Drop zurückgegeben – ohne Funktionsverlust.
    """
    if _DND_IMPORTED:
        win = None
        try:
            class _DnDWindow(ttkb.Window, TkinterDnD.DnDWrapper):
                pass
            win = _DnDWindow(themename=themename)
            win.TkdndVersion = TkinterDnD._require(win)
            return win, True
        except Exception as e:
            if win is not None:
                try:
                    win.destroy()
                except Exception:
                    pass
            print(f"Drag&Drop nicht verfügbar, nutze Standard-Fenster: {e}")
    return ttkb.Window(themename=themename), False


def main():
    """
    1) Unsichtbares tk.Tk() für den Splash
    2) show_splash(duration=10000) => Splash 10s
    3) root.destroy()
    4) ttkbootstrap.Window => Hauptfenster
    """
    # 1) Unsichtbares Root-Fenster
    root = tk.Tk()
    root.withdraw()

    # Splash 6 Sekunden
    show_splash(duration=6000)

    # 3) Root zerstören
    root.destroy()

    # 4) Hauptfenster (mit Drag-&-Drop-Fähigkeit, falls verfügbar)
    app, _dnd_active = _create_main_window("journal")
    ui.DND_ACTIVE = _dnd_active
    app.title("gmlConverter by mwo @ Krekeler Architekten Generalplaner GmbH")
    
    # Icon setzen (verwende resource_path, um kgp.ico zu laden)
    icon_path = resource_path(os.path.join("__files__", "kgp.ico"))
    try:
        app.iconbitmap(icon_path)
    except Exception as e:
        print(f"Fehler beim Setzen des Icons: {e}")

    # Beim Start maximiert/Vollbild öffnen (plattformübergreifend)
    try:
        app.state("zoomed")                     # Windows / die meisten Plattformen
    except Exception:
        try:
            app.attributes("-zoomed", True)     # Linux
        except Exception:
            app.geometry(f"{app.winfo_screenwidth()}x{app.winfo_screenheight()}+0+0")

    # Dein Style-Code
    style = ttkb.Style()
    style.configure(".", background="#FFFFFF")

    # Combobox-Dropdown-Liste: Font + Auswahl in Krekeler-Rot statt Theme-Orange
    app.option_add("*TCombobox*Listbox.font", ("Segoe UI", 13))
    app.option_add("*TCombobox*Listbox.selectBackground", "#892337")
    app.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")

    style.configure(
        "Krekeler.TButton",
        foreground="#FFFFFF",
        background="#892337",
        font=("Segoe UI", 14),
        borderwidth=0
    )
    style.map("Krekeler.TButton",
        background=[("hover", "#A23A48"), ("active", "#701F2A")],
        foreground=[("hover", "#FFFFFF"), ("active", "#FFFFFF")]
    )

    # Prominenter Haupt-Aktionsbutton (Call To Action)
    style.configure(
        "CTA.TButton",
        foreground="#FFFFFF",
        background="#892337",
        font=("Segoe UI Semibold", 16),
        borderwidth=0,
        padding=(26, 14)
    )
    style.map("CTA.TButton",
        background=[("hover", "#A23A48"), ("active", "#701F2A")],
        foreground=[("hover", "#FFFFFF"), ("active", "#FFFFFF")]
    )

    style.configure(
        "Grey.TButton",
        foreground="#666666",
        background="#DDDDDD",
        font=("Segoe UI", 14),
        borderwidth=0
    )
    style.map("Grey.TButton",
        background=[("hover", "#CCCCCC"), ("active", "#BBBBBB")],
        foreground=[("hover", "#666666"), ("active", "#666666")]
    )

    # Grauer Button in CTA-Groesse (fuer gleich grosse Button-Paare wie Laden/Vorschau)
    style.configure(
        "CTAGrey.TButton",
        foreground="#666666",
        background="#DDDDDD",
        font=("Segoe UI Semibold", 16),
        borderwidth=0,
        padding=(26, 14)
    )
    style.map("CTAGrey.TButton",
        background=[("hover", "#CCCCCC"), ("active", "#BBBBBB")],
        foreground=[("hover", "#666666"), ("active", "#666666")]
    )

    # Combobox: echte Feldhoehe ueber padding (kein ipady-Hintergrund),
    # Hover/Fokus-Rahmen in Krekeler-Rot statt Theme-Orange
    style.configure("Krekeler.TCombobox", padding=(10, 7))
    style.map("Krekeler.TCombobox",
        bordercolor=[("hover", "#892337"), ("focus", "#892337")],
        lightcolor=[("hover", "#892337"), ("focus", "#892337")],
        darkcolor=[("hover", "#892337"), ("focus", "#892337")]
    )

    style.configure("Minimal.TNotebook",
        background="#FFFFFF",
        borderwidth=0
    )
    style.configure("Minimal.TNotebook.Tab",
        foreground="#666666",
        background="#FFFFFF",
        font=("Segoe UI", 14),
        padding=(16, 10)
    )
    style.map("Minimal.TNotebook.Tab",
        foreground=[
            ("selected", "#000000"),
            ("!selected", "#666666")
        ],
        background=[
            ("selected", "#FFFFFF"),
            ("!selected", "#FFFFFF")
        ]
    )

    style.configure("FooterBrand.TLabel",
        foreground="#999999",
        background="#FFFFFF",
        font=("Segoe UI", 11, "italic")
    )

    # Frames + Notebook
    outer_frame = ttkb.Frame(app, style="TFrame", padding=10)
    outer_frame.pack(fill=BOTH, expand=True)

    # Dezenter Header
    header_frame = ttkb.Frame(outer_frame, style="TFrame")
    header_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))
    ttkb.Label(header_frame, text="gmlConverter",
               font=("Segoe UI Semibold", 22), foreground="#222222",
               background="#FFFFFF").pack(side=tk.LEFT)
    ttkb.Label(header_frame, text="CityGML-Werkzeuge",
               font=("Segoe UI", 13), foreground="#8A8A8A",
               background="#FFFFFF").pack(side=tk.LEFT, padx=(14, 0), pady=(9, 0))

    notebook_frame = ttkb.Frame(outer_frame, style="TFrame")
    notebook_frame.pack(side=tk.TOP, fill=BOTH, expand=True)

    notebook = ttkb.Notebook(notebook_frame, style="Minimal.TNotebook")
    notebook.pack(fill=BOTH, expand=True)

    # Tabs (README ganz ans Ende)
    tab_map = create_tab_map(notebook)
    notebook.add(tab_map, text="Pick GML")

    tab_z0 = create_tab_z0(notebook)
    notebook.add(tab_z0, text="z0 Converter")

    tab_ifc = create_tab_ifc(notebook)
    notebook.add(tab_ifc, text="GML2IFC")

    tab_combine = create_tab_combine(notebook)
    notebook.add(tab_combine, text="Merge GML")

    tab_terrain = create_tab_terrain(notebook)
    notebook.add(tab_terrain, text="Gelände (DGM)")

    tab_preview = create_tab_preview(notebook)
    notebook.add(tab_preview, text="Preview")

    tab_start = create_readme_tab(notebook, style)
    notebook.add(tab_start, text="README")

    # Console Frame
    console_frame = ttkb.Frame(outer_frame, style="TFrame")
    console_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False)

    console_frame.columnconfigure(0, weight=1)
    console_frame.columnconfigure(1, weight=1)
    console_frame.rowconfigure(0, weight=1)

    console_text = ScrolledText(console_frame, wrap="word", height=6)
    console_text.grid(row=0, column=0, columnspan=2, sticky="nsew")

    stdout_redirector = TextRedirector(console_text)
    stderr_redirector = TextRedirector(console_text)
    sys.stdout = stdout_redirector
    sys.stderr = stderr_redirector

    from citygml_converter import __version__
    version_label = ttkb.Label(
        console_frame,
        text=f"version {__version__}",
        style="FooterBrand.TLabel"
    )
    version_label.grid(row=1, column=0, sticky="w", pady=(5,0))

    brand_label = ttkb.Label(
        console_frame,
        text="Made in Brandenburg",
        style="FooterBrand.TLabel"
    )
    brand_label.grid(row=1, column=1, sticky="e", pady=(5,0))

    app.mainloop()

if __name__ == "__main__":
    main()
