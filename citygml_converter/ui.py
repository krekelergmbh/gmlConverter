"""Geteilte, moderne UI-Bausteine für den gmlConverter.

Enthält:
- enable_file_drop(): registriert ein Widget als Datei-Drop-Ziel (Drag & Drop).
- section_header(): einheitliche Abschnitts-Überschrift mit Akzentlinie.
- FilePicker: modernes Datei-Eingabefeld (klickbar + Drag & Drop + Durchsuchen).

Drag & Drop ist optional: Ist tkinterdnd2 nicht verfügbar oder nicht aktiv,
verhalten sich die Felder weiterhin wie zuvor (Klick öffnet den Dateidialog).
Es geht also keine Funktion verloren.
"""

import tkinter as tk
import ttkbootstrap as ttkb

# Markenfarben
BRAND = "#892337"
MUTED = "#8A8A8A"
INK = "#222222"

try:
    from tkinterdnd2 import DND_FILES
    DND_IMPORTED = True
except Exception:
    DND_FILES = None
    DND_IMPORTED = False

# Wird von gui.main() auf True gesetzt, sobald das Hauptfenster
# erfolgreich Drag-&-Drop-fähig initialisiert wurde.
DND_ACTIVE = False


def dnd_ready():
    """True, wenn Drag & Drop tatsächlich nutzbar ist."""
    return DND_IMPORTED and DND_ACTIVE


def enable_file_drop(widget, on_files):
    """Registriert *widget* als Datei-Drop-Ziel.

    on_files(list_of_paths) wird beim Fallenlassen aufgerufen.
    No-op (kein Fehler), wenn Drag & Drop nicht verfügbar ist.
    """
    if not dnd_ready():
        return
    try:
        widget.drop_target_register(DND_FILES)

        def _handler(event):
            try:
                files = list(widget.tk.splitlist(event.data))
            except Exception:
                files = [event.data]
            files = [f for f in files if f]
            if files:
                on_files(files)

        widget.dnd_bind("<<Drop>>", _handler)
    except Exception:
        # Fällt still zurück – Klick-zum-Durchsuchen bleibt funktionsfähig.
        pass


def section_header(parent, title, subtitle=None):
    """Einheitliche Abschnitts-Überschrift: Akzentlinie + Titel (+ Untertitel)."""
    frame = ttkb.Frame(parent)
    tk.Frame(frame, background=BRAND, width=58, height=4).pack(anchor="w", pady=(0, 9))
    ttkb.Label(frame, text=title, font=("Segoe UI Semibold", 21),
               foreground=INK).pack(anchor="w")
    if subtitle:
        ttkb.Label(frame, text=subtitle, font=("Segoe UI", 13), foreground=MUTED,
                   wraplength=700, justify="left").pack(anchor="w", pady=(5, 0))
    return frame


class FilePicker(ttkb.Frame):
    """Modernes Datei-Eingabefeld.

    Aufbau: Label · Eingabefeld (klickbar + Drag & Drop) · Durchsuchen-Button · Hinweis.

    Parameter:
        label        Beschriftung über dem Feld
        placeholder  Platzhaltertext (gilt als "leer")
        dialog       Funktion ohne Argumente, die einen Pfad (oder "") zurückgibt
        dnd          Drag & Drop aktivieren (Default True)
    """

    def __init__(self, parent, label, placeholder, dialog, dnd=True):
        super().__init__(parent)
        self._placeholder = placeholder
        self._dialog = dialog
        self.columnconfigure(0, weight=1)

        ttkb.Label(self, text=label, font=("Segoe UI Semibold", 13),
                   foreground=INK).grid(row=0, column=0, columnspan=2,
                                        sticky="w", pady=(0, 5))

        self.var = tk.StringVar(value=placeholder)
        self.entry = ttkb.Entry(self, textvariable=self.var, font=("Segoe UI", 13))
        self.entry.grid(row=1, column=0, sticky="ew", ipady=7)
        self.entry.configure(takefocus=False)
        self.entry.bind("<Button-1>", lambda e: self.browse())

        ttkb.Button(self, text="Durchsuchen", style="Grey.TButton",
                    command=self.browse).grid(row=1, column=1, padx=(10, 0), sticky="ew")

        hint = ("Datei hierher ziehen oder Feld anklicken" if dnd_ready()
                else "Feld anklicken, um eine Datei auszuwählen")
        ttkb.Label(self, text=hint, font=("Segoe UI", 10),
                   foreground=MUTED).grid(row=2, column=0, columnspan=2,
                                          sticky="w", pady=(5, 0))

        if dnd:
            enable_file_drop(self.entry, self._dropped)
            enable_file_drop(self, self._dropped)

    def browse(self):
        path = self._dialog()
        if path:
            self.set(path)

    def _dropped(self, files):
        self.set(files[0])

    def get(self):
        """Aktueller Pfad – leerer String, wenn nur der Platzhalter steht."""
        value = self.var.get().strip()
        return "" if value == self._placeholder else value

    def set(self, path):
        self.var.set(path)
