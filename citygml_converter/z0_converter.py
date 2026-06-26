# z0_converter.py

import xml.etree.ElementTree as ET

# Angepasste Namespaces entsprechend Deiner GML-Datei
ns = {
    'gml': 'http://www.opengis.net/gml',
    'core': 'http://www.opengis.net/citygml/1.0',
    'bldg': 'http://www.opengis.net/citygml/building/1.0'
}

def convert_gml_to_z0(input_path, output_path):
    """
    Liest eine CityGML-Datei ein und zieht den minimalen Z-Wert des GroundSurface
    von allen Z-Koordinaten ab, damit das Gebäude bei Z=0 liegt.
    Speichert die angepasste Datei in 'output_path'.
    """
    tree = ET.parse(input_path)
    root = tree.getroot()
    building_count = 0
    updated_buildings = 0

    # Durchlaufe alle cityObjectMember (Gebäude)
    for cityObject in root.findall('.//core:cityObjectMember', ns):
        building_count += 1

        # Suche das Element GroundSurface innerhalb des Gebäudes
        ground_surface = cityObject.find('.//bldg:GroundSurface', ns)
        if ground_surface is None:
            continue

        # Suche das erste posList-Element innerhalb von GroundSurface
        poslist_element = ground_surface.find('.//gml:posList', ns)
        if poslist_element is None or not poslist_element.text:
            continue

        try:
            ground_coords = [float(c) for c in poslist_element.text.strip().split()]
        except ValueError:
            continue

        if len(ground_coords) < 3:
            continue

        # Bestimme den minimalen Z-Wert (jede dritte Zahl)
        min_z = min(ground_coords[2::3])

        # Alle posList-Elemente des aktuellen Gebäudes anpassen
        for posList in cityObject.findall('.//gml:posList', ns):
            if not posList.text:
                continue
            try:
                coords = [float(c) for c in posList.text.strip().split()]
            except ValueError:
                continue

            new_coords = []
            for i, value in enumerate(coords):
                # Jede dritte Zahl ist ein Z-Wert
                if (i + 1) % 3 == 0:
                    new_coords.append(value - min_z)
                else:
                    new_coords.append(value)

            posList.text = ' '.join(f'{c:.3f}' for c in new_coords)

        updated_buildings += 1

    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    print(f"Verarbeitet: {building_count} Gebäude, aktualisiert: {updated_buildings} Gebäude.")
