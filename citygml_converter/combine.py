import xml.etree.ElementTree as ET

ns = {
    'gml':  'http://www.opengis.net/gml',
    'core': 'http://www.opengis.net/citygml/1.0',
    'bldg': 'http://www.opengis.net/citygml/building/1.0',
    'gen':  'http://www.opengis.net/citygml/generics/1.0'
}

def combine_gml_files(file_list, output_path, progress_callback=None):
    """
    Kombiniert mehrere CityGML-Dateien zu einer einzigen GML-Datei.
    Ruft progress_callback(i+1, len(file_list)) nach jeder Datei auf,
    falls progress_callback übergeben wurde.
    """

    if not file_list:
        print("Keine Eingabedateien angegeben, Abbruch.")
        return

    citymodel_tag = '{http://www.opengis.net/citygml/1.0}CityModel'
    root = ET.Element(citymodel_tag)

    gml_name = ET.SubElement(root, '{http://www.opengis.net/gml}name')
    gml_name.text = "Combined_CityModel"

    boundedBy = ET.SubElement(root, '{http://www.opengis.net/gml}boundedBy')
    envelope = ET.SubElement(boundedBy, '{http://www.opengis.net/gml}Envelope', {
        'srsName': 'urn:adv:crs:ETRS89_UTM32*DE_DHHN2016_NH'
    })

    lowerCorner = ET.SubElement(envelope, '{http://www.opengis.net/gml}lowerCorner', {
        'srsDimension': '3'
    })
    upperCorner = ET.SubElement(envelope, '{http://www.opengis.net/gml}upperCorner', {
        'srsDimension': '3'
    })

    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')

    total = len(file_list)
    for i, f in enumerate(file_list):
        # CityGML parsen
        tree = ET.parse(f)
        in_root = tree.getroot()

        # boundingBox
        in_bounded = in_root.find('.//gml:boundedBy', ns)
        if in_bounded is not None:
            in_envelope = in_bounded.find('.//gml:Envelope', ns)
            if in_envelope is not None:
                in_lower = in_envelope.find('.//gml:lowerCorner', ns)
                in_upper = in_envelope.find('.//gml:upperCorner', ns)
                if in_lower is not None and in_upper is not None:
                    try:
                        lower_vals = [float(v) for v in in_lower.text.strip().split()]
                        upper_vals = [float(v) for v in in_upper.text.strip().split()]
                        lx, ly, lz = lower_vals
                        ux, uy, uz = upper_vals
                        if lx < min_x: min_x = lx
                        if ly < min_y: min_y = ly
                        if lz < min_z: min_z = lz
                        if ux > max_x: max_x = ux
                        if uy > max_y: max_y = uy
                        if uz > max_z: max_z = uz
                    except:
                        print("Warnung: boundingBox parsing fehlgeschlagen, ignoriere")

        # cityObjectMember
        com_list = in_root.findall('.//core:cityObjectMember', ns)
        for com in com_list:
            root.append(com)

        # Fortschritt melden
        if progress_callback:
            progress_callback(i + 1, total)

    # Falls keine boundingBox gefunden
    if min_x == float('inf'):
        min_x = min_y = min_z = 0.0
        max_x = max_y = max_z = 100.0

    lowerCorner.text = f"{min_x} {min_y} {min_z}"
    upperCorner.text = f"{max_x} {max_y} {max_z}"

    # Schreiben
    ET.ElementTree(root).write(output_path, encoding='utf-8', xml_declaration=True)
    # Keine weitere Ausgabe
