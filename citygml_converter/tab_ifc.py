import ttkbootstrap as ttkb
from tkinter import filedialog
from citygml_converter.gml_to_ifc import convert_gml_to_ifc
from citygml_converter.ui import section_header, FilePicker


def create_tab_ifc(notebook):
    tab = ttkb.Frame(notebook, padding=28)
    tab.columnconfigure(0, weight=1)

    section_header(
        tab,
        "GML2IFC",
        "Wandelt CityGML-Gebäude in das BIM-Format IFC4 um."
    ).grid(row=0, column=0, sticky="ew", pady=(0, 20))

    inp = FilePicker(
        tab, "1 · CityGML-Eingabedatei", "Dateien durchsuchen...",
        lambda: filedialog.askopenfilename(filetypes=[("CityGML Dateien", "*.gml *.xml")])
    )
    inp.grid(row=1, column=0, sticky="ew", pady=(0, 16))

    outp = FilePicker(
        tab, "2 · IFC4-Ausgabedatei (Speicherort)", "IFC4 Speicherort...",
        lambda: filedialog.asksaveasfilename(
            defaultextension=".ifc", filetypes=[("IFC4 Dateien", "*.ifc")])
    )
    outp.grid(row=2, column=0, sticky="ew", pady=(0, 22))

    def run_ifc():
        in_path = inp.get()
        out_path = outp.get()
        if not in_path:
            print("Fehler:", "Bitte GML-Datei angeben!")
            return
        if not out_path:
            print("Fehler:", "Bitte IFC-Datei angeben!")
            return
        try:
            convert_gml_to_ifc(in_path, out_path)
            print("Erfolg:", f"GML->IFC Konvertierung abgeschlossen:\n{out_path}")
        except Exception as e:
            print("Fehler:", str(e))

    ttkb.Button(tab, text="Konvertieren", command=run_ifc, style="CTA.TButton")\
        .grid(row=3, column=0, sticky="w")

    return tab
