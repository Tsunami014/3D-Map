import requests
import zipfile
import io
import math
import pygame
import mapbox_vector_tile
import os
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

def lat_lngTOxy(lat, lng, zoom):
    return math.floor((lng+180)/360*pow(2, zoom)), \
        (math.floor((1-math.log(math.tan(lat*math.pi/180) + 1/math.cos(lat*math.pi/180))/math.pi)/2*math.pow(2,zoom)))

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

def getLand():
    if not os.path.exists('cache/landPolys.zip'):
        print('Downloading land polygons... (will take a very long time, go get a coffee)')
        resp = requests.get('https://osmdata.openstreetmap.de/download/land-polygons-split-3857.zip')
        resp.raise_for_status()
        if not os.path.exists('cache/'):
            os.mkdir('cache')
        with open('cache/landPolys.zip', 'wb+') as f:
            f.write(resp.content)
    # zf = zipfile.ZipFile('cache/landPolys.zip', "r")

def getPlaceInfo(x, y, z):
    def fix_coords(coords, coordFixingFunc):
        if isinstance(coords, int):
            return coordFixingFunc(coords)
        elif isinstance(coords[0], int) and len(coords) == 2:
            return [coordFixingFunc(coords[0]), 1-coordFixingFunc(coords[1])]
        return [fix_coords(i, coordFixingFunc) for i in coords]
    assert z <= 16
    
    #                                                               /tilesize/layers
    resp = requests.get(f'https://tile.nextzen.org/tilezen/vector/v1/512/all/{z}/{x}/{y}.mvt?api_key=dmlO1fVQRPKI-GrVIYJ1YA', headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0', # For avoiding cloudfare
        'Origin': 'https://tangrams.github.io', # For working
        'Connection': 'keep-alive' # For speed
    })
    resp.raise_for_status()
    Dcoded = mapbox_vector_tile.decode(resp.content)
    IMPORTANCE = {
        'water': 1,
        'boundaries': 2,
        'roads': 3,
        'places': 4
    }
    out = []
    for featureGroup in Dcoded:
        for feature in Dcoded[featureGroup]['features']:
            coords = fix_coords(feature['geometry']['coordinates'], lambda num: num/Dcoded[featureGroup]['extent'])
            out.append({
                'type': feature['geometry']['type'], 
                'coords': coords, 
                'importance': -1 if featureGroup not in IMPORTANCE else IMPORTANCE[featureGroup],
                'group': featureGroup,
                'kind': feature['properties']['kind'],
                'name': feature["properties"].get('name', '')
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
