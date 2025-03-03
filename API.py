import requests
import io
import math
import pygame
import re
from typing import Tuple, Iterable
import xml.etree.ElementTree as ET

__all__ = [
    'get_location',
    'lat_lngTOxy',
    'planetDataPth',
    'planetDataFile',
    'getPlaceInfo',
    'getHeightInfo'
]

def get_location(city: str, country: str = 'Australia') -> Tuple[float | None, float | None, Iterable[float] | None]:
    """
    Gets the latitude and longitude of a city.

    Args:
        city (str): The city to find the latitude and longitude of.
        country (str, optional): The country which contains the city. Defaults to 'Australia'.

    Returns:
        float | None: The latitude of the city (or None if unknown)
        float | None: The longitude of the city (or None if unknown)
        list[float] | None: The bounding box of the city; in [min lat, max lat, min long, max long] (or None if unknown)
    """
    resp = requests.get(f'https://nominatim.openstreetmap.org/search?format=xml&country={country.replace(" ", "%20")}&city={city.replace(" ", "%20")}', headers={
            'User-Agent': 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'
        })
    resp.raise_for_status()
    xml = resp.text
    root = ET.fromstring(xml)
    for elm in root.iter('place'):
        vals = elm.attrib
        return float(vals['lat']), float(vals['lon']), [float(i) for i in vals['boundingbox'].split(',')]
    return None, None, None

def lat_lngTOxy(lat, lng, zoom, partial=False):
    # Thanks to https://stackoverflow.com/questions/37464824/converting-longitude-latitude-to-tile-coordinates !
    x = (lng+180)/360*pow(2, zoom)
    y = (1-math.log(math.tan(lat*math.pi/180) + 1/math.cos(lat*math.pi/180))/math.pi)/2*pow(2,zoom)
    if partial:
        return x, y
    return math.floor(x), math.floor(y)

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
            if feature['properties'].get('min_zoom', 0) <= z or feature['geometry']['type'] == 'buildings':
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
