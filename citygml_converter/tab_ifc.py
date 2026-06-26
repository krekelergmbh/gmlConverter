import ttkbootstrap as ttkb
from ttkbootstrap.constants import SUCCESS
import tkinter as tk
from tkinter import filedialog
from citygml_converter.gml_to_ifc import convert_gml_to_ifc

def create_tab_ifc(notebook):
    tab_ifc = ttkb.Frame(notebook)
    tab_ifc.columnconfigure(0, weight=1)
    tab_ifc.columnconfigure(1, weight=0)

    entry_input_ifc = ttkb.Entry(tab_ifc, width=50)
    entry_input_ifc.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    entry_input_ifc.insert(0, "Dateien durchsuchen...")
    entry_input_ifc.configure(takefocus=False)

    def select_input_path(event):
        path = filedialog.askopenfilename(filetypes=[("CityGML Dateien", "*.gml")])
        if path:
            entry_input_ifc.delete(0, "end")
            entry_input_ifc.insert(0, path)

    entry_input_ifc.bind("<Button-1>", select_input_path)

    ttkb.Label(tab_ifc, text="").grid(row=1, column=0, columnspan=2)

    def run_ifc():
        in_path = entry_input_ifc.get()
        out_path = entry_output_ifc.get()
        if not in_path or in_path == "Dateien durchsuchen...":
            print("Fehler:", "Bitte GML-Datei angeben!")
            return
        if not out_path or out_path == "IFC4 Speicherort...":
            print("Fehler:", "Bitte IFC-Datei angeben!")
            return
        try:
            convert_gml_to_ifc(in_path, out_path)
            print("Erfolg:", f"GML->IFC Konvertierung abgeschlossen:\n{out_path}")
        except Exception as e:
            print("Fehler:", str(e))

    btn_convert = ttkb.Button(tab_ifc, text="Konvertieren", command=run_ifc, style="Krekeler.TButton")
    btn_convert.grid(row=2, column=0, columnspan=2, pady=5)

    ttkb.Label(tab_ifc, text="").grid(row=3, column=0, columnspan=2)

    entry_output_ifc = ttkb.Entry(tab_ifc, width=50)
    entry_output_ifc.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
    entry_output_ifc.insert(0, "IFC4 Speicherort...")
    entry_output_ifc.configure(takefocus=False)

    def select_output_path(event):
        path = filedialog.asksaveasfilename(defaultextension=".ifc", filetypes=[("IFC4 Dateien", "*.ifc")])
        if path:
            entry_output_ifc.delete(0, "end")
            entry_output_ifc.insert(0, path)

    entry_output_ifc.bind("<Button-1>", select_output_path)

    return tab_ifc
