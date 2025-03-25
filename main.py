from queue import Empty, Queue
import pygame
from objs import Mesh, surfaceToTexture
from API import get_location, lat_lngTOxy, getPlaceInfo, getHeightInfo, cityChooser, getTotMoney, getPropertyPrice
from OpenGL.GL import *  # noqa: F403
from OpenGL.GLU import gluPerspective
from functools import lru_cache
from threading import Thread

city, country = cityChooser()
print(country+' total money:', getTotMoney(country))
print(country+' apartment price:', getPropertyPrice(country))

# Initialize Pygame and OpenGL
pygame.init()
display = (1200, 900)
screen = pygame.display.set_mode(display, pygame.DOUBLEBUF | pygame.OPENGL)

glEnable(GL_DEPTH_TEST)
glEnable(GL_LIGHTING)
glShadeModel(GL_SMOOTH)
glEnable(GL_COLOR_MATERIAL)
glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
glEnable(GL_LIGHT0)
glLightfv(GL_LIGHT0, GL_AMBIENT, [0.5, 0.5, 0.5, 1])
glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1])

glMatrixMode(GL_PROJECTION)
gluPerspective(45, display[0]/display[1], 0.1, 50.0)

glMatrixMode(GL_MODELVIEW)

RHO = 40
CHUNKSZE = 13
hei = 5
z = 12
startHei = 4
glTranslate(-CHUNKSZE//2, -startHei, -CHUNKSZE//2)
glRotatef(-RHO, 1.0, 0.0, 0.0)

viewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)
glLoadIdentity()

lat, lng, bbx = get_location(city, country)
if lat is None or lng is None:
    raise ValueError(
        f'Place "{city}", "{country}" cannot be found!'
    )
x, y = lat_lngTOxy(lat, lng, z)
startx, starty = x, y
SZE = 512
@lru_cache
def genMesh(x, y, z, Q):
    inf = getPlaceInfo(x, y, z)
    heightsur = getHeightInfo(x, y, z)
    inf.sort(key=lambda x: x['importance'])
    realHei = pygame.Surface((SZE, SZE))
    realHei.blit(heightsur, (0, 0))
    
    COL_D = {
        'water': (10, 50, 255),
        'earth': (10, 255, 50),
        'places': (255, 50, 50),
        'pois': (255, 50, 50),
        'transit': (90, 60, 100),
        'boundaries': (0, 0, 0),
        'roads': (255, 255, 50),
        'landuse': (155, 130, 10),
        'buildings': (125, 125, 125),
        'other': (255, 50, 255)
    }
    WIDTH = 5
    def drawShp(shp, sur, col):
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
    
    for shp in inf:
        if shp['group'] == 'water':
            drawShp(shp, realHei, 0)
        if shp['group'] in COL_D:
            col = COL_D[shp['group']]
        else:
            col = COL_D['other']
        drawShp(shp, heightsur, col)

    fact = (SZE//CHUNKSZE, SZE//CHUNKSZE)
    def getAt(x, y):
        if x == CHUNKSZE-1:
            x2 = realHei.get_width()-1
        else:
            x2 = x*fact[0]+CHUNKSZE//2
        if y == CHUNKSZE-1:
            y2 = 0
        else:
            y2 = SZE-(y*fact[1]+CHUNKSZE//2)
        px = realHei.get_at((x2, y2))
        if px[1] > 200:
            outh = 0
        else:
            outh = px[1]/255
        return max(outh, 0)*hei-hei

    Q.put([
        ((x-startx)*(CHUNKSZE-1), (starty-y)*(CHUNKSZE-1), 0),
        [[getAt(x, y) for x in range(CHUNKSZE)] for y in range(CHUNKSZE)],
        pygame.image.tobytes(heightsur, 'RGB')
    ])

class progressMesh:
    def __init__(self, x, y, z):
        self.Q = Queue()
        self.pro = Thread(target=genMesh, args=(x, y, z, self.Q), daemon=True)
        self.pro.start()
    
    def render(self):
        try:
            pos, arr, sur = self.Q.get()
        except Empty:
            return
        objs.remove(self)
        objs.append(Mesh(
            pos, arr, texture=surfaceToTexture(pygame.image.frombytes(sur, (SZE, SZE), 'RGB'))
        ))

objs = [
    progressMesh(x, y, z),

    progressMesh(x+1, y, z),
    progressMesh(x-1, y, z),
    progressMesh(x, y+1, z),
    progressMesh(x, y-1, z),

    progressMesh(x+1, y+1, z),
    progressMesh(x-1, y-1, z),
    progressMesh(x-1, y+1, z),
    progressMesh(x+1, y-1, z),
]

paused = False
run = True
clock = pygame.time.Clock()
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            run = False
        if event.type == pygame.KEYDOWN and event.key in [pygame.K_PAUSE, pygame.K_p]:
            paused = not paused

    keypress = pygame.key.get_pressed()
    
    if not paused:
        glLoadIdentity()

        glPushMatrix()
        glLoadIdentity()

        # Movement controls
        move_speed = 0.5
        if keypress[pygame.K_w]:
            glRotatef(RHO, 1.0, 0.0, 0.0)
            glTranslate(0, 0, move_speed)
            glRotatef(-RHO, 1.0, 0.0, 0.0)
        if keypress[pygame.K_s]:
            glRotatef(RHO, 1.0, 0.0, 0.0)
            glTranslate(0, 0, -move_speed)
            glRotatef(-RHO, 1.0, 0.0, 0.0)
        if keypress[pygame.K_d]:
            glTranslate(-move_speed, 0, 0)
        if keypress[pygame.K_a]:
            glTranslate(move_speed, 0, 0)
        if keypress[pygame.K_COMMA]:
            glTranslate(0, 0, move_speed)
        if keypress[pygame.K_PERIOD]:
            glTranslate(0, 0, -move_speed)

        glMultMatrixf(viewMatrix)
        viewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        glPopMatrix()
        glMultMatrixf(viewMatrix)
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        
        glEnable(GL_TEXTURE_2D)
        for obj in objs:
            obj.render()
        glDisable(GL_TEXTURE_2D)

        glPopMatrix()
        
        pygame.display.flip()
        clock.tick(60)

pygame.quit()
