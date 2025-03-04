import pygame
from objs import Cube
from OpenGL.GL import *  # noqa: F403
from OpenGL.GLU import gluPerspective, gluLookAt

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
gluLookAt(0, -8, 0, # Look from
          0, 0, -5, # Look at
          0, 0, 1 # Positive y up vector
)
viewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)
glLoadIdentity()

objs = [
    Cube(0, 0, 0)
]

paused = False
run = True
while run:
    mouseMove = [0, 0]
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
            glTranslate(0, -move_speed, move_speed)
        if keypress[pygame.K_s]:
            glTranslate(0, move_speed, -move_speed)
        if keypress[pygame.K_d]:
            glTranslate(-move_speed, 0, 0)
        if keypress[pygame.K_a]:
            glTranslate(move_speed, 0, 0)
        if keypress[pygame.K_LSHIFT]:
            glTranslate(0, 0.5, 0)
        if keypress[pygame.K_SPACE]:
            glTranslate(0, -0.5, 0)

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
        pygame.time.wait(10)

pygame.quit()
