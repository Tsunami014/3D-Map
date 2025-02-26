import requests
import re
from typing import Tuple, Iterable
import xml.etree.ElementTree as ET

__all__ = [
    'check_online',
    'get_location',
    'planetDataPth',
    'planetDataFile'
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
            f'Version {VERSION} is not supported by openstreetmap! Versions must be between (inclusive) "{versionData['minimum']}"-"{versionData['maximum']}".'
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
    resp = requests.get(NOMINATIM_URL+f'/search?format=xml&{country.replace(' ', '%20')}=Australia&city={city.replace(' ', '%20')}', headers=NOMINATIM_HEADERS)
    resp.raise_for_status()
    xml = resp.text
    root = ET.fromstring(xml)
    for elm in root.iter('place'):
        vals = elm.attrib
        return float(vals['lat']), float(vals['lon'])
    return None, None

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
