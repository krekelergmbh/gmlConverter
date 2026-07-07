"""DGM-Verarbeitung (Digitales Geländemodell).

Liest amtliche DGM-Kacheln der Bundesländer ein und erzeugt daraus ein
Gelände-Dreiecksnetz, das mit den CityGML-Gebäuden kombiniert werden kann
(Vorschau und IFC-Export).

Unterstützte Formate (alles Klartext, keine Zusatzabhängigkeiten):
- XYZ-Gitter (.xyz, .txt, .csv): eine Zeile pro Punkt "x y z",
  Trennzeichen Leerzeichen/Tab/Semikolon/Komma
- ESRI-ASCII-Grid (.asc): ncols/nrows/cellsize-Header, sowohl mit
  xllcorner/yllcorner als auch xllcenter/yllcenter (z. B. BKG-Abgaben)
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

# Fallback-Parser: Zeilenpuffer chunkweise in Arrays wandeln (Speicherspitze klein halten)
_CHUNK_ROWS = 1_000_000


def _open_text(path):
    """Öffnet eine Klartext-Datei, transparent auch gzip (.gz)."""
    if str(path).lower().endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def _finite_only(points):
    """Verwirft Zeilen mit NaN/Inf (kommen z. B. aus GDAL-Exporten vor)."""
    if len(points) == 0:
        return points
    mask = np.isfinite(points).all(axis=1)
    return points[mask] if not mask.all() else points


def _parse_xyz(path):
    """Liest eine XYZ-Datei -> ndarray (N, 3).

    Schneller Pfad über np.loadtxt (Leerzeichen/Tab-getrennt, liest .gz direkt);
    toleranter Fallback für Semikolon/Komma-Trenner und Kopfzeilen.
    """
    try:
        pts = np.loadtxt(path, dtype=np.float64, ndmin=2)
        if pts.ndim == 2 and pts.shape[1] >= 3:
            return pts[:, :3]
    except Exception:
        pass  # -> toleranter Fallback

    chunks = []
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
            if len(rows) >= _CHUNK_ROWS:
                chunks.append(np.asarray(rows, dtype=np.float64))
                rows = []
    if rows:
        chunks.append(np.asarray(rows, dtype=np.float64))
    if not chunks:
        raise ValueError(f"Keine XYZ-Punkte in {os.path.basename(path)} gefunden.")
    return np.vstack(chunks)


def _parse_asc(path):
    """Liest ein ESRI-ASCII-Grid (.asc) -> ndarray (N, 3), ohne NODATA-Punkte.

    Unterstützt xllcorner/yllcorner (Zellecke) und xllcenter/yllcenter
    (Zellmittelpunkt, u. a. in BKG-GRID-ASCII-Abgaben).
    """
    header = {}
    header_keys = ("ncols", "nrows", "xllcorner", "yllcorner",
                   "xllcenter", "yllcenter", "cellsize", "nodata_value")
    data_rows = []
    with _open_text(path) as fh:
        for line in fh:
            parts = line.split()
            if not parts:
                continue
            key = parts[0].lower()
            if key in header_keys and len(parts) >= 2:
                header[key] = float(parts[1])
                continue
            try:
                data_rows.append([float(v) for v in parts])
            except ValueError:
                continue  # Kommentar-/Fremdzeilen tolerant überspringen

    for req in ("ncols", "nrows", "cellsize"):
        if req not in header:
            raise ValueError(
                f"ASC-Header unvollständig in {os.path.basename(path)} ({req} fehlt).")

    ncols = int(header["ncols"])
    nrows = int(header["nrows"])
    cell = header["cellsize"]
    nodata = header.get("nodata_value", -9999.0)

    # Ursprung: corner-Variante -> +0,5 Zellen zum Mittelpunkt; center-Variante direkt
    if "xllcorner" in header and "yllcorner" in header:
        x0 = header["xllcorner"] + 0.5 * cell
        y0 = header["yllcorner"] + 0.5 * cell
    elif "xllcenter" in header and "yllcenter" in header:
        x0 = header["xllcenter"]
        y0 = header["yllcenter"]
    else:
        raise ValueError(
            f"ASC-Header unvollständig in {os.path.basename(path)} "
            f"(xllcorner/yllcorner oder xllcenter/yllcenter fehlt).")

    grid = np.asarray([v for row in data_rows for v in row], dtype=np.float64)
    if grid.size != ncols * nrows:
        raise ValueError(
            f"ASC-Datenmenge passt nicht zum Header in {os.path.basename(path)} "
            f"({grid.size} Werte, erwartet {ncols * nrows})."
        )
    grid = grid.reshape(nrows, ncols)

    xs = x0 + np.arange(ncols) * cell
    ys = y0 + np.arange(nrows)[::-1] * cell  # oberste Zeile = größtes Y
    xx, yy = np.meshgrid(xs, ys)

    # NODATA raus – auch wenn NODATA_value als NaN geschrieben wurde
    mask = np.isfinite(grid) & (grid != nodata)
    points = np.column_stack([xx[mask], yy[mask], grid[mask]])
    if points.size == 0:
        raise ValueError(f"Nur NODATA-Werte in {os.path.basename(path)}.")
    return points


def load_dgm_files(paths, log=print, bounds=None, margin=100.0):
    """Lädt DGM-Kacheln (XYZ/ASC, auch .gz) -> ndarray (N, 3).

    Mit bounds=(min_x, max_x, min_y, max_y) wird jede Kachel direkt nach dem
    Einlesen zugeschnitten – hält den Speicherbedarf auch bei vielen Kacheln klein.
    """
    chunks = []
    total_raw = 0
    for p in paths:
        name = os.path.basename(p)
        base = name[:-3] if name.lower().endswith(".gz") else name
        ext = os.path.splitext(base)[1].lower()
        log(f"Lese DGM-Kachel: {name} ...")
        if ext == ".asc":
            pts = _parse_asc(p)
        else:  # .xyz / .txt / .csv / unbekannt -> XYZ-Versuch
            pts = _parse_xyz(p)
        pts = _finite_only(pts)
        total_raw += len(pts)
        if bounds is not None:
            pts = crop_points(pts, bounds, margin=margin)
            log(f"  {len(pts):,} Punkte im Zielbereich".replace(",", "."))
        else:
            log(f"  {len(pts):,} Punkte".replace(",", "."))
        if len(pts):
            chunks.append(pts)
    if not paths:
        raise ValueError("Keine DGM-Dateien angegeben.")
    if not chunks:
        if bounds is not None and total_raw > 0:
            raise ValueError(
                "DGM-Kacheln und GML-Gebäude überlappen sich nicht. "
                "Bitte prüfen, ob Kacheln und GML zum selben Gebiet gehören.")
        raise ValueError("Keine verwertbaren DGM-Punkte gefunden.")
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


def thin_points(points, max_points=MAX_TERRAIN_POINTS, seed=0):
    """Dünnt isotrop auf höchstens max_points aus (Zufallsauswahl, reproduzierbar).

    Bewusst KEIN Schrittweiten-Sampling: auf zeilenweise sortierten Rasterkacheln
    erzeugt ein Stride starke Streifen (z. B. 16 m x 1 m statt ~4 m x 4 m).
    """
    n = len(points)
    if n <= max_points:
        return points
    rng = np.random.default_rng(seed)
    idx = rng.choice(n, size=max_points, replace=False)
    idx.sort()
    return points[idx]


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
    """Komplettpfad: Kacheln laden (mit Zuschnitt je Kachel) -> ausdünnen -> Mesh.

    Rückgabe: (mesh, anzahl_verwendeter_punkte)
    """
    bounds = None
    if gml_path:
        bounds = gml_bounds(gml_path)
        log(f"Zuschnitt auf Gebäudebereich (+{int(margin)} m Rand)")

    points = load_dgm_files(dgm_paths, log=log, bounds=bounds, margin=margin)
    log(f"DGM gesamt: {len(points):,} Punkte".replace(",", "."))

    points = thin_points(points, max_points=max_points)
    log(f"Für Mesh verwendet: {len(points):,} Punkte".replace(",", "."))
    mesh = terrain_mesh(points)
    log(f"Geländemesh: {mesh.n_cells:,} Dreiecke".replace(",", "."))
    return mesh, len(points)
