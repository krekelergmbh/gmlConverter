import ttkbootstrap as ttkb
import tkinter as tk

def create_readme_tab(notebook, style):
    """
    Erzeugt einen README-Tab mit einem übersichtlichen, dreispaltigen Layout:
    
      - Linke Spalte (ca. 200 Pixel breit): Menü-Buttons in Krekeler Rot (weißer Text, Segoe UI).
      - Mittlere Spalte: Vertikaler Separator (Linie) mit erweitertem Abstand zur rechten Seite.
      - Rechte Spalte: Detaillierte Erklärung.
      
    Im rechten Bereich wird oben in einem Topframe der Name des gewählten Menüpunkts angezeigt,
    gefolgt von einer Leerzeile und der detaillierten Beschreibung.
    """
    tab_readme = ttkb.Frame(notebook)
    
    # Drei Spalten: 0 = Menü, 1 = Separator, 2 = Inhalt
    tab_readme.columnconfigure(0, weight=0)
    tab_readme.columnconfigure(1, weight=0)
    tab_readme.columnconfigure(2, weight=1)
    
    # Linke Spalte: Menüframe
    menu_frame = ttkb.Frame(tab_readme)
    menu_frame.grid(row=0, column=0, sticky="ns", padx=(10, 5), pady=10)
    menu_frame.configure(width=200)
    
    # Mittlere Spalte: Vertikaler Separator mit erweitertem Abstand rechts
    separator = ttkb.Separator(tab_readme, orient="vertical")
    separator.grid(row=0, column=1, sticky="ns", padx=(5,15), pady=10)
    
    # Rechte Spalte: Inhaltsframe
    content_frame = ttkb.Frame(tab_readme)
    content_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)
    content_frame.columnconfigure(0, weight=1)
    
    # Topframe für den Titel in der Inhalts-Spalte
    title_var = tk.StringVar()
    title_var.set("")
    top_frame = ttkb.Frame(content_frame)
    top_frame.pack(fill='x', padx=20, pady=(0,5))
    title_label = ttkb.Label(top_frame, textvariable=title_var,
                             font=("Segoe UI", 18, "bold"), foreground="black")
    title_label.pack(anchor="w")

    # Leerzeile als Abstandshalter
    spacer = ttkb.Label(content_frame, text="", font=("Segoe UI", 14))
    spacer.pack(fill='x', pady=(0,5))

    # Label für den erklärenden Text
    content_var = tk.StringVar()
    content_var.set("Wählen Sie einen Menüpunkt aus der linken Spalte, um detaillierte Informationen anzuzeigen.")
    explanation_label = ttkb.Label(content_frame, textvariable=content_var,
                                   wraplength=620, justify="left", font=("Segoe UI", 15),
                                   foreground="black")
    explanation_label.pack(fill='both', padx=20, pady=(0,10))
    
    # Definition der Abschnitte mit detaillierten Anleitungen
    sections = {
        "Workflow": (
            "Der Workflow-Assistent führt Sie ohne Vorkenntnisse Schritt für Schritt zum fertigen Ergebnis.\n\n"
            "Schritt 1: Wählen Sie, welche Daten Sie benötigen – Gebäude (GML), Gelände (DGM) oder beides.\n\n"
            "Schritt 2: Wählen Sie Ihr Bundesland und öffnen Sie die vorgeschlagenen Download-Portale. "
            "Laden Sie dort die Daten für Ihr Gebiet herunter (ZIP-Dateien bitte entpacken).\n\n"
            "Schritt 3: Geben Sie die heruntergeladenen Dateien an – mehrere GML-Dateien werden automatisch vereint, "
            "das Gelände wird automatisch auf den Gebäudebereich zugeschnitten.\n\n"
            "Schritt 4: Bestätigen Sie die Optionen (z. B. IFC-Modell oder bearbeitete GML, Höhen auf Null, 3D-Vorschau).\n\n"
            "Schritt 5: Speicherort wählen und auf 'Jetzt ausführen' klicken – der Assistent erledigt alle Schritte "
            "in der richtigen Reihenfolge und zeigt auf Wunsch die 3D-Vorschau."
        ),
        "Pick GML": (
            "Schritt 1: Navigieren Sie in der interaktiven Deutschlandkarte zu dem Bundesland, aus dem Sie CityGML LoD2-Daten beziehen möchten.\n\n"
            "Schritt 2: Bewegen Sie die Maus über das gewünschte Bundesland. Das Bundesland wird rot hervorgehoben.\n\n"
            "Schritt 3: Klicken Sie auf das hervorgehobene Bundesland, um die zugehörige Website zu öffnen.\n\n"
            "Schritt 4: Laden Sie den CityGML LoD2-Datensatz von der Website herunter und speichern Sie die Datei lokal auf Ihrem Rechner.\n\n"
            "Schritt 5: Verwenden Sie anschließend den Pfad zu dieser lokal gespeicherten Datei in den weiteren Tools, wie dem z0 Converter oder GML2IFC."
        ),
        "z0 Converter": (
            "Schritt 1: Datei auswählen: Klicken Sie auf das Eingabefeld, um über den Dateidialog eine CityGML-Datei auszuwählen.\n\n"
            "Schritt 2: Ziel festlegen: Geben Sie den Speicherort und den Dateinamen für die konvertierte Datei ein.\n\n"
            "Schritt 3: Konvertierung starten: Klicken Sie auf den 'Konvertieren'-Button, um den Vorgang zu starten. Das System passt die Z-Koordinaten an, indem der minimale Z-Wert von allen Koordinaten abgezogen wird."
        ),
        "GML2IFC": (
            "Schritt 1: Eingabedatei auswählen: Klicken Sie auf das Eingabefeld und wählen Sie die gewünschte CityGML-Datei aus.\n\n"
            "Schritt 2: Ausgabedatei festlegen: Legen Sie den Zielordner und den Dateinamen für die IFC4-Datei fest.\n\n"
            "Schritt 3: Umwandlung starten: Klicken Sie auf den 'Konvertieren'-Button, um den Umwandlungsprozess zu starten. Die Anwendung rechnet die Gebäudedaten in das IFC4-Format um."
        ),
        "Merge GML": (
            "Schritt 1: Dateien hinzufügen: Klicken Sie auf den 'Hinzufügen'-Button und wählen Sie die gewünschten CityGML-Dateien aus.\n\n"
            "Schritt 2: Liste überprüfen: Prüfen Sie die angezeigte Liste. Mit 'Liste leeren' können Sie die gesamte Auswahl zurücksetzen und neu beginnen.\n\n"
            "Schritt 3: Ausgabedatei festlegen: Geben Sie den Zielpfad und den Dateinamen für die zusammengeführte Datei ein.\n\n"
            "Schritt 4: Merge starten: Klicken Sie auf den 'Merge'-Button, um den Zusammenführungsprozess zu starten. Am Ende erhalten Sie eine konsolidierte CityGML-Datei."
        ),
        "Gelände (DGM)": (
            "Schritt 1: DGM-Daten herunterladen: Wählen Sie Ihr Bundesland aus und klicken Sie auf 'Portal öffnen'. "
            "Laden Sie dort die DGM1-Kacheln für Ihr Gebiet herunter (XYZ- oder ASC-Format, auch gzip .gz).\n\n"
            "Schritt 2: Kacheln hinzufügen: Fügen Sie die heruntergeladenen DGM-Kacheln über 'Hinzufügen' hinzu "
            "oder ziehen Sie sie direkt in die Liste.\n\n"
            "Schritt 3: Gebäude angeben (optional): Wählen Sie die CityGML-Datei mit den Gebäuden – dann entsteht eine "
            "kombinierte IFC und das Gelände wird automatisch auf den Gebäudebereich (+100 m Rand) zugeschnitten. "
            "Ohne Gebäude-GML entsteht eine reine Gelände-IFC. Wichtig: Original-GML mit absoluten Höhen verwenden "
            "(nicht die z0-konvertierte Datei), damit Gebäude und Gelände zusammenpassen.\n\n"
            "Schritt 4: 'Als IFC exportieren' erzeugt die IFC4-Datei (Gelände als IfcGeographicElement).\n\n"
            "Tipp: Die 3D-Ansicht von Gelände und Gebäuden finden Sie im Tab 'Preview'."
        ),
        "Preview": (
            "Schritt 1: Daten auswählen: Wählen Sie eine CityGML-Datei und/oder fügen Sie DGM-Kacheln hinzu – "
            "beides zusammen zeigt Gebäude und Gelände kombiniert.\n\n"
            "Schritt 2: Daten laden: Klicken Sie auf den 'Laden'-Button, um die Dateien einzulesen. "
            "Sind Gebäude und Gelände angegeben, wird das Gelände auf den Gebäudebereich zugeschnitten.\n\n"
            "Schritt 3: Vorschau starten: Klicken Sie auf den 'Vorschau'-Button, um die grafische 3D-Darstellung zu öffnen."
        ),
        "PyVista Fenster": (
            "Schritt 1: Öffnen Sie den Preview-Tab, laden Sie Ihre Daten über 'Laden' und öffnen Sie das 3D-Fenster über 'Vorschau'.\n\n"
            "Schritt 2: Wählen Sie die gewünschte Ansicht (Top View, Front View oder Isometric), um das Modell aus verschiedenen Perspektiven zu betrachten.\n\n"
            "Schritt 3: Interagieren Sie mit dem Modell: Ziehen Sie, um zu rotieren; scrollen Sie, um hinein- oder herauszuzoomen; klicken Sie, um Details auszuwählen."
        )
    }
    
    # Funktion zum Aktualisieren von Titel und Erklärung bei Klick auf einen Menüpunkt
    def show_content(section_name):
        title_var.set(section_name)
        content = sections.get(section_name, "Keine Informationen verfügbar.")
        content_var.set(content)
    
    # Erstellen der Buttons im Menü (linke Spalte) in der Reihenfolge der Dictionary-Keys
    for section_name in sections:
        btn = ttkb.Button(menu_frame, text=section_name, style="Krekeler.TButton",
                           command=lambda name=section_name: show_content(name))
        btn.pack(fill='x', pady=5)
    
    return tab_readme
