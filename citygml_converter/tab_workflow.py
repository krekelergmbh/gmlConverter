"""Workflow-Assistent: führt Schritt für Schritt durch das Tool.

Für Nutzer, die die Einzel-Tabs nicht kennen: Daten wählen, Portale öffnen,
Dateien angeben, Optionen bestätigen – der Assistent führt Merge, z0,
Gelände-Verarbeitung und IFC-Export automatisch in der richtigen
Reihenfolge aus.
"""

import os
import tempfile
import webbrowser

import ttkbootstrap as ttkb
import tkinter as tk
from tkinter import filedialog

from citygml_converter.ui import (section_header, enable_file_drop, dnd_ready,
                                  MUTED, INK, BRAND)
from citygml_converter import dgm
from citygml_converter.tab_terrain import DGM_PORTALE, DGM_FILETYPES, add_tile_paths
from citygml_converter.tab_map import GML_PORTALE
from citygml_converter.combine import combine_gml_files
from citygml_converter.z0_converter import convert_gml_to_z0
from citygml_converter.gml_to_ifc import convert_gml_to_ifc

GML_FILETYPES = [("CityGML Dateien", "*.gml *.xml"), ("Alle Dateien", "*.*")]


def execute_workflow(gml_files, dgm_files, output_path,
                     gml_output="ifc", z0=False, log=print):
    """Führt den zusammengestellten Workflow aus (testbar, ohne GUI).

    gml_files:   Liste von CityGML-Dateien (mehrere werden automatisch vereint)
    dgm_files:   Liste von DGM-Kacheln
    output_path: Zieldatei (.ifc oder .gml, je nach gml_output/Daten)
    gml_output:  bei reinen GML-Workflows "ifc" oder "gml"
    z0:          bei GML-Ausgabe zusätzlich Höhen auf Null setzen

    Rückgabe: (verwendete_gml_datei_oder_None, gelaende_mesh_oder_None)
    """
    if not gml_files and not dgm_files:
        raise ValueError("Keine Eingabedaten angegeben.")

    # 1) Mehrere GML-Dateien automatisch vereinen
    gml_path = None
    if gml_files:
        if len(gml_files) == 1:
            gml_path = gml_files[0]
        else:
            log(f"Vereine {len(gml_files)} GML-Dateien ...")
            merged = os.path.join(tempfile.gettempdir(), "gmlconverter_workflow_merge.gml")
            combine_gml_files(gml_files, merged,
                              progress_callback=lambda c, t: None)
            gml_path = merged
            log("Vereint.")

    mesh = None

    # 2) Zielprodukt erzeugen
    if gml_files and dgm_files:
        log("Verarbeite Gelände und kombiniere mit den Gebäuden ...")
        mesh, _ = dgm.prepare_terrain(dgm_files, gml_path=gml_path, log=log)
        vertices, faces = dgm.mesh_to_triangles(mesh)
        convert_gml_to_ifc(gml_path, output_path, terrain=(vertices, faces))
    elif dgm_files:
        log("Verarbeite Gelände ...")
        mesh, _ = dgm.prepare_terrain(dgm_files, gml_path=None, log=log)
        vertices, faces = dgm.mesh_to_triangles(mesh)
        convert_gml_to_ifc(None, output_path, terrain=(vertices, faces))
    else:  # nur GML
        if gml_output == "ifc":
            log("Erzeuge IFC aus den Gebäuden ...")
            convert_gml_to_ifc(gml_path, output_path)
        else:
            if z0:
                log("Setze Höhen auf Null (z0) ...")
                convert_gml_to_z0(gml_path, output_path)
            elif len(gml_files) > 1:
                log("Schreibe vereinte GML-Datei ...")
                combine_gml_files(gml_files, output_path,
                                  progress_callback=lambda c, t: None)
            else:
                raise ValueError(
                    "Nichts zu tun: eine einzelne GML ohne z0 würde nur kopiert. "
                    "Bitte z0 wählen, mehrere Dateien angeben oder IFC erzeugen.")

    log(f"FERTIG: {output_path}")
    return gml_path, mesh


def create_tab_workflow(notebook):
    tab = ttkb.Frame(notebook, padding=28)
    tab.columnconfigure(0, weight=1)
    tab.rowconfigure(2, weight=1)

    # ----------------------------------------------------------- Zustand
    want_gml = tk.BooleanVar(value=True)
    want_dgm = tk.BooleanVar(value=False)
    land_var = tk.StringVar(value="Brandenburg")
    gml_files = []
    dgm_files = []
    gml_output = tk.StringVar(value="ifc")   # "ifc" | "gml"
    z0_var = tk.BooleanVar(value=False)
    preview_var = tk.BooleanVar(value=True)
    out_var = tk.StringVar(value="")
    busy = [False]
    current = [0]

    TITLES = {
        "daten": "Welche Daten benötigen Sie?",
        "portale": "Daten herunterladen",
        "gml": "Gebäude-Dateien angeben",
        "dgm": "Gelände-Kacheln angeben",
        "optionen": "Optionen",
        "fertig": "Zusammenfassung & Start",
    }

    def step_sequence():
        steps = ["daten", "portale"]
        if want_gml.get():
            steps.append("gml")
        if want_dgm.get():
            steps.append("dgm")
        steps += ["optionen", "fertig"]
        return steps

    # ----------------------------------------------------------- Rahmen
    section_header(
        tab,
        "Workflow",
        "Der Assistent führt Sie Schritt für Schritt von den Rohdaten zum "
        "fertigen Ergebnis – ohne Vorkenntnisse."
    ).grid(row=0, column=0, sticky="ew", pady=(0, 14))

    step_label = ttkb.Label(tab, text="", font=("Segoe UI Semibold", 14),
                            foreground=BRAND)
    step_label.grid(row=1, column=0, sticky="w", pady=(0, 12))

    content = ttkb.Frame(tab)
    content.grid(row=2, column=0, sticky="nsew")
    content.columnconfigure(0, weight=1)

    nav = ttkb.Frame(tab)
    nav.grid(row=3, column=0, sticky="ew", pady=(20, 0))

    # ------------------------------------------------------ Hilfsbausteine
    def _clear_content():
        for child in content.winfo_children():
            child.destroy()

    def _info(parent, text, row, pady=(0, 14)):
        ttkb.Label(parent, text=text, font=("Segoe UI", 13), foreground=INK,
                   wraplength=820, justify="left")\
            .grid(row=row, column=0, sticky="w", pady=pady)

    def _hint(parent, text, row, pady=(0, 14)):
        ttkb.Label(parent, text=text, font=("Segoe UI", 11), foreground=MUTED,
                   wraplength=820, justify="left")\
            .grid(row=row, column=0, sticky="w", pady=pady)

    def _file_list_section(parent, row, title, files, filetypes, hint_text):
        """Kachel-/Datei-Liste im einheitlichen Kopfzeilen-Muster."""
        header = ttkb.Frame(parent)
        header.grid(row=row, column=0, sticky="ew", pady=(0, 5))
        ttkb.Label(header, text=title, font=("Segoe UI Semibold", 13),
                   foreground=INK).pack(side="left")

        def add_dialog():
            paths = filedialog.askopenfilenames(filetypes=filetypes)
            if paths:
                add_tile_paths(list(paths), files, listbox)

        def clear_all():
            files.clear()
            listbox.delete(0, tk.END)

        ttkb.Button(header, text="Liste leeren", style="Grey.TButton",
                    command=clear_all).pack(side="right")
        ttkb.Button(header, text="Hinzufügen", style="Grey.TButton",
                    command=add_dialog).pack(side="right", padx=(0, 8))

        frame = ttkb.Frame(parent)
        frame.grid(row=row + 1, column=0, sticky="ew")
        listbox = tk.Listbox(frame, height=5, activestyle="none",
                             borderwidth=1, relief="solid", highlightthickness=0,
                             font=("Segoe UI", 13))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttkb.Scrollbar(frame, bootstyle="round", command=listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=sb.set)
        for p in files:
            listbox.insert(tk.END, p)
        enable_file_drop(listbox, lambda paths: add_tile_paths(paths, files, listbox))

        _hint(parent, hint_text, row + 2, pady=(5, 0))
        return listbox

    # ------------------------------------------------------------ Schritte
    def render_daten():
        _info(content, "Wählen Sie aus, welche Daten Sie verarbeiten möchten. "
                       "Beides zusammen ergibt ein kombiniertes 3D-Modell.", 0)
        cb1 = ttkb.Checkbutton(content, text="  Gebäude (GML) – amtliche 3D-Gebäudemodelle (LoD2)",
                               variable=want_gml, bootstyle="round-toggle")
        cb1.grid(row=1, column=0, sticky="w", pady=(0, 10))
        cb2 = ttkb.Checkbutton(content, text="  Gelände (DGM) – digitales Geländemodell (Erdoberfläche)",
                               variable=want_dgm, bootstyle="round-toggle")
        cb2.grid(row=2, column=0, sticky="w", pady=(0, 10))
        _hint(content, "Beispiele: nur Gebäude → IFC für die BIM-Planung; "
                       "Gebäude + Gelände → Gebäude stehen auf dem echten Gelände.", 3)

    def render_portale():
        _info(content, "Um welches Bundesland geht es? Öffnen Sie dann die "
                       "Download-Portale und laden Sie die Daten für Ihr "
                       "Gebiet herunter.", 0)

        row1 = ttkb.Frame(content)
        row1.grid(row=1, column=0, sticky="w", pady=(0, 16))
        combo = ttkb.Combobox(row1, textvariable=land_var,
                              values=list(DGM_PORTALE.keys()), state="readonly",
                              width=26, font=("Segoe UI", 13),
                              height=len(DGM_PORTALE), style="Krekeler.TCombobox")
        combo.pack(side="left")
        combo.configure(takefocus=False)
        combo.bind("<<ComboboxSelected>>",
                   lambda e: (combo.selection_clear(), tab.focus_set()))

        if want_gml.get():
            ttkb.Button(row1, text="Gebäude-Portal öffnen", style="Grey.TButton",
                        command=lambda: webbrowser.open_new_tab(
                            GML_PORTALE.get(land_var.get(), "")))\
                .pack(side="left", padx=(10, 0), fill="y")
        if want_dgm.get():
            ttkb.Button(row1, text="Gelände-Portal öffnen", style="Grey.TButton",
                        command=lambda: webbrowser.open_new_tab(
                            DGM_PORTALE.get(land_var.get(), "")))\
                .pack(side="left", padx=(10, 0), fill="y")

        steps_text = ("So geht's:\n"
                      "1. Portal öffnen und Ihr Gebiet suchen\n"
                      "2. Daten herunterladen"
                      + ("  –  Gebäude: CityGML-Datei (.gml oder .xml)" if want_gml.get() else "")
                      + ("  –  Gelände: DGM1-Kacheln (.xyz oder .asc)" if want_dgm.get() else "") + "\n"
                      "3. ZIP-Dateien entpacken\n"
                      "4. Unten auf 'Weiter' klicken und die Dateien angeben\n\n"
                      "Sie haben die Daten schon? Einfach direkt auf 'Weiter'.")
        ttkb.Label(content, text=steps_text, font=("Segoe UI", 12),
                   foreground=INK, justify="left")\
            .grid(row=2, column=0, sticky="w")

    def render_gml():
        _info(content, "Geben Sie Ihre CityGML-Gebäudedateien an.", 0)
        _file_list_section(
            content, 1, "Gebäude-Dateien (GML/XML)", gml_files, GML_FILETYPES,
            ("Dateien hierher ziehen oder über 'Hinzufügen' auswählen. "
             "Mehrere Dateien werden automatisch zu einer vereint."
             if dnd_ready() else
             "Dateien über 'Hinzufügen' auswählen. Mehrere Dateien werden "
             "automatisch zu einer vereint."))

    def render_dgm():
        _info(content, "Geben Sie Ihre DGM-Geländekacheln an.", 0)
        _file_list_section(
            content, 1, "Gelände-Kacheln (XYZ/ASC, auch .gz)", dgm_files, DGM_FILETYPES,
            ("Kacheln hierher ziehen oder über 'Hinzufügen' auswählen."
             if dnd_ready() else "Kacheln über 'Hinzufügen' auswählen.")
            + (" Das Gelände wird automatisch auf den Gebäudebereich zugeschnitten."
               if want_gml.get() else ""))

    def render_optionen():
        row = 0
        if want_gml.get() and want_dgm.get():
            _info(content, "Gebäude und Gelände werden zu EINEM IFC-Modell "
                           "kombiniert – die Gebäude stehen exakt auf dem "
                           "Gelände.", row); row += 1
        elif want_dgm.get():
            _info(content, "Aus den Gelände-Kacheln entsteht ein IFC-Modell "
                           "des Geländes.", row); row += 1
        else:
            _info(content, "Was soll aus den Gebäuden entstehen?", row); row += 1
            rb1 = ttkb.Radiobutton(content, text="  IFC-Modell (für BIM-Software, z. B. Revit/Archicad)",
                                   variable=gml_output, value="ifc")
            rb1.grid(row=row, column=0, sticky="w", pady=(0, 8)); row += 1
            rb2 = ttkb.Radiobutton(content, text="  Bearbeitete GML-Datei (vereint und/oder Höhen auf Null)",
                                   variable=gml_output, value="gml")
            rb2.grid(row=row, column=0, sticky="w", pady=(0, 12)); row += 1
            cb_z0 = ttkb.Checkbutton(content, text="  Höhen auf Null setzen (z0) – Gebäude beginnen bei Höhe 0",
                                     variable=z0_var, bootstyle="round-toggle")
            cb_z0.grid(row=row, column=0, sticky="w", pady=(0, 12)); row += 1
            _hint(content, "Hinweis: z0 wirkt nur bei der GML-Ausgabe. Beim "
                           "IFC-Modell wird der Ursprung ohnehin automatisch "
                           "lokal gesetzt.", row); row += 1

        ttkb.Checkbutton(content, text="  Nach Abschluss 3D-Vorschau anzeigen",
                         variable=preview_var, bootstyle="round-toggle")\
            .grid(row=row, column=0, sticky="w", pady=(6, 0))

    def _output_is_ifc():
        if want_dgm.get():
            return True
        return gml_output.get() == "ifc"

    def render_fertig():
        lines = []
        if want_gml.get():
            lines.append(f"• Gebäude: {len(gml_files)} Datei(en)"
                         + (" – werden vereint" if len(gml_files) > 1 else ""))
        if want_dgm.get():
            lines.append(f"• Gelände: {len(dgm_files)} Kachel(n)"
                         + (" – Zuschnitt auf Gebäudebereich" if want_gml.get() else ""))
        if want_gml.get() and want_dgm.get():
            lines.append("• Ergebnis: kombiniertes IFC-Modell (Gebäude + Gelände)")
        elif want_dgm.get():
            lines.append("• Ergebnis: IFC-Modell des Geländes")
        elif _output_is_ifc():
            lines.append("• Ergebnis: IFC-Modell der Gebäude")
        else:
            lines.append("• Ergebnis: bearbeitete GML-Datei"
                         + (" (Höhen auf Null)" if z0_var.get() else ""))
        if preview_var.get():
            lines.append("• Danach: 3D-Vorschau")

        _info(content, "Bitte prüfen:", 0, pady=(0, 8))
        ttkb.Label(content, text="\n".join(lines), font=("Segoe UI", 13),
                   foreground=INK, justify="left")\
            .grid(row=1, column=0, sticky="w", pady=(0, 18))

        # Speicherort (einheitliches Kopfzeilen-Muster)
        header = ttkb.Frame(content)
        header.grid(row=2, column=0, sticky="ew", pady=(0, 5))
        ttkb.Label(header, text="Speicherort des Ergebnisses",
                   font=("Segoe UI Semibold", 13), foreground=INK).pack(side="left")

        def choose_out():
            if _output_is_ifc():
                path = filedialog.asksaveasfilename(
                    defaultextension=".ifc", filetypes=[("IFC4 Dateien", "*.ifc")])
            else:
                path = filedialog.asksaveasfilename(
                    defaultextension=".gml", filetypes=[("CityGML Dateien", "*.gml")])
            if path:
                out_var.set(path)

        ttkb.Button(header, text="Durchsuchen", style="Grey.TButton",
                    command=choose_out).pack(side="right")

        entry = ttkb.Entry(content, textvariable=out_var, font=("Segoe UI", 13))
        entry.grid(row=3, column=0, sticky="ew", ipady=7)
        entry.configure(takefocus=False)
        entry.bind("<Button-1>", lambda e: choose_out())
        _hint(content, "Feld anklicken oder 'Durchsuchen', um den Speicherort zu wählen.", 4,
              pady=(5, 0))

    RENDERERS = {
        "daten": render_daten,
        "portale": render_portale,
        "gml": render_gml,
        "dgm": render_dgm,
        "optionen": render_optionen,
        "fertig": render_fertig,
    }

    # -------------------------------------------------------- Navigation
    def show_step(index):
        seq = step_sequence()
        index = max(0, min(index, len(seq) - 1))
        current[0] = index
        step = seq[index]
        step_label.configure(
            text=f"Schritt {index + 1} von {len(seq)} · {TITLES[step]}")
        _clear_content()
        RENDERERS[step]()
        btn_back.configure(state=("disabled" if index == 0 else "normal"))
        btn_next.configure(
            text=("Jetzt ausführen" if step == "fertig" else "Weiter"))

    def validate_step(step):
        if step == "daten" and not (want_gml.get() or want_dgm.get()):
            print("Bitte mindestens eine Datenart auswählen (Gebäude oder Gelände).")
            return False
        if step == "gml" and not gml_files:
            print("Bitte mindestens eine GML-Datei hinzufügen.")
            return False
        if step == "dgm" and not dgm_files:
            print("Bitte mindestens eine DGM-Kachel hinzufügen.")
            return False
        return True

    def go_back():
        if busy[0]:
            return
        show_step(current[0] - 1)

    def go_next():
        if busy[0]:
            return
        seq = step_sequence()
        step = seq[current[0]]
        if not validate_step(step):
            return
        if step == "fertig":
            run_workflow()
        else:
            show_step(current[0] + 1)

    # -------------------------------------------------------- Ausführung
    def _log(*args):
        print(*args)
        try:
            tab.update_idletasks()
        except tk.TclError:
            pass

    def _show_result_preview(gml_path, mesh):
        try:
            import numpy as np
            import pyvista as pv

            if mesh is None and not gml_path:
                return
            if mesh is not None:
                offset = np.array(mesh.bounds[::2], dtype=np.float64)
            else:
                from citygml_converter.gml_preview import parse_gml_to_multiblock
                mb_tmp = parse_gml_to_multiblock(gml_path)
                if mb_tmp.n_blocks == 0:
                    return
                offset = np.array(mb_tmp.bounds[::2], dtype=np.float64)

            plotter = pv.Plotter()
            if mesh is not None:
                view = mesh.copy(deep=True)
                view.points = view.points - offset
                plotter.add_mesh(view, color="#C9B896", show_edges=False,
                                 style="surface")
            if gml_path:
                from citygml_converter.gml_preview import parse_gml_to_multiblock
                mb = parse_gml_to_multiblock(gml_path)
                for i in range(len(mb)):
                    block = mb[i]
                    if block is None or block.n_points == 0:
                        continue
                    block = block.triangulate().copy(deep=True)
                    block.points = block.points - offset
                    plotter.add_mesh(block, color="white", show_edges=False,
                                     style="surface")
            plotter.show_axes()
            plotter.show()
        except Exception as e:
            print("Fehler bei der Vorschau:", e)

    def run_workflow():
        out = out_var.get().strip()
        if not out:
            print("Bitte zuerst einen Speicherort wählen.")
            return
        busy[0] = True
        btn_next.configure(state="disabled")
        btn_back.configure(state="disabled")
        try:
            used_gml, mesh = execute_workflow(
                gml_files=list(gml_files) if want_gml.get() else [],
                dgm_files=list(dgm_files) if want_dgm.get() else [],
                output_path=out,
                gml_output=gml_output.get(),
                z0=z0_var.get(),
                log=_log,
            )
            if preview_var.get():
                # GML-Ausgabe: das Ergebnis zeigen; sonst die verwendeten Gebäude
                preview_gml = out if (used_gml and not _output_is_ifc()) else used_gml
                _show_result_preview(preview_gml if want_gml.get() else None, mesh)
        except Exception as e:
            print("Fehler im Workflow:", e)
        finally:
            busy[0] = False
            try:
                btn_next.configure(state="normal")
                btn_back.configure(state="normal")
            except tk.TclError:
                pass

    btn_back = ttkb.Button(nav, text="Zurück", style="CTAGrey.TButton",
                           command=go_back)
    btn_back.pack(side="left")
    btn_next = ttkb.Button(nav, text="Weiter", style="CTA.TButton",
                           command=go_next)
    btn_next.pack(side="left", padx=(10, 0))

    show_step(0)
    return tab
