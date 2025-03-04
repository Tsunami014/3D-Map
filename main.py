import math
from API import get_location, lat_lngTOxy, getInf, SZE
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
            sur = getInf(math.floor(x)+xoff, math.floor(y)+yoff, math.floor(z))
            if sur is not None:
                WIN.blit(sur, (xoff*SZE-(x%1)*SZE, yoff*SZE-(y%1)*SZE))

    pygame.display.update()
    clock.tick(30)
