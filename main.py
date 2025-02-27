import math
from API import getPlaceInfo, getHeightInfo, get_location, lat_lngTOxy
from threading import Thread
import pygame

z = 9
lat, lng = get_location(input('Choose a city in Australia (blank for Sydney) > ') or 'Sydney')
x, y = lat_lngTOxy(lat, lng, z)

pygame.init()
WIN = pygame.display.set_mode((800, 800))

placesInf = {}
SZE = 512

def getInf(x, y, z):
    inf = getPlaceInfo(x, y, z)
    inf.sort(key=lambda x: x['importance'])
    heightsur = getHeightInfo(x, y, z)
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
    WIDTH = 3
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
            pygame.draw.circle(sur, col, (shp['coords'][0] * SZE, shp['coords'][1] * SZE), WIDTH//2)
    
    heightsur.blit(sur, (0, 0))
    placesInf[(x, y, z)] = heightsur

def drawInf(x, y, z):
    placesInf[(x, y, z)] = None
    Thread(target=getInf, args=(x, y, z), daemon=True).start()

run = True
while run:
    for evnt in pygame.event.get():
        if evnt.type == pygame.QUIT:
            run = False
        elif evnt.type == pygame.KEYDOWN:
            if evnt.key == pygame.K_ESCAPE:
                run = False
            elif evnt.key == pygame.K_COMMA:
                if z > 1:
                    z -= 1
                    x /= 2
                    y /= 2
            elif evnt.key == pygame.K_PERIOD:
                z += 1
                x *= 2
                y *= 2
    
    ks = pygame.key.get_pressed()
    if ks[pygame.K_UP]:
        y -= 0.01
    elif ks[pygame.K_DOWN]:
        y += 0.01
    if ks[pygame.K_LEFT]:
        x -= 0.01
    elif ks[pygame.K_RIGHT]:
        x += 0.01
    
    WIN.fill((255, 255, 255))
    for yoff in (1, 2, 0):
        for xoff in (1, 2, 0):
            pos = (math.floor(x)+xoff, math.floor(y)+yoff, math.floor(z))
            if pos not in placesInf:
                pygame.display.update()
                drawInf(*pos)
            elif placesInf[pos] is not None:
                WIN.blit(placesInf[pos], (xoff*SZE-(x%1)*SZE, yoff*SZE-(y%1)*SZE))

    pygame.display.update()
