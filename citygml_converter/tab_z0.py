import ttkbootstrap as ttkb
from ttkbootstrap.constants import SUCCESS
import tkinter as tk
from tkinter import filedialog
from citygml_converter.z0_converter import convert_gml_to_z0

def create_tab_z0(notebook):
    tab_z0 = ttkb.Frame(notebook)
    tab_z0.columnconfigure(0, weight=1)

    entry_input_z0 = ttkb.Entry(tab_z0, width=50)
    entry_input_z0.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    entry_input_z0.insert(0, "Dateien durchsuchen...")
    entry_input_z0.configure(takefocus=False)

    def select_input_z0(event):
        path = filedialog.askopenfilename(filetypes=[("CityGML Dateien", "*.gml")])
        if path:
            entry_input_z0.delete(0, "end")
            entry_input_z0.insert(0, path)

    entry_input_z0.bind("<Button-1>", select_input_z0)

    ttkb.Label(tab_z0, text="").grid(row=1, column=0)

    def run_z0():
        in_path = entry_input_z0.get()
        out_path = entry_output_z0.get()
        if not in_path or in_path == "Dateien durchsuchen...":
            print("Fehler", "Bitte GML-Datei angeben!")
            return
        if not out_path or out_path == "Speicherort...":
            print("Fehler", "Bitte Ausgabedatei angeben!")
            return
        try:
            convert_gml_to_z0(in_path, out_path)
            print("Erfolg", f"Z=0-Konvertierung abgeschlossen:\n{out_path}")
        except Exception as e:
            print("Fehler", str(e))

    btn_convert = ttkb.Button(tab_z0, text="Konvertieren", command=run_z0, style="Krekeler.TButton")
    btn_convert.grid(row=2, column=0, pady=5)

    ttkb.Label(tab_z0, text="").grid(row=3, column=0)

    entry_output_z0 = ttkb.Entry(tab_z0, width=50)
    entry_output_z0.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
    entry_output_z0.insert(0, "Speicherort...")
    entry_output_z0.configure(takefocus=False)

    def select_output_z0(event):
        path = filedialog.asksaveasfilename(defaultextension=".gml", filetypes=[("CityGML Dateien", "*.gml")])
        if path:
            entry_output_z0.delete(0, "end")
            entry_output_z0.insert(0, path)

    entry_output_z0.bind("<Button-1>", select_output_z0)

    return tab_z0
