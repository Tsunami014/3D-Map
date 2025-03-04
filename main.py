import math
from API import getPlaceInfo, getHeightInfo, get_location, lat_lngTOxy
from threading import Thread
import pygame

z = 9
lat, lng, bbx = get_location(input('Choose a city in Australia (blank for Sydney) > ') or 'Sydney')
x, y = lat_lngTOxy(lat, lng, z)
minmaxZoom = 9
minx, miny = lat_lngTOxy(bbx[0], bbx[2], minmaxZoom)
maxx, maxy = lat_lngTOxy(bbx[1], bbx[3], minmaxZoom)
x -= 1
y -= 1

pygame.init()
WIN = pygame.display.set_mode((1200, 900))

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
    WIDTH = 10
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
    placesInf[(x, y, z)] = (heightsur, pygame.transform.scale2x(heightsur))

run = True
clock = pygame.time.Clock()
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
    
    z = max(min(z, 14), 8)
    zf = 2**(z-minmaxZoom)
    x = max(min(x, maxx*zf+int(z>10)), minx*zf)
    y = max(min(y, miny*zf), maxy*zf)
    
    ks = pygame.key.get_pressed()
    if ks[pygame.K_UP]:
        y -= 0.03
    elif ks[pygame.K_DOWN]:
        y += 0.03
    if ks[pygame.K_LEFT]:
        x -= 0.03
    elif ks[pygame.K_RIGHT]:
        x += 0.03
    
    WIN.fill((255, 255, 255))
    for yoff in (1, 2, 0):
        for xoff in (1, 2, 0, 3):
            pos = (math.floor(x)+xoff, math.floor(y)+yoff, math.floor(z))
            if pos not in placesInf:
                pygame.display.update()
                placesInf[pos] = None
                Thread(target=drawInf, args=pos, daemon=True).start()
            
            if placesInf[pos] is not None:
                WIN.blit(placesInf[pos][0], (xoff*SZE-(x%1)*SZE, yoff*SZE-(y%1)*SZE))
            elif pos[2] > 1:
                pos2 = (math.floor(pos[0]/2), math.floor(pos[1]/2), pos[2]-1)
                if pos2 in placesInf and placesInf[pos2] is not None:
                    xoff2 = int((pos[0]/2)%1 == 0.5)
                    yoff2 = int((pos[1]/2)%1 == 0.5)
                    sect = placesInf[pos2][1].subsurface(xoff2*SZE, yoff2*SZE, SZE, SZE)
                    WIN.blit(sect, (xoff*SZE-(x%1)*SZE, yoff*SZE-(y%1)*SZE))

    pygame.display.update()
    clock.tick(30)
