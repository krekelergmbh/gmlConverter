import ttkbootstrap as ttkb
import tkinter as tk
from tkinter import filedialog
from citygml_converter.ui import section_header, FilePicker, enable_file_drop, MUTED, INK

try:
    from citygml_converter.combine import combine_gml_files
except ImportError:
    def combine_gml_files(file_list, output_path, progress_callback=None):
        pass


def create_tab_combine(notebook):
    tab = ttkb.Frame(notebook, padding=28)
    tab.columnconfigure(0, weight=1)
    tab.rowconfigure(2, weight=1)
    gml_file_list = []

    section_header(
        tab,
        "Merge GML",
        "Führt mehrere CityGML-Dateien zu einer einzigen Datei zusammen."
    ).grid(row=0, column=0, sticky="ew", pady=(0, 18))

    # --- Aktionen ---------------------------------------------------------
    def add_paths(paths):
        new = [p for p in paths if p]
        if new:
            gml_file_list.extend(new)
            for p in new:
                listbox.insert(tk.END, p)

    def add_gml_files():
        paths = filedialog.askopenfilenames(filetypes=[("CityGML Dateien", "*.gml")])
        if paths:
            add_paths(list(paths))

    def clear_gml_files():
        gml_file_list.clear()
        listbox.delete(0, tk.END)

    # Meilensteine (25/50/75/100 %) wie in der Originalversion
    progress_milestones = [25, 50, 75, 100]
    have_printed_in_progress = [False]

    def my_progress_callback(current, total):
        fraction_percent = int((current / total) * 100)

        if not have_printed_in_progress[0]:
            print("In Progress...")
            have_printed_in_progress[0] = True

        while progress_milestones and fraction_percent >= progress_milestones[0]:
            milestone = progress_milestones.pop(0)
            print(f"{milestone}% done...")

        tab.update()

    def run_combine():
        if not gml_file_list:
            print("Fehler: Keine Eingabedateien ausgewählt!")
            return

        out_path = out_picker.get()
        if not out_path:
            print("Fehler: Bitte Ausgabedatei angeben!")
            return

        total = len(gml_file_list)
        print(f"Starte Zusammenführung von {total} Dateien...")

        progress_milestones[:] = [25, 50, 75, 100]
        have_printed_in_progress[0] = False

        try:
            combine_gml_files(
                file_list=gml_file_list,
                output_path=out_path,
                progress_callback=my_progress_callback
            )
            print(f"SUCCESS - {total} Dateien wurden vereint.")
            print(out_path)
        except Exception as e:
            print("Fehler:", e)

    # --- Oberfläche -------------------------------------------------------
    toolbar = ttkb.Frame(tab)
    toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    ttkb.Label(toolbar, text="Eingabedateien", font=("Segoe UI Semibold", 10),
               foreground=INK).pack(side="left")
    ttkb.Button(toolbar, text="Hinzufügen", style="Grey.TButton",
                command=add_gml_files).pack(side="right")
    ttkb.Button(toolbar, text="Liste leeren", style="Grey.TButton",
                command=clear_gml_files).pack(side="right", padx=(0, 8))

    list_frame = ttkb.Frame(tab)
    list_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 4))

    listbox = tk.Listbox(list_frame, height=8, activestyle="none",
                         borderwidth=1, relief="solid", highlightthickness=0)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttkb.Scrollbar(list_frame, bootstyle="round", command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scrollbar.set)

    # Drag & Drop: Dateien direkt in die Liste ziehen
    enable_file_drop(listbox, add_paths)

    ttkb.Label(tab, text="Tipp: GML-Dateien direkt in die Liste ziehen.",
               font=("Segoe UI", 8), foreground=MUTED)\
        .grid(row=3, column=0, sticky="w", pady=(0, 14))

    out_picker = FilePicker(
        tab, "Ausgabedatei (Speicherort)", "Speicherort...",
        lambda: filedialog.asksaveasfilename(
            defaultextension=".gml", filetypes=[("CityGML Dateien", "*.gml")])
    )
    out_picker.grid(row=4, column=0, sticky="ew", pady=(0, 18))

    ttkb.Button(tab, text="Zusammenführen", style="CTA.TButton",
                command=run_combine).grid(row=5, column=0, sticky="w")

    return tab
