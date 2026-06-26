import sys
import os
import tkinter as tk
import ttkbootstrap as ttkb
import webbrowser
import json

def create_tab_map(notebook):
    tab_map = ttkb.Frame(notebook)
    tab_map.columnconfigure(0, weight=1)
    tab_map.rowconfigure(0, weight=1)

    # Canvas, der den gesamten Bereich ausfüllt
    canvas = tk.Canvas(tab_map, bg="white")
    canvas.grid(row=0, column=0, sticky="nsew")

    # Pfad zur germany_bundeslaender.json in __files__
    # Beachte: Bei PyInstaller steht sys._MEIPASS für das temporäre Entpack-Verzeichnis
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    # JSON liegt jetzt in __files__/germany_bundeslaender.json
    json_path = os.path.join(base_path, "__files__", "germany_bundeslaender.json")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            geo_data = json.load(f)
    except Exception as e:
        print("Fehler beim Laden der germany_bundeslaender.json:", e)
        return tab_map

    # Dictionary: Zuordnung von Bundeslandnamen zu den LoD2-Geoportal-URLs
    geoportal_urls = {
        "Baden-Württemberg": "https://opengeodata.lgl-bw.de/#/(sidenav:product/lod2)",
        "Bayern": "https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=lod2",
        "Berlin": "https://gdi.berlin.de/geonetwork/srv/ger/catalog.search#/metadata/3c7c49af-00a4-3bcd-bc00-20e7f0f1b7bf",
        "Brandenburg": "https://data.geobasis-bb.de/geobasis/daten/3d_gebaeude/lod2_gml/",
        "Bremen": "https://metaver.de/trefferanzeige?docuuid=226971C2-6677-4B79-95F3-C5311F1275C8",
        "Hamburg": "https://suche.transparenz.hamburg.de/dataset/3d-stadtmodell-hamburg",
        "Hessen": "https://gds.hessen.de/INTERSHOP/web/WFS/HLBG-Geodaten-Site/de_DE/-/EUR/ViewDownloadcenter-Start?path=3D-Daten/3D-Geb%C3%A4udemodelle/3D-Geb%C3%A4udemodelle%20LoD2",
        "Mecklenburg-Vorpommern": "https://laiv.geodaten-mv.de/afgvk/Geotopographie/Download?produkt=LOD2",
        "Niedersachsen": "https://ni-lgln-opengeodata.hub.arcgis.com/",
        "Nordrhein-Westfalen": "https://www.opengeodata.nrw.de/produkte/geobasis/3dg/lod2_gml/",
        "Rheinland-Pfalz": "https://geoshop.rlp.de/opendata-geb3dlo.html",
        "Saarland": "https://mediaproxy.tvtropes.org/width/1200/https://static.tvtropes.org/pmwiki/pub/images/spongebob_meme_64.png",
        "Sachsen": "https://www.geodaten.sachsen.de/downloadbereich-digitale-3d-stadtmodelle-4875.html",
        "Sachsen-Anhalt": "https://www.lvermgeo.sachsen-anhalt.de/de/startseite.html",
        "Schleswig-Holstein": "https://geodaten.schleswig-holstein.de/gaialight-sh/_apps/dladownload/dl-lod2.html",
        "Thüringen": "https://geoportal.thueringen.de/gdi-th/download-offene-geodaten/download-3d-gebaeudedaten"
    }

    def draw_map():
        canvas.delete("all")
        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        if cw <= 0 or ch <= 0:
            return

        # Ermittele globale Bounding Box
        lons, lats = [], []
        for feature in geo_data["features"]:
            geometry = feature["geometry"]
            if geometry["type"] == "Polygon":
                for ring in geometry["coordinates"]:
                    for lon, lat in ring:
                        lons.append(lon)
                        lats.append(lat)
            elif geometry["type"] == "MultiPolygon":
                for polygon in geometry["coordinates"]:
                    for ring in polygon:
                        for lon, lat in ring:
                            lons.append(lon)
                            lats.append(lat)
        if not lons or not lats:
            return
        global_min_lon, global_max_lon = min(lons), max(lons)
        global_min_lat, global_max_lat = min(lats), max(lats)

        # Skalierung + Offset (10% Rand)
        scale_x = cw / (global_max_lon - global_min_lon)
        scale_y = ch / (global_max_lat - global_min_lat)
        scale = min(scale_x, scale_y) * 0.9
        offset_x = (cw - (global_max_lon - global_min_lon) * scale) / 2
        offset_y = (ch - (global_max_lat - global_min_lat) * scale) / 2

        def transform(lon, lat):
            x = (lon - global_min_lon) * scale + offset_x
            y = offset_y + (global_max_lat - lat) * scale
            return x, y

        # Zeichne alle Bundesländer
        for feature in geo_data["features"]:
            props = feature["properties"]
            state_name = props.get("name", "unbekannt")
            geometry = feature["geometry"]
            if geometry["type"] == "Polygon":
                for ring in geometry["coordinates"]:
                    flat_coords = []
                    for lon, lat in ring:
                        x, y = transform(lon, lat)
                        flat_coords.extend([x, y])
                    canvas.create_polygon(flat_coords, fill="#DDDDDD", outline="black", tags=(state_name,))
            elif geometry["type"] == "MultiPolygon":
                for polygon in geometry["coordinates"]:
                    for ring in polygon:
                        flat_coords = []
                        for lon, lat in ring:
                            x, y = transform(lon, lat)
                            flat_coords.extend([x, y])
                        canvas.create_polygon(flat_coords, fill="#DDDDDD", outline="black", tags=(state_name,))

        # Enklaven (Berlin, Bremen) oben halten
        for enclave in ["Berlin", "Bremen"]:
            canvas.tag_raise(enclave)

        # Hover-Label unten links
        canvas.delete("hover_label")
        canvas.create_text(
            5, ch - 5,
            text="",
            anchor="sw",
            font=("Segoe UI", 12),
            fill="black",
            tags=("hover_label",)
        )

    def on_motion(event):
        overlapping = canvas.find_overlapping(event.x, event.y, event.x, event.y)
        top_state = None
        if overlapping:
            top_item = overlapping[-1]
            tags = canvas.gettags(top_item)
            if tags:
                top_state = tags[0]
        # Standardfarbe wiederherstellen
        for state in geoportal_urls.keys():
            canvas.itemconfigure(state, fill="#DDDDDD")
        # Aktives Bundesland rot hervorheben
        if top_state:
            canvas.itemconfigure(top_state, fill="#A23A48")
        # Label (unten links) updaten
        canvas.itemconfigure("hover_label", text=top_state if top_state else "")

    def on_leave_canvas(event):
        for state in geoportal_urls.keys():
            canvas.itemconfigure(state, fill="#DDDDDD")
        canvas.itemconfigure("hover_label", text="")

    def on_click(event):
        overlapping = canvas.find_overlapping(event.x, event.y, event.x, event.y)
        if overlapping:
            top_item = overlapping[-1]
            tags = canvas.gettags(top_item)
            if tags:
                state = tags[0]
                url = geoportal_urls.get(state)
                if url:
                    webbrowser.open_new_tab(url)

    canvas.bind("<Motion>", on_motion)
    canvas.bind("<Leave>", on_leave_canvas)
    canvas.bind("<Button-1>", on_click)
    canvas.bind("<Configure>", lambda event: draw_map())

    return tab_map
