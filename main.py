from API import getPlaceInfo
import pygame
pygame.init()
WIN = pygame.display.set_mode((800, 800))

def drawInf():
    inf = getPlaceInfo()
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

drawInf()
pygame.time.delay(60000)
