import xml.etree.ElementTree as ET
import ifcopenshell
import ifcopenshell.guid
import time

# CityGML Namespaces anpassen, falls Deine Datei andere nutzt
ns = {
    'gml': 'http://www.opengis.net/gml',
    'core': 'http://www.opengis.net/citygml/1.0',
    'bldg': 'http://www.opengis.net/citygml/building/1.0'
}

def convert_gml_to_ifc(input_path, output_path, terrain=None):
    """
    Liest eine CityGML-Datei mit beliebig vielen Gebäuden ein.
    Für jedes <bldg:Building> wird ein IfcBuildingElementProxy erzeugt
    und als IfcFacetedBrep (IfcClosedShell) abgelegt.

    input_path darf None sein, wenn terrain übergeben wird – dann entsteht
    eine reine Gelände-IFC ohne Gebäude.

    Koordinaten werden um (min_x, min_y, min_z) verschoben; die Verschiebung
    ist im IfcMapConversion dokumentiert (Eastings/Northings/OrthogonalHeight).

    Optional: terrain=(vertices, faces) fügt ein Gelände (DGM) als
    IfcGeographicElement mit IfcTriangulatedFaceSet hinzu.
    vertices: Punktliste (N, 3) in denselben absoluten Koordinaten wie die GML;
    faces: Dreiecksindizes (M, 3), 0-basiert. Gebäude und Gelände werden um
    denselben Offset verschoben und passen dadurch exakt zusammen.
    """

    # 1) GML parsen (optional – ohne GML entsteht eine reine Gelände-IFC)
    root = None
    buildings = []
    all_coords = []
    if input_path:
        from citygml_converter.z0_converter import parse_citygml
        tree = parse_citygml(input_path)
        root = tree.getroot()

        buildings = root.findall('.//core:cityObjectMember/bldg:Building', ns)
        if not buildings:
            print("Keine <bldg:Building> gefunden (CityGML 1.0 erwartet) – "
                  "es wird keine IFC-Datei geschrieben.")
            return

        # Alle Koordinaten sammeln, um min_x/min_y/min_z zu bestimmen
        for bldg in buildings:
            bounded_by_list = bldg.findall('.//bldg:boundedBy', ns)
            for bb in bounded_by_list:
                if len(bb) == 0:
                    continue
                surface_elem = bb[0]  # z.B. GroundSurface, WallSurface, RoofSurface
                polygons = surface_elem.findall('.//gml:Polygon', ns)
                for poly in polygons:
                    exterior = poly.find('.//gml:exterior', ns)
                    if exterior is None:
                        continue
                    posList = exterior.find('.//gml:posList', ns)
                    if posList is None or not posList.text:
                        continue
                    coords = [float(c) for c in posList.text.strip().split()]
                    for i in range(0, len(coords), 3):
                        all_coords.append((coords[i], coords[i+1], coords[i+2]))

        if not all_coords:
            print("Keine Koordinaten gefunden.")
            return
    elif terrain is None:
        print("Weder Gebäude-GML noch Gelände angegeben – nichts zu tun.")
        return

    min_x = min_y = min_z = float("inf")
    if all_coords:
        min_x = min(c[0] for c in all_coords)
        min_y = min(c[1] for c in all_coords)
        min_z = min(c[2] for c in all_coords)

    # Gelände in den gemeinsamen Offset einbeziehen, damit Gebäude und
    # Gelände im IFC exakt zusammenpassen (Gelände liegt i.d.R. tiefer).
    if terrain is not None:
        t_vertices, t_faces = terrain
        if len(t_vertices) > 0:
            min_x = min(min_x, float(min(v[0] for v in t_vertices)))
            min_y = min(min_y, float(min(v[1] for v in t_vertices)))
            min_z = min(min_z, float(min(v[2] for v in t_vertices)))

    if min_x == float("inf"):
        print("Keine verwertbare Geometrie gefunden – es wird keine IFC-Datei geschrieben.")
        return

    # 2) IFC-Datei erstellen
    ifc_file = ifcopenshell.file(schema="IFC4")

    # (A) IFC-Organisation, Person, Application
    org = ifc_file.create_entity("IfcOrganization",
        Identification="IAI/KIT", 
        Name="Research University Karlsruhe"
    )
    person = ifc_file.create_entity("IfcPerson",
        Identification="IAI/KIT",
        FamilyName="IAI/KIT"
    )
    person_org = ifc_file.create_entity("IfcPersonAndOrganization",
        ThePerson=person,
        TheOrganization=org
    )
    app = ifc_file.create_entity("IfcApplication",
        ApplicationDeveloper=org,
        Version="Version 7.3.0",
        ApplicationFullName="KITModelViewer",
        ApplicationIdentifier="KITModelViewer"
    )
    now_unix = int(time.time())
    owner_history = ifc_file.create_entity("IfcOwnerHistory",
        OwningUser=person_org,
        OwningApplication=app,
        State="READWRITE",
        ChangeAction="NOCHANGE",
        LastModifiedDate=now_unix
    )

    # (B) IfcProject
    project = ifc_file.create_entity("IfcProject",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="CityGML Project"
    )

    # (C) IfcGeometricRepresentationContext
    origin = ifc_file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
    axis2placement = ifc_file.create_entity("IfcAxis2Placement3D", Location=origin)
    dir2d = ifc_file.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0))
    geom_context = ifc_file.create_entity("IfcGeometricRepresentationContext",
        ContextIdentifier=None,
        ContextType="Model",
        CoordinateSpaceDimension=3,
        Precision=1e-5,
        WorldCoordinateSystem=axis2placement,
        TrueNorth=dir2d
    )

    # -> IFCProjectedCRS (optional, z.B. EPSG:25833)
    projected_crs = ifc_file.create_entity("IfcProjectedCRS",
        Name="EPSG:25833",
        Description="ETRS89 / UTM Zone 33N"
    )

    # (D) IfcMapConversion – OrthogonalHeight ist in IFC4 Pflicht und
    # dokumentiert die Z-Verschiebung (mit Gelände ist min_z variabel)
    map_conversion = ifc_file.create_entity("IfcMapConversion",
        SourceCRS=geom_context,
        TargetCRS=projected_crs,
        Eastings=min_x,
        Northings=min_y,
        OrthogonalHeight=min_z,
        XAxisAbscissa=1.0,
        XAxisOrdinate=0.0,
        Scale=1.0
    )

    project.RepresentationContexts = [geom_context]

    # (E) IfcSIUnit (Meter, etc.)
    length_unit = ifc_file.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
    area_unit   = ifc_file.create_entity("IfcSIUnit", UnitType="AREAUNIT", Name="SQUARE_METRE")
    vol_unit    = ifc_file.create_entity("IfcSIUnit", UnitType="VOLUMEUNIT", Name="CUBIC_METRE")
    unit_assignment = ifc_file.create_entity("IfcUnitAssignment", Units=[area_unit, length_unit, vol_unit])
    project.UnitsInContext = unit_assignment

    # (F) IfcSite
    site_placement_origin = ifc_file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
    site_placement = ifc_file.create_entity("IfcAxis2Placement3D", Location=site_placement_origin)
    site_local_placement = ifc_file.create_entity("IfcLocalPlacement",
        PlacementRelTo=None,
        RelativePlacement=site_placement
    )
    site = ifc_file.create_entity("IfcSite",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="core:CityModel",
        ObjectPlacement=site_local_placement,
        CompositionType="ELEMENT"
    )
    ifc_file.create_entity("IfcRelAggregates",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        RelatingObject=project,
        RelatedObjects=[site]
    )

    # GML-Name in PropertySet
    gml_name_elem = root.find('.//gml:name', ns) if root is not None else None
    if gml_name_elem is not None and gml_name_elem.text:
        prop_name = ifc_file.create_entity("IfcPropertySingleValue",
            Name="gml:name",
            NominalValue=ifc_file.create_entity("IfcLabel", gml_name_elem.text)
        )
        pset_citymodel = ifc_file.create_entity("IfcPropertySet",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner_history,
            Name="GML PropertySet",
            HasProperties=[prop_name]
        )
        ifc_file.create_entity("IfcRelDefinesByProperties",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner_history,
            RelatedObjects=[site],
            RelatingPropertyDefinition=pset_citymodel
        )

    # 3) Gebäude
    for bldg in buildings:
        bldg_id = bldg.get('{http://www.opengis.net/gml}id') or "UnknownID"

        function_elem = bldg.find('.//bldg:function', ns)
        roofType_elem = bldg.find('.//bldg:roofType', ns)
        creationDate_elem = bldg.find('.//core:creationDate', ns)
        measuredHeight_elem = bldg.find('.//bldg:measuredHeight', ns)

        # Alle Polygone
        polygons = []
        bounded_by_list = bldg.findall('.//bldg:boundedBy', ns)
        for bb in bounded_by_list:
            if len(bb) == 0:
                continue
            surface_elem = bb[0]
            poly_list = surface_elem.findall('.//gml:Polygon', ns)
            for poly in poly_list:
                exterior = poly.find('.//gml:exterior', ns)
                if exterior is None:
                    continue
                posList = exterior.find('.//gml:posList', ns)
                if posList is None or not posList.text:
                    continue
                coords = [float(c) for c in posList.text.strip().split()]
                poly_points = []
                for i in range(0, len(coords), 3):
                    # Verschiebung um (min_x, min_y, min_z)
                    x = coords[i]   - min_x
                    y = coords[i+1] - min_y
                    z = coords[i+2] - min_z
                    poly_points.append((x, y, z))
                polygons.append(poly_points)

        if not polygons:
            print(f"Keine Polygone im Building {bldg_id} gefunden.")
            continue

        # IfcBuildingElementProxy
        proxy_placement_origin = ifc_file.create_entity("IfcCartesianPoint", Coordinates=(0.,0.,0.))
        proxy_placement = ifc_file.create_entity("IfcAxis2Placement3D", Location=proxy_placement_origin)
        proxy_local_placement = ifc_file.create_entity("IfcLocalPlacement",
            PlacementRelTo=site_local_placement,
            RelativePlacement=proxy_placement
        )
        proxy = ifc_file.create_entity("IfcBuildingElementProxy",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner_history,
            Name=f"bldg:Building_{bldg_id}",
            ObjectPlacement=proxy_local_placement
        )

        # Geometrie -> IfcFacetedBrep
        # IfcPolyLoop verlangt paarweise verschiedene Punkte: den CityGML-
        # Schlusspunkt (erster == letzter) und Folge-Duplikate entfernen,
        # degenerierte Loops überspringen – strenge Importer (z. B. Archicad)
        # verwerfen sonst den ganzen Körper
        faces = []
        for poly_points in polygons:
            pts = list(poly_points)
            if len(pts) >= 2 and pts[0] == pts[-1]:
                pts.pop()
            cleaned = []
            for pt in pts:
                if not cleaned or cleaned[-1] != pt:
                    cleaned.append(pt)
            if len(cleaned) < 3:
                continue
            cpoints = [ifc_file.create_entity("IfcCartesianPoint", Coordinates=pt) for pt in cleaned]
            poly_loop = ifc_file.create_entity("IfcPolyLoop", Polygon=cpoints)
            face_outer_bound = ifc_file.create_entity("IfcFaceOuterBound", Bound=poly_loop, Orientation=True)
            face = ifc_file.create_entity("IfcFace", Bounds=[face_outer_bound])
            faces.append(face)

        if not faces:
            print(f"Keine gültigen Flächen im Building {bldg_id} – übersprungen.")
            continue
        closed_shell = ifc_file.create_entity("IfcClosedShell", CfsFaces=faces)
        faceted_brep = ifc_file.create_entity("IfcFacetedBrep", Outer=closed_shell)

        shape_rep = ifc_file.create_entity("IfcShapeRepresentation",
            ContextOfItems=geom_context,
            RepresentationIdentifier="Body",
            RepresentationType="Brep",
            Items=[faceted_brep]
        )
        product_def_shape = ifc_file.create_entity("IfcProductDefinitionShape",
            Representations=[shape_rep]
        )
        proxy.Representation = product_def_shape

        # GML-Attribute in PropertySet
        props = []
        if function_elem is not None and function_elem.text:
            p_function = ifc_file.create_entity("IfcPropertySingleValue",
                Name="bldg:function",
                NominalValue=ifc_file.create_entity("IfcLabel", function_elem.text)
            )
            props.append(p_function)
        if roofType_elem is not None and roofType_elem.text:
            p_roof = ifc_file.create_entity("IfcPropertySingleValue",
                Name="bldg:roofType",
                NominalValue=ifc_file.create_entity("IfcLabel", roofType_elem.text)
            )
            props.append(p_roof)
        if creationDate_elem is not None and creationDate_elem.text:
            p_creation = ifc_file.create_entity("IfcPropertySingleValue",
                Name="core:creationDate",
                NominalValue=ifc_file.create_entity("IfcLabel", creationDate_elem.text)
            )
            props.append(p_creation)
        if measuredHeight_elem is not None and measuredHeight_elem.text:
            val = measuredHeight_elem.text
            uom = measuredHeight_elem.get('uom')
            if uom:
                val += f" [{uom.split(':')[-1]}]"
            p_height = ifc_file.create_entity("IfcPropertySingleValue",
                Name="bldg:measuredHeight",
                NominalValue=ifc_file.create_entity("IfcLabel", val)
            )
            props.append(p_height)

        if props:
            pset = ifc_file.create_entity("IfcPropertySet",
                GlobalId=ifcopenshell.guid.new(),
                OwnerHistory=owner_history,
                Name="GML PropertySet",
                HasProperties=props
            )
            ifc_file.create_entity("IfcRelDefinesByProperties",
                GlobalId=ifcopenshell.guid.new(),
                OwnerHistory=owner_history,
                RelatedObjects=[proxy],
                RelatingPropertyDefinition=pset
            )

        # Site -> Proxy
        ifc_file.create_entity("IfcRelAggregates",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner_history,
            RelatingObject=site,
            RelatedObjects=[proxy]
        )

    # 4) Optionales Gelände (DGM) als IfcGeographicElement
    if terrain is not None:
        t_vertices, t_faces = terrain
        if len(t_vertices) >= 3 and len(t_faces) > 0:
            print(f"Füge Gelände hinzu: {len(t_vertices)} Punkte, {len(t_faces)} Dreiecke ...")
            coord_list = [
                (float(v[0]) - min_x, float(v[1]) - min_y, float(v[2]) - min_z)
                for v in t_vertices
            ]
            point_list = ifc_file.create_entity("IfcCartesianPointList3D",
                CoordList=coord_list
            )
            # IFC-Indizes sind 1-basiert
            coord_index = [(int(f[0]) + 1, int(f[1]) + 1, int(f[2]) + 1) for f in t_faces]
            tfs = ifc_file.create_entity("IfcTriangulatedFaceSet",
                Coordinates=point_list,
                CoordIndex=coord_index,
                Closed=False
            )
            terrain_shape = ifc_file.create_entity("IfcShapeRepresentation",
                ContextOfItems=geom_context,
                RepresentationIdentifier="Body",
                RepresentationType="Tessellation",
                Items=[tfs]
            )
            terrain_pds = ifc_file.create_entity("IfcProductDefinitionShape",
                Representations=[terrain_shape]
            )
            terrain_placement = ifc_file.create_entity("IfcLocalPlacement",
                PlacementRelTo=site_local_placement,
                RelativePlacement=ifc_file.create_entity("IfcAxis2Placement3D",
                    Location=ifc_file.create_entity("IfcCartesianPoint",
                                                    Coordinates=(0.0, 0.0, 0.0))
                )
            )
            terrain_elem = ifc_file.create_entity("IfcGeographicElement",
                GlobalId=ifcopenshell.guid.new(),
                OwnerHistory=owner_history,
                Name="Gelände (DGM)",
                ObjectPlacement=terrain_placement,
                Representation=terrain_pds,
                PredefinedType="TERRAIN"
            )
            ifc_file.create_entity("IfcRelAggregates",
                GlobalId=ifcopenshell.guid.new(),
                OwnerHistory=owner_history,
                RelatingObject=site,
                RelatedObjects=[terrain_elem]
            )
        else:
            if not buildings:
                print("Gelände ohne verwertbare Geometrie und keine Gebäude – "
                      "es wird keine IFC-Datei geschrieben.")
                return
            print("Warnung: Gelände übergeben, aber ohne verwertbare Geometrie – übersprungen.")

    # 5) IFC-Datei speichern
    ifc_file.write(output_path)
    print("GML->IFC Konvertierung erfolgreich abgeschlossen.")
    print(f"Datei gespeichert in: {output_path}")
