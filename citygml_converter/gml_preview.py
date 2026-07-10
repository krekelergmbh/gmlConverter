import xml.etree.ElementTree as ET
import pyvista as pv

def parse_gml_to_multiblock(gml_path: str) -> pv.MultiBlock:
    """
    Liest eine CityGML-Datei und erzeugt ein PyVista MultiBlock-Objekt.
    Für jedes <cityObjectMember> (Gebäude) wird ein einziges PolyData erstellt:
      - Alle <gml:Polygon> im Gebäude werden gesammelt.
      - Ring-Schluss wird entfernt (falls erster == letzter Punkt).
      - Keine Toleranz, kein Triangulate, kein globales Merging.
    Am Ende liegt jedes Gebäude als ein eigener Block in MultiBlock.

    Ausgabe:
      - Anzahl Buildings (Gebäude)
    """

    from citygml_converter.z0_converter import parse_citygml
    tree = parse_citygml(gml_path)
    root = tree.getroot()

    ns = {
        'gml':  'http://www.opengis.net/gml',
        'core': 'http://www.opengis.net/citygml/1.0',
        'bldg': 'http://www.opengis.net/citygml/building/1.0',
        'gen':  'http://www.opengis.net/citygml/generics/1.0'
    }

    city_objects = root.findall('.//core:cityObjectMember', ns)

    multi_block = pv.MultiBlock()
    building_count = 0

    for obj in city_objects:
        polygons = obj.findall('.//gml:Polygon', ns)
        if not polygons:
            continue

        # Sammle Punkte/Faces in diesem Gebäude
        sub_points = []
        sub_faces = []
        current_index = 0
        valid_poly_count = 0

        for poly in polygons:
            pos_elem = poly.find('.//gml:posList', ns)
            if pos_elem is None or not pos_elem.text:
                continue

            floats = [float(c) for c in pos_elem.text.strip().split()]
            coords = []
            for i in range(0, len(floats), 3):
                coords.append((floats[i], floats[i+1], floats[i+2]))

            # Ring-Schluss entfernen
            if len(coords) > 1 and coords[0] == coords[-1]:
                coords.pop()

            n = len(coords)
            if n < 3:
                continue  # Kein valider Polygon

            # Indizes für dieses Polygon
            face_indices = list(range(current_index, current_index + n))
            face = [n] + face_indices

            sub_points.extend(coords)
            sub_faces.extend(face)
            current_index += n
            valid_poly_count += 1

        # Falls in diesem Gebäude keine validen Polygone => skip
        if valid_poly_count == 0:
            continue

        # PolyData für dieses Gebäude
        building_poly = pv.PolyData(sub_points)
        try:
            building_poly.faces = sub_faces
        except Exception:
            # Falls PyVista meckert => Polygon zu komplex
            continue

        # Falls Mesh leer => skip
        if building_poly.n_points == 0:
            continue

        multi_block.append(building_poly)
        building_count += 1

    print("Buildings:", building_count)
    return multi_block
