import os
import sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import webbrowser

def resource_path(relative_path):
    """Gibt den absoluten Pfad zur Ressource zurück.
    Wenn die Anwendung gebündelt ist, wird sys._MEIPASS verwendet."""
    try:
        # Bei gebündelten Anwendungen (PyInstaller)
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def show_splash(duration=6000):
    """
    Zeigt einen Splash-Screen mit folgendem Aufbau:
    - Oben: Titel "gmlConverter" (etwas größer)
    - Darunter: Untertitel "by mwo @ Krekeler Architekten Generalplaner GmbH" in kleiner, grauer Schrift
    - Direkt danach: Ein Separator (lange Unterstriche, die den Untertitel optisch unterstreichen)
    - Eine Leerzeile
    - Eine Überschrift "Partners" (in grau, normal)
    - Darunter das Logo (angepasst, da das Original 9452x1168px beträgt) – klickbar, um einen Link zu öffnen
    - In der untersten Zeile:
         • linksbündig: Ladeanimation (zyklisch: "Loading", "Loading.", "Loading..", "Loading...")
         • rechtsbündig: Version "version 0.1.0"
    Schließt sich nach 'duration' Millisekunden automatisch.
    """
    splash = tk.Toplevel()
    splash.overrideredirect(True)  # Titelleiste und Rahmen entfernen

    # Größe und Position: 400x300 in der Bildschirmmitte
    splash_width, splash_height = 400, 300
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - splash_width) // 2
    y = (screen_height - splash_height) // 2
    splash.geometry(f"{splash_width}x{splash_height}+{x}+{y}")

    # Logo-Pfad ermitteln über resource_path
    logo_path = resource_path(os.path.join("__files__", "Krekeler_Logo_rgb_200mm.png"))

    try:
        # Bild laden und skalieren (Original: 9452x1168px, Ziel: max. Breite 350px)
        logo_image = Image.open(logo_path)
        max_logo_width = 350
        orig_width, orig_height = logo_image.size
        ratio = max_logo_width / orig_width
        new_width = int(orig_width * ratio)
        new_height = int(orig_height * ratio)
        logo_image = logo_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        logo = ImageTk.PhotoImage(logo_image)
    except Exception as e:
        print(f"Fehler beim Laden des Logos: {e}")
        logo = None

    # Hauptcontainer für den oberen Inhalt (Titel, Untertitel, Separator, "Partners" und Logo)
    content_frame = tk.Frame(splash)
    content_frame.pack(expand=True, fill="both", padx=20, pady=20)

    # Titel (etwas größer)
    title_label = tk.Label(content_frame, text="gmlConverter", font=("Segoe UI", 24, "bold"))
    title_label.pack(pady=(10, 5))

    # Untertitel in kleiner, grauer Schrift
    subtitle_label = tk.Label(content_frame, text="by mwo @ Krekeler Architekten Generalplaner GmbH",
                              font=("Segoe UI", 10), fg="gray")
    subtitle_label.pack()

    # Separator als lange Unterstriche
    separator_text = "_" * 50
    separator_label = tk.Label(content_frame, text=separator_text, fg="#892337")
    separator_label.pack(pady=5)

    # Überschrift "Partners" (in grau, normal)
    partners_label = tk.Label(content_frame, text="Partners", font=("Segoe UI", 12), fg="gray")
    partners_label.pack(pady=(5,5))

    # Logo-Label – klickbar, um den Link zu öffnen
    if logo:
        logo_label = tk.Label(content_frame, image=logo, borderwidth=0, cursor="hand2")
        logo_label.image = logo  # Referenz halten
        logo_label.pack(pady=10)
        # Beim Klick den Browser mit dem Link öffnen
        logo_label.bind("<Button-1>", lambda e: webbrowser.open("https://krekeler-architekten.de/"))
    else:
        logo_label = tk.Label(content_frame, text="Krekeler Logo", font=("Segoe UI", 14))
        logo_label.pack(pady=10)

    # Unterer Bereich: Frame für Ladeanimation und Version
    bottom_frame = tk.Frame(splash)
    bottom_frame.pack(side="bottom", fill="x", padx=10, pady=(0,10))

    # Einheitliche Schriftart für beide Labels (klein, grau)
    bottom_font = ("Segoe UI", 10)
    bottom_fg = "gray"

    # Ladeanimation-Label linksbündig
    loading_label = tk.Label(bottom_frame, text="Loading", font=bottom_font, fg=bottom_fg)
    loading_label.pack(side="left", anchor="w")

    # Version-Label rechtsbündig
    version_label = tk.Label(bottom_frame, text="version 1.0.0", font=bottom_font, fg=bottom_fg)
    version_label.pack(side="right", anchor="e")

    # Ladeanimation: Zyklus "Loading", "Loading.", "Loading..", "Loading..."
    animation_texts = ["Loading", "Loading.", "Loading..", "Loading..."]
    after_id = None  # Für den after-Callback

    def update_loading(index=0):
        nonlocal after_id
        if not splash.winfo_exists():
            return
        try:
            current_text = animation_texts[index % len(animation_texts)]
            loading_label.config(text=current_text)
            after_id = splash.after(500, update_loading, index + 1)
        except tk.TclError:
            return

    update_loading()

    def close_splash():
        nonlocal after_id
        if after_id is not None:
            try:
                splash.after_cancel(after_id)
            except tk.TclError:
                pass
        try:
            splash.destroy()
        except tk.TclError:
            pass

    splash.after(duration, close_splash)
    splash.update_idletasks()
    splash.wait_window()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    show_splash(duration=6000)
