import pygame
from objs import Mesh, surfaceToTexture
from API import get_location, lat_lngTOxy, getHeightInfo, getInf
from OpenGL.GL import *  # noqa: F403
from OpenGL.GLU import gluPerspective

# Initialize Pygame and OpenGL
pygame.init()
display = (800, 600)
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
CHUNKSZE = 30
hei = 10
glTranslate(-CHUNKSZE//2, -12, 0)
glRotatef(-RHO, 1.0, 0.0, 0.0)

viewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)
glLoadIdentity()

z = 9
lat, lng, bbx = get_location('Sydney')
x, y = lat_lngTOxy(lat, lng, z)
def genMesh(x, y, z):
    map = getHeightInfo(x, y, z)
    sur = getInf(x, y, z, True)
    tx = surfaceToTexture(sur)
    fact = (map.get_width()//CHUNKSZE, map.get_height()//CHUNKSZE)
    return Mesh((0, 0, 0), [
        [map.get_at((x*fact[0], y*fact[1]))[1]/255*hei-hei for x in range(CHUNKSZE)] for y in range(CHUNKSZE)
    ], texture=tx)

objs = [
    genMesh(x, y, z)
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
        move_speed = 0.3
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

        glMultMatrixf(viewMatrix)
        viewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        glPopMatrix()
        glMultMatrixf(viewMatrix)
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        
        for obj in objs:
            obj.render()

        glPopMatrix()
        
        pygame.display.flip()
        clock.tick(60)

pygame.quit()
