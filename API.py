import requests
import io
import math
import pygame
import re
from typing import Tuple, Iterable
import xml.etree.ElementTree as ET

__all__ = [
    'check_online',
    'get_location',
    'planetDataPth',
    'planetDataFile',
    'getPlaceInfo',
    'lat_lngTOxy'
]

BASE_URL = 'https://api.openstreetmap.org'
NOMINATIM_URL = 'https://nominatim.openstreetmap.org'
NOMINATIM_HEADERS = {
    'User-Agent': 
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'
}
VERSION = 0.6

def check_online() -> None:
    """
    Checks if the servers are running and if it is the right version.
    """
    # Send request & parse XML
    resp = requests.get(BASE_URL+'/api/capabilities')
    resp.raise_for_status()
    xml = resp.text
    root = ET.fromstring(xml)
    api = root.find('api')
    # Check version compatability
    versionData = api.find('version').attrib
    if not (float(versionData['minimum']) <= VERSION <= float(versionData['maximum'])):
        raise ValueError(
            f'Version {VERSION} is not supported by openstreetmap! Versions must be between (inclusive) "{versionData["minimum"]}"-"{versionData["maximum"]}".'
        )
    # Check status
    statusData = api.find('status').attrib
    offs = [i for i in statusData if statusData[i] != 'online']
    if offs:
        raise requests.HTTPError(
            "\n".join([
                f'Openstreetmap\'s {nme} is {val}!' for nme, val in statusData.items() if val != 'online'
            ])
        )
    
    resp = requests.get(NOMINATIM_URL+'/status', headers=NOMINATIM_HEADERS)
    if resp.status_code == 500:
        raise requests.HTTPError(
            resp.text
        )
    resp.raise_for_status()

def get_location(city: str, country: str = 'Australia') -> Tuple[float | None, float | None]:
    """
    Gets the latitude and longitude of a city.

    Args:
        city (str): The city to find the latitude and longitude of.
        country (str, optional): The country which contains the city. Defaults to 'Australia'.

    Returns:
        float | None, float | None: The latitude, longitude of the city (or None if unknown)
    """
    resp = requests.get(NOMINATIM_URL+f'/search?format=xml&country={country.replace(" ", "%20")}&city={city.replace(" ", "%20")}', headers=NOMINATIM_HEADERS)
    resp.raise_for_status()
    xml = resp.text
    root = ET.fromstring(xml)
    for elm in root.iter('place'):
        vals = elm.attrib
        return float(vals['lat']), float(vals['lon'])
    return None, None

def lat_lngTOxy(lat, lng, zoom, partial=False):
    # Thanks to https://stackoverflow.com/questions/37464824/converting-longitude-latitude-to-tile-coordinates !
    x = (lng+180)/360*pow(2, zoom)
    y = (1-math.log(math.tan(lat*math.pi/180) + 1/math.cos(lat*math.pi/180))/math.pi)/2*pow(2,zoom)
    if partial:
        return x, y
    return math.floor(x), math.floor(y)

def planetDataPth(path: str) -> Iterable[str]:
    resp = requests.get('http://download.openstreetmap.fr/polygons/'+path)
    resp.raise_for_status()
    html = resp.text
    a = re.findall(r'<a href="([^"?/][^"]*)">', html)
    return a

def planetDataFile(path: str) -> str:
    resp = requests.get('http://download.openstreetmap.fr/polygons/'+path)
    resp.raise_for_status()
    return resp.text

def getPlaceInfo(x, y, z):
    def fix_coords(coords):
        if isinstance(coords[0], (int, float)) and len(coords) == 2:
            x2, y2 = lat_lngTOxy(coords[1], coords[0], zoom=z, partial=True)
            return [min(max(x2-x, 0), 1), min(max(y2-y, 0), 1)]
        return [fix_coords(i) for i in coords]
    assert z <= 16
    
    #                                                               /tilesize/layers
    resp = requests.get(f'https://tile.nextzen.org/tilezen/vector/v1/512/all/{z}/{x}/{y}.json?api_key=dmlO1fVQRPKI-GrVIYJ1YA', headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0', # For avoiding cloudfare
        'Origin': 'https://tangrams.github.io', # For working
        'Connection': 'keep-alive' # For speed
    })
    resp.raise_for_status()
    Dcoded = resp.json()
    IMPORTANCE = [
        'water',
        'boundaries',
        'roads',
        'buildings',
        'places',
        'pois',
    ]
    out = []
    for featureGroup in Dcoded:
        for feature in Dcoded[featureGroup]['features']:
            if feature['properties'].get('min_zoom', 0) <= z:
                out.append({
                    'type': feature['geometry']['type'], 
                    'coords': fix_coords(feature['geometry']['coordinates']), 
                    'importance': -1 if featureGroup not in IMPORTANCE else IMPORTANCE.index(featureGroup),
                    'group': featureGroup,
                    'kind': feature['properties']['kind'],
                    'name': feature['properties'].get('name', '') # source, operator?
                })
    return out

def getHeightInfo(x, y, z):
    assert z <= 14
    
    resp = requests.get(f'https://tile.nextzen.org/tilezen/terrain/v1/512/terrarium/{z}/{x}/{y}.png?api_key=dmlO1fVQRPKI-GrVIYJ1YA', headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0', # For avoiding cloudfare
        'Origin': 'https://tangrams.github.io', # For working
        'Connection': 'keep-alive' # For speed
    })
    resp.raise_for_status()
    return pygame.image.load(io.BytesIO(resp.content))
