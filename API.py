import requests
import io
import math
import pygame
from threading import Thread
from typing import Tuple, Iterable
import xml.etree.ElementTree as ET

__all__ = [
    'get_location',
    'lat_lngTOxy',
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


placesInf = {}
SZE = 512
WHITES = [pygame.Surface((SZE, SZE)), pygame.Surface((SZE*2, SZE*2))]
WHITES[0].fill((255, 50, 50))
WHITES[1].fill((255, 50, 50))

def drawInf(x, y, z):
    try:
        inf = getPlaceInfo(x, y, z)
        heightsur = getHeightInfo(x, y, z)
    except AssertionError:
        placesInf[(x, y, z)] = WHITES
        return
    except Exception:
        placesInf.pop((x, y, z))
        return
    inf.sort(key=lambda x: x['importance'])
    sur = pygame.Surface((SZE, SZE), pygame.SRCALPHA)
    
    COL_D = {
        'water': (10, 50, 255),
        'earth': (10, 255, 50),
        'places': (255, 50, 50),
        'pois': (255, 50, 50),
        'transit': (90, 60, 100),
        'boundaries': (0, 0, 0),
        'roads': (255, 255, 50),
        'landuse': (155, 130, 10, 200),
        'buildings': (125, 125, 125),
        'other': (255, 50, 255)
    }
    WIDTH = 5
    for shp in inf:
        if shp['group'] == 'earth':
            continue
        if shp['group'] in COL_D:
            col = COL_D[shp['group']]
        else:
            col = COL_D['other']
        if shp['type'] == 'MultiPolygon':
            for poly in shp['coords']:
                pygame.draw.polygon(sur, col, [[i[0]*SZE, i[1]*SZE] for i in poly[0]])
        elif shp['type'] == 'Polygon':
            pygame.draw.polygon(sur, col, [[i[0]*SZE, i[1]*SZE] for i in shp['coords'][0]])
        elif shp['type'] == 'LineString':
            pygame.draw.lines(sur, col, False, [[i[0]*SZE, i[1]*SZE] for i in shp['coords']], WIDTH)
        elif shp['type'] == 'MultiLineString':
            for ln in shp['coords']:
                pygame.draw.lines(sur, col, False, [[i[0]*SZE, i[1]*SZE] for i in ln], WIDTH)
        elif shp['type'] == 'Point':
            pygame.draw.circle(sur, col, (shp['coords'][0] * SZE, shp['coords'][1] * SZE), WIDTH)
    
    heightsur.blit(sur, (0, 0))
    placesInf[(x, y, z)] = (heightsur, pygame.transform.scale2x(heightsur))

def getInf(x, y, z, block=False):
    pos = (x, y, z)
    if pos not in placesInf:
        if block:
            drawInf(*pos)
        else:
            placesInf[pos] = None
            Thread(target=drawInf, args=pos, daemon=True).start()
    
    if placesInf[pos] is not None:
        return placesInf[pos][0]
    elif pos[2] > 1:
        pos2 = (math.floor(pos[0]/2), math.floor(pos[1]/2), pos[2]-1)
        if pos2 in placesInf and placesInf[pos2] is not None:
            xoff2 = int((pos[0]/2)%1 == 0.5)
            yoff2 = int((pos[1]/2)%1 == 0.5)
            sect = placesInf[pos2][1].subsurface(xoff2*SZE, yoff2*SZE, SZE, SZE)
            return sect
