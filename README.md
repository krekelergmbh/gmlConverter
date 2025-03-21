#gmlConverter
"gmlConverter" ist ein Python‑Tool zur Verarbeitung und Konvertierung von CityGML‑Dateien. Das Projekt bietet eine grafische Oberfläche (GUI) zum:

- Auswählen von GML‑Dateien über eine interaktive Karte (Pick GML)
- Anpassen der Z‑Koordinaten (z0 Converter), sodass Gebäude bei Z=0 liegen
- Konvertieren von CityGML in das IFC‑Format (GML2IFC)
- Zusammenführen mehrerer GML‑Dateien (Merge GML)
- Vorschau und 3D‑Visualisierung der CityGML‑Modelle (Preview)

Features
Interaktive Deutschlandkarte ("Pick GML")
Der Tab "Pick GML" zeigt eine Karte der deutschen Bundesländer. Beim Überfahren mit der Maus werden die Bundesländer hervorgehoben, und ein Klick öffnet den entsprechenden Geoportal‑Link, um CityGML‑Daten zu beziehen.

Z‑Koordinatenanpassung ("z0 Converter")
Mit diesem Feature werden die minimalen Z‑Werte aus den GML‑Dateien ermittelt, sodass die Gebäudeansicht bei Z=0 ausgerichtet wird.

Konvertierung in IFC ("GML2IFC")
Die CityGML‑Gebäudedaten werden in das IFC‑Format umgerechnet. Dabei wird für jedes Gebäude ein IfcBuildingElementProxy erstellt, das als IfcFacetedBrep abgelegt wird. Zudem werden die Koordinaten entsprechend angepasst und in einem IfcMapConversion‑Objekt dokumentiert.

Zusammenführen von GML‑Dateien ("Merge GML")
Mehrere CityGML‑Dateien können zu einer einzigen konsolidierten GML‑Datei zusammengeführt werden. Dabei werden die boundingBox‑Informationen neu berechnet und Fortschrittsinformationen ausgegeben.

3D‑Vorschau und Visualisierung ("Preview")
Mit Hilfe von PyVista werden GML‑Daten eingelesen, in ein MultiBlock‑Objekt umgewandelt und als 3D‑Mesh angezeigt. Zusätzliche Widgets ermöglichen verschiedene Ansichten (Top, Front, Isometric) und interaktive Steuerung des Modells.

Kontakt
Für Fragen, Anregungen oder Fehlerberichte wende Dich bitte an maximilian.woharek@krekeler-architekten.de
