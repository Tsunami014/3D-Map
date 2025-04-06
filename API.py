import requests
import io
import math
import pygame
import re
from difflib import get_close_matches
from typing import Tuple, Iterable
import xml.etree.ElementTree as ET

__all__ = [
    'cityChooser',
    'get_location',
    'lat_lngTOxy',
    'getPlaceInfo',
    'getHeightInfo',
    'getTotMoney',
    'getPropertyPrice'
]

def _checkInps(**kwargs) -> None:
    """
    Ensures inputs are of the correct type

    Args:
        **kwargs (str: Iterable[object, type]): The arguments to check in format: `name=(object, ExpectedType)` 

    Raises:
        ValueError: If inputs are not of the correct type
    """
    diff = {}
    for name, (val, xpected) in kwargs.items():
        if not isinstance(val, xpected):
            diff[name] = (str(xpected), type(val))
    if diff != {}:
        raise ValueError(
            '\n'.join(
                f'Arg {n} should be of type {t[0]}, instead found {t[1]}!'
                for n, t in diff.items()
            )
        )

def cityChooser() -> Tuple[str, str]:
    """
    Asks for input to choose a city!

    Returns:
        tuple[str, str]: A tuple in the form `(city, country)`
    """
    chosen = (input('Choose a city (blank for "Sydney Australia") > ') or 'Sydney Australia').replace(',', ' ').replace('  ', ' ').strip()
    spl = chosen.split(' ')
    if len(spl) == 0:
        return 'Sydney', 'Australia'
    elif len(spl) == 1:
        return spl[0], 'Australia'
    return spl[0], ' '.join(spl[1:])

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
    _checkInps(city=(city, str), country=(country, str))
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

def lat_lngTOxy(lat: int|float, lng: int|float, zoom: int, partial: bool = False) -> Tuple[int|float|None, int|float|None]:
    """
    Translate a latitude and longitude into an x and y map coordinate with the specified zoom.

    Args:
        lat (int | float): The latitude of the position.
        lng (int | float): The longitude of the position.
        zoom (int): The zoom level.
        partial (bool, optional): Whether to return the exact x and y or the partial x and y (exact being integer, partial being float). Defaults to False.

    Returns:
        Tuple[int|float|None, int|float|None]: The output x and y coordinate, or None if it's out of bounds.
    """
    _checkInps(lat=(lat, (int, float)), lng=(lng, (int, float)), zoom=(zoom, int), partial=(partial, bool))
    if lat < -90 or lat > 90 or lng < -180 or lng > 180 or zoom < 0 or zoom > 23:
        return None, None
    # Thanks to https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames !
    lat_rad = math.radians(lat)
    n = 1 << zoom
    x = (lng + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    if partial:
        return x, y
    return math.floor(x), math.floor(y)

def _check_xyz(x: int, y: int, z: int) -> None:
    """
    Ensure an x, y, z map tile coordinate is in bounds

    Args:
        x: The x coordinate of the map tile
        y: The y coordinate of the map tile
        z: The zoom level

    Raises:
        ValueError: If the x and y map tile position is not in bounds
    """
    n = 1 << z
    if x < 0 or y < 0 or x >= n or y >= n:
        raise ValueError(
            f"Values for 'x' and 'y' should be between 0-{n}, instead found: [x: {x}, y: {y}]"
        )

def getPlaceInfo(x: int, y: int, z: int) -> Iterable:
    """
    Get information about an x, y, z map tile

    Args:
        x: The x coordinate of the map tile
        y: The y coordinate of the map tile
        z: The zoom level

    Returns:
        Iterable[Dict]: A list of features in dict format.
    """
    _checkInps(x=(x, int), y=(y, int), z=(z, int))
    if z < 0 or z > 16:
        raise ValueError(
            f'Zoom must be between 0-16, found {z}!'
        )
    _check_xyz(x, y, z)
    
    def fix_coords(coords):
        if isinstance(coords[0], (int, float)) and len(coords) == 2:
            x2, y2 = lat_lngTOxy(coords[1], coords[0], zoom=z, partial=True)
            return [min(max(x2-x, 0), 1), min(max(y2-y, 0), 1)]
        return [fix_coords(i) for i in coords]
    
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

def getHeightInfo(x: int, y: int, z: int) -> pygame.Surface:
    """
    Gets a pygame surface of the heightmap at a certain tile x, y, z

    Args:
        x: The x coordinate of the map tile
        y: The y coordinate of the map tile
        z: The zoom level

    Returns:
        pygame.Surface: The heightmap image
    """
    _checkInps(x=(x, int), y=(y, int), z=(z, int))
    if z < 0 or z > 14:
        raise ValueError(
            f'Zoom must be between 0-14, found {z}!'
        )
    _check_xyz(x, y, z)
    
    resp = requests.get(f'https://tile.nextzen.org/tilezen/terrain/v1/512/terrarium/{z}/{x}/{y}.png?api_key=dmlO1fVQRPKI-GrVIYJ1YA', headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0', # For avoiding cloudfare
 'Origin': 'https://tangrams.github.io', # For working
        'Connection': 'keep-alive' # For speed
    })
    resp.raise_for_status()
    return pygame.image.load(io.BytesIO(resp.content))

def getTotMoney(country: str) -> int|None:
    """
    Get the total amount of money in a country

    Args:
        country: The country in question

    Returns:
        int|None: The amount of money the gov has (or None if not found)
    """
    _checkInps(country=(country, str))
    resp = requests.get('https://datacatalogapi.worldbank.org/dexapps/efi/metadata/countries?country='+country.replace(' ', '+'))
    resp.raise_for_status()
    vals = resp.json()['value']
    if not vals:
        return None
    ISO3 = vals[0]['ISO3']
    resp = requests.get('https://datacatalogapi.worldbank.org/dexapps/efi/data?datasetId=IMF.GFSMAB&indicatorIds=IMF.GFSMAB.GANW_G14_XDC&top=1&attribute1=Local%20governments&attribute2=Billions&countryCodes='+ISO3)
    resp.raise_for_status()
    year = 0
    val = None
    values = resp.json()['value']
    if not values:
        return None
    for info in values:
        nyear = int(info['CAL_YEAR'].split('/')[-1])
        if nyear > year:
            val = info['IND_VALUE']
    return round(val * 1000000000) # It's in billions

def getPropertyPrice(country: str) -> int|None:
    """
    Gets the average price of a 2 bedroom apartment in a country

    Args:
        country: The country in question

    Returns:
        int|None: The price of a 2 bedroom apartment in the country, or None if not found.
    """
    _checkInps(country=(country, str))
    resp = requests.get('https://static.dwcdn.net/data/W1lDC.csv?v=1742769960000')
    resp.raise_for_status()
    dat = resp.text.split('\r\n')
    names = [j.split(',')[0] for j in dat[1:]]
    closest = get_close_matches(country, names, 1, 0.6)
    if not closest:
        return None
    country = closest[0]
    TwoBedroomApartmentPrice = re.findall(re.escape(country)+r',(?:(?:"[0-9,.]+")|[0-9,.]+),"?([0-9,.]+)"?,', '\n'.join(dat))[0]
    TwoBedroomApartmentPrice = int(TwoBedroomApartmentPrice.replace(',', ''))
    return TwoBedroomApartmentPrice
