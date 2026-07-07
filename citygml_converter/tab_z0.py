import ttkbootstrap as ttkb
from tkinter import filedialog
from citygml_converter.z0_converter import convert_gml_to_z0
from citygml_converter.ui import section_header, FilePicker


def create_tab_z0(notebook):
    tab = ttkb.Frame(notebook, padding=28)
    tab.columnconfigure(0, weight=1)

    section_header(
        tab,
        "z0 Converter",
        "Verschiebt alle Z-Koordinaten, sodass das Gebäude auf Höhe Z = 0 liegt."
    ).grid(row=0, column=0, sticky="ew", pady=(0, 20))

    inp = FilePicker(
        tab, "1 · CityGML-Eingabedatei", "Dateien durchsuchen...",
        lambda: filedialog.askopenfilename(filetypes=[("CityGML Dateien", "*.gml *.xml")])
    )
    inp.grid(row=1, column=0, sticky="ew", pady=(0, 16))

    outp = FilePicker(
        tab, "2 · Ausgabedatei (Speicherort)", "Speicherort...",
        lambda: filedialog.asksaveasfilename(
            defaultextension=".gml", filetypes=[("CityGML Dateien", "*.gml")])
    )
    outp.grid(row=2, column=0, sticky="ew", pady=(0, 22))

    def run_z0():
        in_path = inp.get()
        out_path = outp.get()
        if not in_path:
            print("Fehler", "Bitte GML-Datei angeben!")
            return
        if not out_path:
            print("Fehler", "Bitte Ausgabedatei angeben!")
            return
        try:
            convert_gml_to_z0(in_path, out_path)
            print("Erfolg", f"Z=0-Konvertierung abgeschlossen:\n{out_path}")
        except Exception as e:
            print("Fehler", str(e))

    ttkb.Button(tab, text="Konvertieren", command=run_z0, style="CTA.TButton")\
        .grid(row=3, column=0, sticky="w")

    return tab
