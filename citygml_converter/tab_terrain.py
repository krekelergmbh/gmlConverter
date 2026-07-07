import os
import webbrowser

import ttkbootstrap as ttkb
import tkinter as tk
from tkinter import filedialog

from citygml_converter.ui import (section_header, FilePicker, enable_file_drop,
                                  dnd_ready, MUTED, INK)
from citygml_converter import dgm
from citygml_converter.gml_to_ifc import convert_gml_to_ifc

# Verifizierte DGM-Download-Portale der Bundesländer (Stand 06/2026)
DGM_PORTALE = {
    "Baden-Württemberg": "https://opengeodata.lgl-bw.de/#/(sidenav:product/dgm)",
    "Bayern": "https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=dgm1",
    "Berlin": "https://gdi.berlin.de/geonetwork/srv/ger/catalog.search#/metadata/fa02f9e1-a0df-3be1-b0aa-bc624c0c7ff5",
    "Brandenburg": "https://data.geobasis-bb.de/geobasis/daten/dgm/",
    "Bremen": "https://metaver.de/trefferanzeige?docuuid=2351ABA6-019D-4155-853F-76EEFC26CA52",
    "Hamburg": "https://suche.transparenz.hamburg.de/dataset/digitales-hohenmodell-hamburg-dgm-1",
    "Hessen": "https://gds.hessen.de/INTERSHOP/web/WFS/HLBG-Geodaten-Site/de_DE/-/EUR/ViewDownloadcenter-Start?path=3D-Daten/Digitale%20Gel%C3%A4ndemodelle%20(DGM1)",
    "Mecklenburg-Vorpommern": "https://laiv.geodaten-mv.de/afgvk/Geotopographie/Download?produkt=DGM",
    "Niedersachsen": "https://ni-lgln-opengeodata.hub.arcgis.com/",
    "Nordrhein-Westfalen": "https://www.opengeodata.nrw.de/produkte/geobasis/hm/",
    "Rheinland-Pfalz": "https://geoshop.rlp.de/opendata-dgm1.html",
    "Saarland": "https://geoportal.saarland.de/article/Themen_Hoehe/",
    "Sachsen": "https://www.geodaten.sachsen.de/downloadbereich-digitale-hoehenmodelle-4851.html",
    "Sachsen-Anhalt": "https://www.lvermgeo.sachsen-anhalt.de/de/gdp-download-dgm.html",
    "Schleswig-Holstein": "https://geodaten.schleswig-holstein.de/gaialight-sh/_apps/dladownload/dl-dgm1.html",
    "Thüringen": "https://geoportal.thueringen.de/gdi-th/download-offene-geodaten/download-hoehendaten",
}

DGM_FILETYPES = [
    ("DGM Dateien", "*.xyz *.txt *.csv *.asc *.gz"),
    ("Alle Dateien", "*.*"),
]


def _file_sig(path):
    """Signatur einer Datei für den Mesh-Cache (Pfad + Größe + Änderungszeit)."""
    try:
        st = os.stat(path)
        return (path, st.st_size, st.st_mtime_ns)
    except OSError:
        return (path, -1, -1)


def add_tile_paths(paths, tile_list, listbox):
    """Fügt DGM-Kachel-Pfade validiert in Liste + Listbox ein (geteilt mit Preview)."""
    for p in paths:
        if not p:
            continue
        if os.path.isdir(p):
            print(f"Übersprungen (Ordner): {p} – bitte die Kachel-Dateien "
                  f"selbst hinzufügen.")
            continue
        if p.lower().endswith(".zip"):
            print(f"Übersprungen (ZIP): {os.path.basename(p)} – bitte erst "
                  f"entpacken, dann die XYZ-/ASC-Dateien hinzufügen.")
            continue
        if p in tile_list:
            print(f"Übersprungen (bereits in der Liste): {os.path.basename(p)}")
            continue
        tile_list.append(p)
        listbox.insert(tk.END, p)


def create_tab_terrain(notebook):
    tab = ttkb.Frame(notebook, padding=28)
    tab.columnconfigure(0, weight=1)

    dgm_file_list = []
    busy = [False]                    # verhindert re-entrante Läufe
    mesh_cache = {"key": None, "mesh": None}

    section_header(
        tab,
        "Gelände (DGM)",
        "Erzeugt aus amtlichen Geländemodellen (DGM) eine IFC – wahlweise "
        "kombiniert mit den CityGML-Gebäuden oder als reines Gelände. "
        "Die 3D-Ansicht finden Sie im Tab 'Preview'."
    ).grid(row=0, column=0, sticky="ew", pady=(0, 20))

    # ---- 1 · Download-Portal (Aufbau wie FilePicker: Label / Zeile / Hinweis)
    ttkb.Label(tab, text="1 · DGM-Daten herunterladen",
               font=("Segoe UI Semibold", 13), foreground=INK)\
        .grid(row=1, column=0, sticky="w", pady=(0, 5))

    portal_row = ttkb.Frame(tab)
    portal_row.grid(row=2, column=0, sticky="w")
    state_var = tk.StringVar(value="Brandenburg")
    combo = ttkb.Combobox(portal_row, textvariable=state_var,
                          values=list(DGM_PORTALE.keys()),
                          state="readonly", width=26, font=("Segoe UI", 13),
                          height=len(DGM_PORTALE),  # alle 16 ohne Scrollbalken
                          style="Krekeler.TCombobox")
    combo.pack(side="left")
    # Kein dauerhafter Fokusrahmen: nicht per Tab fokussierbar, und nach
    # einer Auswahl Markierung + Fokus wieder abgeben
    combo.configure(takefocus=False)

    def _on_state_selected(_event):
        combo.selection_clear()
        tab.focus_set()

    combo.bind("<<ComboboxSelected>>", _on_state_selected)

    def open_portal():
        url = DGM_PORTALE.get(state_var.get())
        if url:
            webbrowser.open_new_tab(url)
            print(f"[Gelände] Portal geöffnet: {state_var.get()}")

    # fill="y": Button exakt so hoch wie die Combobox -> buendige Oberkanten
    ttkb.Button(portal_row, text="Portal öffnen", style="Grey.TButton",
                command=open_portal).pack(side="left", padx=(10, 0), fill="y")
    ttkb.Label(tab,
               text="DGM1-Kacheln als XYZ- oder ASC-Datei herunterladen "
                    "(gzip .gz wird direkt unterstützt, ZIP bitte vorher entpacken).",
               font=("Segoe UI", 10), foreground=MUTED)\
        .grid(row=3, column=0, sticky="w", pady=(5, 16))

    # ---- 2 · Kachel-Liste ------------------------------------------------
    def add_files():
        paths = filedialog.askopenfilenames(filetypes=DGM_FILETYPES)
        if paths:
            add_tile_paths(list(paths), dgm_file_list, listbox)

    def clear_files():
        dgm_file_list.clear()
        listbox.delete(0, tk.END)

    # Kopfzeile wie beim Pfadfeld: Label links, Buttons rechts, Liste volle Breite
    header2 = ttkb.Frame(tab)
    header2.grid(row=4, column=0, sticky="ew", pady=(0, 5))
    ttkb.Label(header2, text="2 · DGM-Kacheln", font=("Segoe UI Semibold", 13),
               foreground=INK).pack(side="left")
    ttkb.Button(header2, text="Liste leeren", style="Grey.TButton",
                command=clear_files).pack(side="right")
    ttkb.Button(header2, text="Hinzufügen", style="Grey.TButton",
                command=add_files).pack(side="right", padx=(0, 8))

    list_frame = ttkb.Frame(tab)
    list_frame.grid(row=5, column=0, sticky="ew")
    listbox = tk.Listbox(list_frame, height=5, activestyle="none",
                         borderwidth=1, relief="solid", highlightthickness=0,
                         font=("Segoe UI", 13))
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar = ttkb.Scrollbar(list_frame, bootstyle="round", command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scrollbar.set)
    enable_file_drop(listbox, lambda paths: add_tile_paths(paths, dgm_file_list, listbox))

    hint = ("DGM-Kacheln hierher ziehen oder über 'Hinzufügen' auswählen."
            if dnd_ready() else "Kacheln über 'Hinzufügen' auswählen.")
    ttkb.Label(tab, text=hint, font=("Segoe UI", 10), foreground=MUTED)\
        .grid(row=6, column=0, sticky="w", pady=(5, 16))

    # ---- 3 · Gebäude-GML (optional) + 4 · IFC-Ausgabe --------------------
    gml_picker = FilePicker(
        tab, "3 · CityGML-Gebäude (optional – leer lassen für reines Gelände)",
        "Dateien durchsuchen...",
        lambda: filedialog.askopenfilename(
            filetypes=[("CityGML Dateien", "*.gml *.xml")]),
        clearable=True
    )
    gml_picker.grid(row=7, column=0, sticky="ew", pady=(0, 16))

    out_picker = FilePicker(
        tab, "4 · IFC-Ausgabedatei", "IFC4 Speicherort...",
        lambda: filedialog.asksaveasfilename(
            defaultextension=".ifc", filetypes=[("IFC4 Dateien", "*.ifc")])
    )
    out_picker.grid(row=8, column=0, sticky="ew", pady=(0, 22))

    # ---- Aktion -----------------------------------------------------------
    def _log(*args):
        """Fortschritt sofort sichtbar machen. update_idletasks() zeichnet die
        Konsole neu, verarbeitet aber KEINE Klicks – verhindert verschachtelte
        Aktionen (auch aus anderen Tabs) während der Verarbeitung."""
        print(*args)
        try:
            tab.update_idletasks()
        except tk.TclError:
            pass

    def _prepare(gml_path):
        if not dgm_file_list:
            print("Fehler: Keine DGM-Kacheln in der Liste!")
            return None
        cache_key = (tuple(_file_sig(p) for p in dgm_file_list),
                     _file_sig(gml_path) if gml_path else None)
        if mesh_cache["key"] == cache_key and mesh_cache["mesh"] is not None:
            print("Verwende bereits berechnetes Geländemesh (unveränderte Eingaben).")
            return mesh_cache["mesh"]
        try:
            mesh, _ = dgm.prepare_terrain(
                dgm_file_list, gml_path=gml_path or None, log=_log)
            mesh_cache["key"] = cache_key
            mesh_cache["mesh"] = mesh
            return mesh
        except Exception as e:
            print("Fehler bei der DGM-Verarbeitung:", e)
            return None

    def export_ifc():
        if busy[0]:
            print("Bitte warten – es läuft bereits eine Verarbeitung.")
            return
        gml_path = gml_picker.get()
        out_path = out_picker.get()
        if not out_path:
            print("Fehler: Bitte IFC-Ausgabedatei angeben (Feld 4)!")
            return
        busy[0] = True
        btn_export.configure(state="disabled")
        try:
            mesh = _prepare(gml_path)
            if mesh is None:
                return
            vertices, faces = dgm.mesh_to_triangles(mesh)
            if gml_path:
                _log(f"Schreibe IFC: Gebäude + Gelände "
                     f"({len(faces):,} Dreiecke) ...".replace(",", "."))
            else:
                _log(f"Schreibe IFC: reines Gelände "
                     f"({len(faces):,} Dreiecke) ...".replace(",", "."))
            convert_gml_to_ifc(gml_path or None, out_path,
                               terrain=(vertices, faces))
        except Exception as e:
            print("Fehler beim IFC-Export:", e)
        finally:
            busy[0] = False
            try:
                btn_export.configure(state="normal")
            except tk.TclError:
                pass

    btn_export = ttkb.Button(tab, text="Als IFC exportieren", style="CTA.TButton",
                             command=export_ifc)
    btn_export.grid(row=9, column=0, sticky="w")

    return tab
