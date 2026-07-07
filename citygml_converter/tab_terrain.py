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


def create_tab_terrain(notebook):
    tab = ttkb.Frame(notebook, padding=28)
    tab.columnconfigure(0, weight=1)
    tab.rowconfigure(4, weight=1)

    dgm_file_list = []
    busy = [False]                    # verhindert re-entrante Läufe
    mesh_cache = {"key": None, "mesh": None}

    section_header(
        tab,
        "Gelände (DGM)",
        "Lädt amtliche Geländemodelle (DGM, XYZ/ASC-Kacheln) und kombiniert sie "
        "mit den CityGML-Gebäuden – als 3D-Vorschau und IFC-Export."
    ).grid(row=0, column=0, sticky="ew", pady=(0, 18))

    # ---- 1 · Download-Portal -------------------------------------------
    portal_row = ttkb.Frame(tab)
    portal_row.grid(row=1, column=0, sticky="ew", pady=(0, 16))
    ttkb.Label(portal_row, text="1 · DGM-Daten herunterladen",
               font=("Segoe UI Semibold", 13), foreground=INK)\
        .pack(side="left")

    state_var = tk.StringVar(value="Brandenburg")
    combo = ttkb.Combobox(portal_row, textvariable=state_var,
                          values=list(DGM_PORTALE.keys()),
                          state="readonly", width=24, font=("Segoe UI", 12))
    combo.pack(side="left", padx=(16, 8))

    def open_portal():
        url = DGM_PORTALE.get(state_var.get())
        if url:
            webbrowser.open_new_tab(url)
            print(f"[Gelände] Portal geöffnet: {state_var.get()}")

    ttkb.Button(portal_row, text="Portal öffnen", style="Grey.TButton",
                command=open_portal).pack(side="left")
    ttkb.Label(tab,
               text="Dort DGM1-Kacheln als XYZ- oder ASC-Datei herunterladen "
                    "(gzip .gz wird direkt unterstützt, ZIP bitte vorher entpacken).",
               font=("Segoe UI", 10), foreground=MUTED)\
        .grid(row=2, column=0, sticky="w", pady=(0, 14))

    # ---- 2 · Kachel-Liste ------------------------------------------------
    def add_paths(paths):
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
            if p in dgm_file_list:
                print(f"Übersprungen (bereits in der Liste): {os.path.basename(p)}")
                continue
            dgm_file_list.append(p)
            listbox.insert(tk.END, p)

    def add_files():
        paths = filedialog.askopenfilenames(filetypes=DGM_FILETYPES)
        if paths:
            add_paths(list(paths))

    def clear_files():
        dgm_file_list.clear()
        listbox.delete(0, tk.END)

    toolbar = ttkb.Frame(tab)
    toolbar.grid(row=3, column=0, sticky="ew", pady=(0, 8))
    ttkb.Label(toolbar, text="2 · DGM-Kacheln", font=("Segoe UI Semibold", 13),
               foreground=INK).pack(side="left")
    ttkb.Button(toolbar, text="Hinzufügen", style="Grey.TButton",
                command=add_files).pack(side="right")
    ttkb.Button(toolbar, text="Liste leeren", style="Grey.TButton",
                command=clear_files).pack(side="right", padx=(0, 8))

    list_frame = ttkb.Frame(tab)
    list_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 4))
    listbox = tk.Listbox(list_frame, height=5, activestyle="none",
                         borderwidth=1, relief="solid", highlightthickness=0,
                         font=("Segoe UI", 12))
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar = ttkb.Scrollbar(list_frame, bootstyle="round", command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scrollbar.set)
    enable_file_drop(listbox, add_paths)

    hint = ("Tipp: DGM-Kacheln direkt in die Liste ziehen." if dnd_ready()
            else "Kacheln über 'Hinzufügen' auswählen.")
    ttkb.Label(tab, text=hint, font=("Segoe UI", 10), foreground=MUTED)\
        .grid(row=5, column=0, sticky="w", pady=(0, 14))

    # ---- 3 · Gebäude-GML + 4 · IFC-Ausgabe -------------------------------
    gml_picker = FilePicker(
        tab, "3 · CityGML-Gebäude (für Zuschnitt & Kombination)",
        "Dateien durchsuchen...",
        lambda: filedialog.askopenfilename(filetypes=[("CityGML Dateien", "*.gml")])
    )
    gml_picker.grid(row=6, column=0, sticky="ew", pady=(0, 14))

    out_picker = FilePicker(
        tab, "4 · IFC-Ausgabedatei (Gelände + Gebäude)", "IFC4 Speicherort...",
        lambda: filedialog.asksaveasfilename(
            defaultextension=".ifc", filetypes=[("IFC4 Dateien", "*.ifc")])
    )
    out_picker.grid(row=7, column=0, sticky="ew", pady=(0, 18))

    # ---- Aktionen ---------------------------------------------------------
    def _log(*args):
        """Fortschritt sofort sichtbar machen (Konsole zeichnet erst bei update)."""
        print(*args)
        try:
            tab.update()
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

    def _run_guarded(fn):
        """Führt eine Aktion aus; blockiert Doppel-Klicks, deaktiviert die Buttons."""
        if busy[0]:
            print("Bitte warten – es läuft bereits eine Verarbeitung.")
            return
        busy[0] = True
        btn_export.configure(state="disabled")
        btn_preview.configure(state="disabled")
        try:
            fn()
        finally:
            busy[0] = False
            try:
                btn_export.configure(state="normal")
                btn_preview.configure(state="normal")
            except tk.TclError:
                pass

    def show_preview():
        import pyvista as pv
        import numpy as np

        gml_path = gml_picker.get()
        mesh = _prepare(gml_path)
        if mesh is None:
            return
        try:
            # Gemeinsamer Anzeige-Offset (VTK rechnet intern mit float32)
            offset = np.array(mesh.bounds[::2], dtype=np.float64)
            terrain_view = mesh.copy()
            terrain_view.points = terrain_view.points - offset

            plotter = pv.Plotter()
            plotter.add_mesh(terrain_view, color="#C9B896",
                             show_edges=False, style="surface")

            if gml_path:
                from citygml_converter.gml_preview import parse_gml_to_multiblock
                multi_block = parse_gml_to_multiblock(gml_path)
                for i in range(len(multi_block)):
                    block = multi_block[i]
                    if block is None or block.n_points == 0:
                        continue
                    block = block.triangulate()
                    block.points = block.points - offset
                    plotter.add_mesh(block, color="white",
                                     show_edges=False, style="surface")

            plotter.show_axes()
            plotter.add_text("Gelände + Gebäude" if gml_path else "Gelände",
                             position=(20, 20), font_size=10, color="black")
            plotter.show()
        except Exception as e:
            print("Fehler bei der Vorschau:", e)

    def export_ifc():
        gml_path = gml_picker.get()
        out_path = out_picker.get()
        if not gml_path:
            print("Fehler: Bitte CityGML-Gebäudedatei angeben (Feld 3)!")
            return
        if not out_path:
            print("Fehler: Bitte IFC-Ausgabedatei angeben (Feld 4)!")
            return
        mesh = _prepare(gml_path)
        if mesh is None:
            return
        try:
            vertices, faces = dgm.mesh_to_triangles(mesh)
            _log(f"Schreibe IFC ({len(faces):,} Gelände-Dreiecke) ...".replace(",", "."))
            convert_gml_to_ifc(gml_path, out_path, terrain=(vertices, faces))
        except Exception as e:
            print("Fehler beim IFC-Export:", e)

    btn_row = ttkb.Frame(tab)
    btn_row.grid(row=8, column=0, sticky="w")
    btn_export = ttkb.Button(btn_row, text="Als IFC exportieren", style="CTA.TButton",
                             command=lambda: _run_guarded(export_ifc))
    btn_export.pack(side="left")
    btn_preview = ttkb.Button(btn_row, text="Vorschau", style="Grey.TButton",
                              command=lambda: _run_guarded(show_preview))
    btn_preview.pack(side="left", padx=(10, 0))

    return tab
