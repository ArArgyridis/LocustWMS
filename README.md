Locust WMS

To run it from terminal:

python LocustMapServerImporter.py path_to_data wms_url

usage from Python:

from LocustMapServerImporter import LocustMapServerImporter

imptr = LocustMapServerImporter(path_to_data, wms_url)
imptr.process()
