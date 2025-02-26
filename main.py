from API import getPlaceInfo
import pygame
pygame.init()
WIN = pygame.display.set_mode((800, 800))

x, y, z = 27, 18, 5

def drawInf(x, y, z):
    WIN.fill((255, 255, 255))
    pygame.display.update()
    inf = getPlaceInfo(x, y, z)
    sze = 600
    sur = pygame.Surface((sze, sze))
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
                    pygame.draw.polygon(sur, col, [[i[0]*sze, i[1]*sze] for i in poly[0]])
            case 'Polygon':
                pygame.draw.polygon(sur, col, [[i[0]*sze, i[1]*sze] for i in shp['coords'][0]])
            case 'LineString':
                pygame.draw.lines(sur, col, False, [[i[0]*sze, i[1]*sze] for i in shp['coords']], WIDTH)
            case 'MultiLineString':
                for ln in shp['coords']:
                    pygame.draw.lines(sur, col, False, [[i[0]*sze, i[1]*sze] for i in ln], WIDTH)
            case 'Point':
                pygame.draw.circle(sur, col, (shp['coords'][0] * sze, shp['coords'][1] * sze), WIDTH//2)
    WIN.blit(sur, (0, 0))
    pygame.display.update()

run = True
needsUpdating = True
while run:
    for evnt in pygame.event.get():
        if evnt.type == pygame.QUIT:
            run = False
        elif evnt.type == pygame.KEYDOWN:
            match evnt.key:
                case pygame.K_ESCAPE:
                    run = False
                case pygame.K_UP:
                    needsUpdating = True
                    y += 1
                case pygame.K_DOWN:
                    needsUpdating = True
                    y -= 1
                case pygame.K_LEFT:
                    needsUpdating = True
                    x -= 1
                case pygame.K_RIGHT:
                    needsUpdating = True
                    x += 1
                case pygame.K_COMMA:
                    needsUpdating = True
                    z -= 1
                case pygame.K_PERIOD:
                    needsUpdating = True
                    z += 1
    
    if needsUpdating:
        needsUpdating = False
        drawInf(x, y, z)
