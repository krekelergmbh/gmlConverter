import ttkbootstrap as ttkb
import tkinter as tk
from tkinter import filedialog
import pyvista as pv
from citygml_converter.gml_preview import parse_gml_to_multiblock
from citygml_converter.ui import (section_header, FilePicker, enable_file_drop,
                                  dnd_ready, MUTED, INK)
from citygml_converter import dgm
from citygml_converter.tab_terrain import add_tile_paths, DGM_FILETYPES


def create_tab_preview(notebook):
    tab = ttkb.Frame(notebook, padding=28)
    tab.columnconfigure(0, weight=1)

    mesh_data = [None]      # Gebäude (pv.MultiBlock)
    terrain_data = [None]   # Gelände (pv.PolyData)
    dgm_file_list = []
    busy = [False]

    section_header(
        tab,
        "Preview",
        "Zeigt CityGML-Gebäude und/oder DGM-Gelände als interaktives 3D-Modell – "
        "einzeln oder kombiniert."
    ).grid(row=0, column=0, sticky="ew", pady=(0, 20))

    picker = FilePicker(
        tab, "CityGML-Gebäude (optional)", "Dateien durchsuchen...",
        lambda: filedialog.askopenfilename(filetypes=[("CityGML Dateien", "*.gml")])
    )
    picker.grid(row=1, column=0, sticky="ew", pady=(0, 16))

    # ---- DGM-Kacheln (optional) ------------------------------------------
    def add_files():
        paths = filedialog.askopenfilenames(filetypes=DGM_FILETYPES)
        if paths:
            add_tile_paths(list(paths), dgm_file_list, listbox)

    def clear_files():
        dgm_file_list.clear()
        listbox.delete(0, tk.END)

    toolbar = ttkb.Frame(tab)
    toolbar.grid(row=2, column=0, sticky="ew", pady=(0, 8))
    ttkb.Label(toolbar, text="DGM-Kacheln (optional)",
               font=("Segoe UI Semibold", 13), foreground=INK).pack(side="left")
    ttkb.Button(toolbar, text="Hinzufügen", style="Grey.TButton",
                command=add_files).pack(side="right")
    ttkb.Button(toolbar, text="Liste leeren", style="Grey.TButton",
                command=clear_files).pack(side="right", padx=(0, 8))

    list_frame = ttkb.Frame(tab)
    list_frame.grid(row=3, column=0, sticky="ew")
    listbox = tk.Listbox(list_frame, height=4, activestyle="none",
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
        .grid(row=4, column=0, sticky="w", pady=(5, 22))

    # ---- Aktionen ----------------------------------------------------------
    def _log(*args):
        """Konsole live neu zeichnen, ohne Klick-Events zu verarbeiten."""
        print(*args)
        try:
            tab.update_idletasks()
        except tk.TclError:
            pass

    def load_data():
        if busy[0]:
            print("Bitte warten – es läuft bereits eine Verarbeitung.")
            return
        gml_path = picker.get()
        if not gml_path and not dgm_file_list:
            print("Fehler: Bitte GML-Datei und/oder DGM-Kacheln angeben!")
            return
        busy[0] = True
        btn_load.configure(state="disabled")
        btn_preview.configure(state="disabled")
        try:
            mesh_data[0] = None
            terrain_data[0] = None
            if gml_path:
                mesh_data[0] = parse_gml_to_multiblock(gml_path)
                print("Erfolg:", "GML wurde geladen.")
            if dgm_file_list:
                mesh, _ = dgm.prepare_terrain(
                    dgm_file_list, gml_path=gml_path or None, log=_log)
                terrain_data[0] = mesh
                print("Erfolg:", "Gelände wurde geladen.")
        except Exception as e:
            print("Fehler beim Laden:", e)
        finally:
            busy[0] = False
            try:
                btn_load.configure(state="normal")
                btn_preview.configure(state="normal")
            except tk.TclError:
                pass

    def show_preview():
        import numpy as np

        if busy[0]:
            print("Bitte warten – es läuft bereits eine Verarbeitung.")
            return
        if mesh_data[0] is None and terrain_data[0] is None:
            print("Fehler:", "Nichts geladen. Bitte zuerst 'Laden' klicken!")
            return
        try:
            # Gemeinsamer Anzeige-Offset (VTK rechnet intern mit float32)
            if terrain_data[0] is not None:
                offset = np.array(terrain_data[0].bounds[::2], dtype=np.float64)
            else:
                offset = np.array(mesh_data[0].bounds[::2], dtype=np.float64)

            plotter = pv.Plotter()
            n_shown = 0

            if terrain_data[0] is not None:
                terrain_view = terrain_data[0].copy(deep=True)
                terrain_view.points = terrain_view.points - offset
                plotter.add_mesh(terrain_view, color="#C9B896",
                                 show_edges=False, style="surface")
                n_shown += 1

            if mesh_data[0] is not None:
                multi_block = mesh_data[0]
                if multi_block.n_blocks == 0 and n_shown == 0:
                    print("Leerer MultiBlock, nichts zu plotten.")
                    return
                for i in range(len(multi_block)):
                    block = multi_block[i]
                    if block is None or block.n_points == 0:
                        continue
                    # deep copy: triangulate() kann den Punktspeicher mit dem
                    # Original teilen – sonst verschiebt jeder Klick erneut
                    block = block.triangulate().copy(deep=True)
                    block.points = block.points - offset
                    plotter.add_mesh(block, color="white", show_edges=False,
                                     style="surface")
                    n_shown += 1

            if n_shown == 0:
                print("Keine darstellbare Geometrie gefunden.")
                return

            plotter.show_axes()

            plotter.add_text("Views", position=(20, 110), font_size=10, color='black')

            def top_view_callback(_checked):
                plotter.view_xy()
                plotter.reset_camera()

            def front_view_callback(_checked):
                plotter.view_xz()
                plotter.reset_camera()

            def iso_view_callback(_checked):
                plotter.view_isometric()
                plotter.reset_camera()

            widget_top = plotter.add_checkbox_button_widget(
                callback=top_view_callback,
                value=False,
                position=(20, 80),
                size=20,
                border_size=2,
                background_color="black",
                color_on="white",
                color_off="white"
            )
            plotter.add_text("Top View", position=(55, 80), font_size=8, color='black')

            widget_front = plotter.add_checkbox_button_widget(
                callback=front_view_callback,
                value=False,
                position=(20, 50),
                size=20,
                border_size=2,
                background_color="black",
                color_on="white",
                color_off="white"
            )
            plotter.add_text("Front View", position=(55, 50), font_size=8, color='black')

            widget_iso = plotter.add_checkbox_button_widget(
                callback=iso_view_callback,
                value=False,
                position=(20, 20),
                size=20,
                border_size=2,
                background_color="black",
                color_on="white",
                color_off="white"
            )
            plotter.add_text("Isometric", position=(55, 20), font_size=8, color='black')

            plotter.add_text("Shortcuts", position=(200, 110), font_size=10, color='black')
            shortcuts_text = (
                "V  =  Reset View\n"
                "W  =  Wireframe\n"
                "S  =  Solid"
            )
            plotter.add_text(shortcuts_text, position=(200, 20), font_size=8, color='black')

            plotter.show()

        except Exception as e:
            print("Fehler beim Anzeigen der Vorschau:", e)

    btn_row = ttkb.Frame(tab)
    btn_row.grid(row=5, column=0, sticky="w")

    btn_load = ttkb.Button(btn_row, text="Laden", style="CTA.TButton", command=load_data)
    btn_load.pack(side="left")

    btn_preview = ttkb.Button(btn_row, text="Vorschau", style="Grey.TButton", command=show_preview)
    btn_preview.pack(side="left", padx=(10, 0))

    return tab
