import ttkbootstrap as ttkb
from ttkbootstrap.constants import SUCCESS
import tkinter as tk
from tkinter import filedialog

try:
    from citygml_converter.combine import combine_gml_files
except ImportError:
    def combine_gml_files(file_list, output_path, progress_callback=None):
        pass

def create_tab_combine(notebook):
    tab_combine = ttkb.Frame(notebook)
    gml_file_list = []

    tab_combine.columnconfigure(2, weight=1)
    tab_combine.rowconfigure(0, weight=1)

    # Listbox + Scrollbar
    list_frame = ttkb.Frame(tab_combine)
    list_frame.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)

    listbox = tk.Listbox(list_frame, height=8, width=60)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttkb.Scrollbar(list_frame, bootstyle="round", command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scrollbar.set)

    def add_gml_files():
        paths = filedialog.askopenfilenames(filetypes=[("CityGML Dateien", "*.gml")])
        if paths:
            gml_file_list.extend(paths)
            for p in paths:
                listbox.insert(tk.END, p)

    def clear_gml_files():
        gml_file_list.clear()
        listbox.delete(0, tk.END)

    def select_output_path(event):
        path = filedialog.asksaveasfilename(
            defaultextension=".gml",
            filetypes=[("CityGML Dateien", "*.gml")]
        )
        if path:
            entry_output_combine.delete(0, "end")
            entry_output_combine.insert(0, path)

    # Einfaches Zwischenspeicher für die "Meilensteine" (25%, 50%, 75%, 100%)
    # und eine Flag, ob wir schon "In Progress..." gedruckt haben
    progress_milestones = [25, 50, 75, 100]
    have_printed_in_progress = [False]  # trick, um in innerer Funktion änderbar zu sein

    def my_progress_callback(current, total):
        fraction_percent = int((current / total) * 100)

        # 1) "In Progress..." nur einmal am Anfang
        if not have_printed_in_progress[0]:
            print("In Progress...")
            have_printed_in_progress[0] = True

        # 2) Check ob wir einen Meilenstein (25,50,75,100) erreicht haben
        #    und drucken "xx% done..." wenn ja
        while progress_milestones and fraction_percent >= progress_milestones[0]:
            milestone = progress_milestones.pop(0)
            print(f"{milestone}% done...")

        tab_combine.update()

    def run_combine():
        if not gml_file_list:
            print("Fehler: Keine Eingabedateien ausgewählt!")
            return

        out_path = entry_output_combine.get()
        if not out_path or out_path == "Speicherort...":
            print("Fehler: Bitte Ausgabedatei angeben!")
            return

        total = len(gml_file_list)
        print(f"Starte Zusammenführung von {total} Dateien...")

        # Reset Milestones und "In Progress"-Flag vor dem Start
        progress_milestones[:] = [25, 50, 75, 100]
        have_printed_in_progress[0] = False

        try:
            combine_gml_files(
                file_list=gml_file_list,
                output_path=out_path,
                progress_callback=my_progress_callback
            )
            # Nach Ende: SUCCESS
            print(f"SUCCESS - {total} Dateien wurden vereint.")
            print(out_path)
        except Exception as e:
            print("Fehler:", e)

    # GUI-Elemente
    btn_add = ttkb.Button(tab_combine, text="Hinzufügen", command=add_gml_files, style="Krekeler.TButton")
    btn_add.grid(row=1, column=0, padx=5, pady=5, sticky="w")

    btn_clear = ttkb.Button(tab_combine, text="Clear List", command=clear_gml_files, style="Krekeler.TButton")
    btn_clear.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    entry_output_combine = ttkb.Entry(tab_combine, width=30)
    entry_output_combine.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
    entry_output_combine.insert(0, "Speicherort...")
    entry_output_combine.bind("<Button-1>", select_output_path)

    btn_merge = ttkb.Button(tab_combine, text="Merge", command=run_combine, style="Krekeler.TButton")
    btn_merge.grid(row=1, column=3, padx=5, pady=5, sticky="w")

    return tab_combine
