import requests
import xml.etree.ElementTree as ET

BASE_URL = 'https://api.openstreetmap.org'
VERSION = 0.6

def check_online():
    """
    Checks if the server is running and if it is the right version.

    Raises:
        HTTPError: If the request did not succeed.
        ValueError: If the version is not supported by openstreetmap.
        HTTPError: If the API is not online.
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
