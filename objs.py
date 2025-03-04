from typing import Iterable
import pygame
from functools import lru_cache
from OpenGL.GL import *  # noqa: F403

def tex_coord(x, y, n=4):
    """Calculate texture coordinates for a given (x, y) position in an n x n texture atlas."""
    m = 1.0 / n
    dx, dy = x * m, y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m

@lru_cache
def loadTexture(name, nearest=False):
    """Load and configure a texture from an image file."""
    textureSurface = pygame.transform.flip(pygame.image.load(f'textures/{name}.png'), True, False)
    textureData = pygame.image.tostring(textureSurface, "RGBA", 1)
    width, height = textureSurface.get_size()

    glEnable(GL_TEXTURE_2D)
    texid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texid)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, textureData)

    # Set texture parameters for wrapping and filtering
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    if nearest:
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    else:
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)
    return texid

class Obj:
    def __init__(self, texture=None):
        self.textureId = loadTexture(texture) if texture is not None else None

    tex_coords: Iterable[Iterable[float]]

    verts: Iterable[Iterable[float]]

    # Define edges for wireframe rendering
    edges: Iterable[Iterable[int]]
    """A tuple of indices referring to the verts() function, which returns the cube's corner points

    What idx of vertex (in the verts func) goes for each edge of the shape"""

    # Define surfaces for solid rendering
    surfaces: Iterable[Iterable[int]]
    """A tuple of indices referring to the verts() function, which returns the cube's corner points

    What idx of vertex (in the verts func) goes for each solid surface (face)"""

    def render(self):
        if self.textureId is not None:
            glBindTexture(GL_TEXTURE_2D, self.textureId)
            block = self.tex_coords
        glBegin(GL_QUADS)
        for i, surface in enumerate(self.surfaces):
            for j, vertex in enumerate(surface):
                if self.textureId is not None:
                    glTexCoord2f(block[i][2*j], block[i][2*j+1])
                glVertex3fv(self.verts[vertex])
        glEnd()
        
        glBegin(GL_LINES)
        glColor4f(0.5, 0.5, 0.5, 1)
        for edge in self.edges:
            for vertex in edge:
                glVertex3fv(self.verts[vertex])
        glEnd()

class Plane:
    def __init__(self, corner, width, height):
        self.corner = corner
        self.size = (width, height)
    
    def render(self):
        glColor4f(0.5, 0.5, 0.5, 1)
        glBegin(GL_QUADS)
        glVertex3f(*self.corner)
        glVertex3f(self.corner[0]+self.size[0], self.corner[1], self.corner[2])
        glVertex3f(self.corner[0]+self.size[0], self.corner[1]+self.size[1], self.corner[2])
        glVertex3f(self.corner[0], self.corner[1]+self.size[0], self.corner[2])
        glEnd()

class Cube(Obj):
    def __init__(self, x, y, z, texture=None):
        self.x, self.y, self.z = x, y, z
        super().__init__(texture)
    
    @property
    def tex_coords(self):
        # Top, bottom, side*4
        return [tex_coord(0, 0), tex_coord(1, 0)] + [tex_coord(2, 0)] * 4

    @property
    def verts(self):
        # Return the 8 corner vertices of a cube centered at (x, y, z).
        return (
            (1+self.x, -1+self.y, -1+self.z), (1+self.x, 1+self.y, -1+self.z), (-1+self.x, 1+self.y, -1+self.z), (-1+self.x, -1+self.y, -1+self.z),
            (1+self.x, -1+self.y, 1+self.z), (1+self.x, 1+self.y, 1+self.z), (-1+self.x, -1+self.y, 1+self.z), (-1+self.x, 1+self.y, 1+self.z)
        )

    edges = ((0,1), (0,3), (0,4), (2,1), (2,3), (2,7), (6,3), (6,4), (6,7), (5,1), (5,4), (5,7))

    surfaces = ((0,1,2,3), (3,2,7,6), (6,7,5,4), (4,5,1,0), (1,5,7,2), (4,0,3,6))

class Mesh(Obj):
    def __init__(self, corner, heights, sze=1, texture=None):
        self.ps = [[
            (corner[0] + x*sze, corner[1] + y*sze, corner[2] + heights[y][x])
            for x in range(len(heights[y]))
        ] for y in range(len(heights))]
        super().__init__(texture)
    
    @property
    def edges(self):
        def conv(x, y):
            return x + y * len(self.ps[0])
        return [
            (conv(x, y), conv(x+1, y)) for y in range(len(self.ps)-1) for x in range(len(self.ps[y])-1)
        ] + [
            (conv(x, y), conv(x, y+1)) for y in range(len(self.ps)-1) for x in range(len(self.ps[y])-1)
        ]
    
    @property
    def surfaces(self):
        def conv(x, y):
            return x + y * len(self.ps[0])
        return (
            (conv(x, y), conv(x, y+1), conv(x+1, y+1), conv(x+1, y)) for y in range(len(self.ps)-1) for x in range(len(self.ps[y])-1)
        )
    
    @property
    def tex_coords(self):
        return [tex_coord(0, 0, 1) for _ in range((len(self.ps)-1)*(len(self.ps[0])-1))]
    
    @property
    def verts(self):
        return [j for i in self.ps for j in i]
