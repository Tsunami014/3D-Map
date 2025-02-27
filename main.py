import math
from API import getPlaceInfo
from threading import Thread
import pygame
pygame.init()
WIN = pygame.display.set_mode((800, 800))

x, y, z = 27, 18, 5

placesInf = {}
SZE = 600

def getInf(x, y, z):
    inf = getPlaceInfo(x, y, z)
    sur = pygame.Surface((SZE, SZE))
    sur.fill((255, 255, 255))
    COL_D = {
        'water': (10, 50, 255),
        'earth': (10, 255, 50),
        'places': (255, 50, 50),
        'transit': (90, 60, 100),
        'boundaries': (0, 0, 0),
        'roads': (255, 255, 50),
        'landuse': (155, 130, 10),
        'other': (255, 50, 255)
    }
    WIDTH = 10
    for shp in inf:
        sec, *_ = shp['desc'].split(':')
        if sec in COL_D:
            col = COL_D[sec]
        else:
            col = COL_D['other']
        match shp['type']:
            case 'MultiPolygon':
                for poly in shp['coords']:
                    pygame.draw.polygon(sur, col, [[i[0]*SZE, i[1]*SZE] for i in poly[0]])
            case 'Polygon':
                pygame.draw.polygon(sur, col, [[i[0]*SZE, i[1]*SZE] for i in shp['coords'][0]])
            case 'LineString':
                pygame.draw.lines(sur, col, False, [[i[0]*SZE, i[1]*SZE] for i in shp['coords']], WIDTH)
            case 'MultiLineString':
                for ln in shp['coords']:
                    pygame.draw.lines(sur, col, False, [[i[0]*SZE, i[1]*SZE] for i in ln], WIDTH)
            case 'Point':
                pygame.draw.circle(sur, col, (shp['coords'][0] * SZE, shp['coords'][1] * SZE), WIDTH//2)
    placesInf[(x, y, z)] = sur

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
                z -= 1
            elif evnt.key == pygame.K_PERIOD:
                z += 1
    
    ks = pygame.key.get_pressed()
    if ks[pygame.K_UP]:
        y += 0.01
    elif ks[pygame.K_DOWN]:
        y -= 0.01
    elif ks[pygame.K_LEFT]:
        x -= 0.01
    elif ks[pygame.K_RIGHT]:
        x += 0.01
    
    WIN.fill((255, 255, 255))
    for yoff in (-1, 0, 1):
        for xoff in (-1, 0, 1):
            pos = (math.floor(x)+xoff, math.floor(y)-yoff, math.floor(z))
            if pos not in placesInf:
                pygame.display.update()
                drawInf(*pos)
            elif placesInf[pos] is not None:
                WIN.blit(placesInf[pos], (xoff*SZE-(x%1)*SZE, yoff*SZE+(y%1)*SZE))

    pygame.display.update()
