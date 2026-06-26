import ttkbootstrap as ttkb
from ttkbootstrap.constants import SUCCESS
import tkinter as tk
from tkinter import filedialog
import pyvista as pv
from citygml_converter.gml_preview import parse_gml_to_multiblock

def create_tab_preview(notebook):
    tab_preview = ttkb.Frame(notebook)
    tab_preview.columnconfigure(0, weight=0)
    tab_preview.columnconfigure(1, weight=1)

    gml_path_var = tk.StringVar(value="Dateien durchsuchen...")
    mesh_data = [None]

    def select_gml_file(event):
        path = filedialog.askopenfilename(filetypes=[("CityGML Dateien", "*.gml")])
        if path:
            gml_path_var.set(path)
            print("[Preview] GML-Datei ausgewählt:", path)

    def load_gml():
        path = gml_path_var.get()
        if path == "Dateien durchsuchen..." or not path:
            print("Fehler:", "Keine GML-Datei ausgewählt!")
            return
        try:
            multi_block = parse_gml_to_multiblock(path)
            mesh_data[0] = multi_block
            print("Erfolg:", "GML wurde geladen.")
            btn_preview.configure(style="Krekeler.TButton")
        except Exception as e:
            print("Fehler beim Laden der GML:", e)

    def show_preview():
        if mesh_data[0] is None:
            print("Fehler:", "Keine GML geladen. Bitte zuerst 'Laden' klicken!")
            return
        try:
            plotter = pv.Plotter()  # keine spezielle Fenstergröße, kein Vollbild
            multi_block = mesh_data[0]
            if multi_block.n_blocks == 0:
                print("Leerer MultiBlock, nichts zu plotten.")
                return

            for i in range(len(multi_block)):
                block = multi_block[i]
                if block is None or block.n_points == 0:
                    continue
                block = block.triangulate()
                plotter.add_mesh(block, color="white", show_edges=False, style="surface")

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

    entry_gml = ttkb.Entry(tab_preview, textvariable=gml_path_var, width=50)
    entry_gml.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
    entry_gml.configure(takefocus=False)

    def on_entry_click(event):
        select_gml_file(event)
    entry_gml.bind("<Button-1>", on_entry_click)

    btn_load = ttkb.Button(
        tab_preview,
        text="Laden",
        style="Krekeler.TButton",
        command=load_gml
    )
    btn_load.grid(row=1, column=0, padx=5, pady=5, sticky="w")

    btn_preview = ttkb.Button(
        tab_preview,
        text="Vorschau",
        style="Grey.TButton",
        command=show_preview
    )
    btn_preview.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    return tab_preview
