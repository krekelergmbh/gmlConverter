import ttkbootstrap as ttkb
from tkinter import filedialog
import pyvista as pv
from citygml_converter.gml_preview import parse_gml_to_multiblock
from citygml_converter.ui import section_header, FilePicker


def create_tab_preview(notebook):
    tab = ttkb.Frame(notebook, padding=28)
    tab.columnconfigure(0, weight=1)

    mesh_data = [None]

    section_header(
        tab,
        "Preview",
        "Lädt eine CityGML-Datei und zeigt die Gebäude als interaktives 3D-Modell."
    ).grid(row=0, column=0, sticky="ew", pady=(0, 20))

    picker = FilePicker(
        tab, "CityGML-Datei", "Dateien durchsuchen...",
        lambda: filedialog.askopenfilename(filetypes=[("CityGML Dateien", "*.gml")])
    )
    picker.grid(row=1, column=0, sticky="ew", pady=(0, 22))

    def load_gml():
        path = picker.get()
        if not path:
            print("Fehler:", "Keine GML-Datei ausgewählt!")
            return
        try:
            multi_block = parse_gml_to_multiblock(path)
            mesh_data[0] = multi_block
            print("Erfolg:", "GML wurde geladen.")
            btn_preview.configure(style="CTA.TButton")
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

    btn_row = ttkb.Frame(tab)
    btn_row.grid(row=2, column=0, sticky="w")

    btn_load = ttkb.Button(btn_row, text="Laden", style="CTA.TButton", command=load_gml)
    btn_load.pack(side="left")

    btn_preview = ttkb.Button(btn_row, text="Vorschau", style="Grey.TButton", command=show_preview)
    btn_preview.pack(side="left", padx=(10, 0))

    return tab
