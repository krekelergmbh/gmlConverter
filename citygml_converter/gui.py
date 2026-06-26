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
from citygml_converter.tab_preview import create_tab_preview
from citygml_converter.tab_map import create_tab_map

# Splash-Funktion importieren
from citygml_converter.splash import show_splash

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

    # 4) Hauptfenster
    app = ttkb.Window(themename="journal")
    app.title("gmlConverter by mwo @ Krekeler Architekten Generalplaner GmbH")
    
    # Icon setzen (verwende resource_path, um kgp.ico zu laden)
    icon_path = resource_path(os.path.join("__files__", "kgp.ico"))
    try:
        app.iconbitmap(icon_path)
    except Exception as e:
        print(f"Fehler beim Setzen des Icons: {e}")

    # Dein Style-Code
    style = ttkb.Style()
    style.configure(".", background="#FFFFFF")

    style.configure(
        "Krekeler.TButton",
        foreground="#FFFFFF",
        background="#892337",
        font=("Segoe UI", 12),
        borderwidth=0
    )
    style.map("Krekeler.TButton",
        background=[("hover", "#A23A48"), ("active", "#701F2A")],
        foreground=[("hover", "#FFFFFF"), ("active", "#FFFFFF")]
    )

    style.configure(
        "Grey.TButton",
        foreground="#666666",
        background="#DDDDDD",
        font=("Segoe UI", 12),
        borderwidth=0
    )
    style.map("Grey.TButton",
        background=[("hover", "#CCCCCC"), ("active", "#BBBBBB")],
        foreground=[("hover", "#666666"), ("active", "#666666")]
    )

    style.configure("Minimal.TNotebook",
        background="#FFFFFF",
        borderwidth=0
    )
    style.configure("Minimal.TNotebook.Tab",
        foreground="#666666",
        background="#FFFFFF",
        font=("Segoe UI", 12)
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
        font=("Segoe UI", 10, "italic")
    )

    # Frames + Notebook
    outer_frame = ttkb.Frame(app, style="TFrame", padding=10)
    outer_frame.pack(fill=BOTH, expand=True)

    notebook_frame = ttkb.Frame(outer_frame, style="TFrame")
    notebook_frame.pack(side=tk.TOP, fill=BOTH, expand=True)

    notebook = ttkb.Notebook(notebook_frame, style="Minimal.TNotebook")
    notebook.pack(fill=BOTH, expand=True)

    # Tabs
    tab_start = create_readme_tab(notebook, style)
    notebook.add(tab_start, text="README")

    tab_map = create_tab_map(notebook)
    notebook.add(tab_map, text="Pick GML")

    tab_z0 = create_tab_z0(notebook)
    notebook.add(tab_z0, text="z0 Converter")

    tab_ifc = create_tab_ifc(notebook)
    notebook.add(tab_ifc, text="GML2IFC")

    tab_combine = create_tab_combine(notebook)
    notebook.add(tab_combine, text="Merge GML")

    tab_preview = create_tab_preview(notebook)
    notebook.add(tab_preview, text="Preview")

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

    version_label = ttkb.Label(
        console_frame,
        text="version 1.0.0",
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
