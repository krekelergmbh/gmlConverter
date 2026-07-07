"""DGM-Verarbeitung (Digitales Geländemodell).

Liest amtliche DGM-Kacheln der Bundesländer ein und erzeugt daraus ein
Gelände-Dreiecksnetz, das mit den CityGML-Gebäuden kombiniert werden kann
(Vorschau und IFC-Export).

Unterstützte Formate (alles Klartext, keine Zusatzabhängigkeiten):
- XYZ-Gitter (.xyz, .txt, .csv): eine Zeile pro Punkt "x y z",
  Trennzeichen Leerzeichen/Tab/Semikolon/Komma
- ESRI-ASCII-Grid (.asc): ncols/nrows/xllcorner/yllcorner/cellsize-Header
- jeweils auch gzip-komprimiert (.gz), wie z. B. bei NRW üblich

Alle Koordinaten bleiben im amtlichen CRS (UTM) – CityGML-LoD2 und DGM
desselben Bundeslands passen dadurch ohne Umrechnung zusammen.
"""

import gzip
import os
import xml.etree.ElementTree as ET

import numpy as np

# Gleiche Namespaces wie im restlichen Tool (CityGML 1.0)
_NS = {
    'gml': 'http://www.opengis.net/gml',
    'core': 'http://www.opengis.net/citygml/1.0',
    'bldg': 'http://www.opengis.net/citygml/building/1.0',
}

# Obergrenze für Punkte im Geländemesh (Vorschau & IFC bleiben flüssig)
MAX_TERRAIN_POINTS = 250_000


def _open_text(path):
    """Öffnet eine Klartext-Datei, transparent auch gzip (.gz)."""
    if str(path).lower().endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def _parse_xyz(path):
    """Liest eine XYZ-Datei -> ndarray (N, 3). Toleriert ; und , als Trenner."""
    rows = []
    with _open_text(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            for sep in (";", ","):
                line = line.replace(sep, " ")
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                rows.append((float(parts[0]), float(parts[1]), float(parts[2])))
            except ValueError:
                continue  # Kopf-/Kommentarzeilen überspringen
    if not rows:
        raise ValueError(f"Keine XYZ-Punkte in {os.path.basename(path)} gefunden.")
    return np.asarray(rows, dtype=np.float64)


def _parse_asc(path):
    """Liest ein ESRI-ASCII-Grid (.asc) -> ndarray (N, 3), ohne NODATA-Punkte."""
    header = {}
    data_rows = []
    with _open_text(path) as fh:
        for line in fh:
            parts = line.split()
            if not parts:
                continue
            key = parts[0].lower()
            if key in ("ncols", "nrows", "xllcorner", "yllcorner",
                       "cellsize", "nodata_value") and len(parts) >= 2:
                header[key] = float(parts[1])
            else:
                data_rows.append([float(v) for v in parts])

    for req in ("ncols", "nrows", "xllcorner", "yllcorner", "cellsize"):
        if req not in header:
            raise ValueError(f"ASC-Header unvollständig in {os.path.basename(path)} ({req} fehlt).")

    ncols = int(header["ncols"])
    nrows = int(header["nrows"])
    cell = header["cellsize"]
    nodata = header.get("nodata_value", -9999.0)

    grid = np.asarray([v for row in data_rows for v in row], dtype=np.float64)
    if grid.size != ncols * nrows:
        raise ValueError(
            f"ASC-Datenmenge passt nicht zum Header in {os.path.basename(path)} "
            f"({grid.size} Werte, erwartet {ncols * nrows})."
        )
    grid = grid.reshape(nrows, ncols)

    # Zellmittelpunkte; oberste Zeile = größtes Y
    xs = header["xllcorner"] + (np.arange(ncols) + 0.5) * cell
    ys = header["yllcorner"] + (np.arange(nrows)[::-1] + 0.5) * cell
    xx, yy = np.meshgrid(xs, ys)

    mask = grid != nodata
    points = np.column_stack([xx[mask], yy[mask], grid[mask]])
    if points.size == 0:
        raise ValueError(f"Nur NODATA-Werte in {os.path.basename(path)}.")
    return points


def load_dgm_files(paths, log=print):
    """Lädt beliebig viele DGM-Kacheln (XYZ/ASC, auch .gz) -> ndarray (N, 3)."""
    chunks = []
    for p in paths:
        name = os.path.basename(p)
        base = name[:-3] if name.lower().endswith(".gz") else name
        ext = os.path.splitext(base)[1].lower()
        log(f"Lese DGM-Kachel: {name} ...")
        if ext == ".asc":
            pts = _parse_asc(p)
        else:  # .xyz / .txt / .csv / unbekannt -> XYZ-Versuch
            pts = _parse_xyz(p)
        log(f"  {len(pts):,} Punkte".replace(",", "."))
        chunks.append(pts)
    if not chunks:
        raise ValueError("Keine DGM-Dateien angegeben.")
    return np.vstack(chunks)


def gml_bounds(gml_path):
    """Liefert (min_x, max_x, min_y, max_y) über alle posList-Koordinaten der GML."""
    tree = ET.parse(gml_path)
    root = tree.getroot()
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    for pos_list in root.iter('{http://www.opengis.net/gml}posList'):
        if not pos_list.text:
            continue
        try:
            vals = [float(v) for v in pos_list.text.split()]
        except ValueError:
            continue
        xs = vals[0::3]
        ys = vals[1::3]
        if xs and ys:
            min_x = min(min_x, min(xs))
            max_x = max(max_x, max(xs))
            min_y = min(min_y, min(ys))
            max_y = max(max_y, max(ys))
    if min_x == float("inf"):
        raise ValueError("Keine Koordinaten in der GML-Datei gefunden.")
    return min_x, max_x, min_y, max_y


def crop_points(points, bounds, margin=100.0):
    """Beschneidet die Punktwolke auf bounds=(min_x, max_x, min_y, max_y) + Rand."""
    min_x, max_x, min_y, max_y = bounds
    m = (
        (points[:, 0] >= min_x - margin) & (points[:, 0] <= max_x + margin) &
        (points[:, 1] >= min_y - margin) & (points[:, 1] <= max_y + margin)
    )
    return points[m]


def thin_points(points, max_points=MAX_TERRAIN_POINTS):
    """Dünnt gleichmäßig auf höchstens max_points aus (Schrittweiten-Sampling)."""
    n = len(points)
    if n <= max_points:
        return points
    stride = int(np.ceil(n / max_points))
    return points[::stride]


def terrain_mesh(points):
    """Erzeugt aus der Punktwolke ein Dreiecksnetz (TIN) via Delaunay in 2D.

    Rückgabe: pyvista.PolyData (nur Dreiecke).
    """
    import pyvista as pv  # lokal importieren, hält Modul-Import leichtgewichtig

    if len(points) < 3:
        raise ValueError("Zu wenige DGM-Punkte für ein Geländemesh (< 3).")
    cloud = pv.PolyData(points)
    mesh = cloud.delaunay_2d()
    if mesh.n_cells == 0:
        raise ValueError("Delaunay-Triangulation ergab keine Fläche – Punkte prüfen.")
    return mesh


def mesh_to_triangles(mesh):
    """Extrahiert (vertices, faces) aus dem PolyData-Mesh.

    vertices: ndarray (N, 3); faces: ndarray (M, 3) mit 0-basierten Indizes.
    """
    tri = mesh.triangulate()
    faces = tri.faces.reshape(-1, 4)
    if not np.all(faces[:, 0] == 3):
        raise ValueError("Unerwartete Zellstruktur im Geländemesh.")
    return np.asarray(tri.points, dtype=np.float64), faces[:, 1:4].astype(np.int64)


def prepare_terrain(dgm_paths, gml_path=None, margin=100.0,
                    max_points=MAX_TERRAIN_POINTS, log=print):
    """Komplettpfad: Kacheln laden -> (optional) auf GML zuschneiden -> ausdünnen -> Mesh.

    Rückgabe: (mesh, anzahl_verwendeter_punkte)
    """
    points = load_dgm_files(dgm_paths, log=log)
    log(f"DGM gesamt: {len(points):,} Punkte".replace(",", "."))

    if gml_path:
        bounds = gml_bounds(gml_path)
        cropped = crop_points(points, bounds, margin=margin)
        log(f"Zuschnitt auf Gebäudebereich (+{int(margin)} m Rand): "
            f"{len(cropped):,} Punkte".replace(",", "."))
        if len(cropped) >= 3:
            points = cropped
        else:
            log("Warnung: DGM überlappt den GML-Bereich nicht – verwende volles DGM. "
                "Bitte prüfen, ob Kacheln und GML zusammengehören.")

    points = thin_points(points, max_points=max_points)
    log(f"Für Mesh verwendet: {len(points):,} Punkte".replace(",", "."))
    mesh = terrain_mesh(points)
    log(f"Geländemesh: {mesh.n_cells:,} Dreiecke".replace(",", "."))
    return mesh, len(points)
