import math
from typing import Iterable
import pygame
from OpenGL.GL import *  # noqa: F403

def tex_coord(x: int, y: int, n: int = 4) -> Iterable[float|int]:
    """
    Calculate texture coordinates for a given (x, y) position in an n x n texture atlas.

    Args:
        x (int): The x coordinate of the texture.
        y (int): The y coordinate of the texture.
        n (int): The amount of times to split the texture.
    """
    m = 1.0 / n
    dx, dy = x * m, y * m
    return dx, dy, dx, dy + m, dx + m, dy + m, dx + m, dy

def surfaceToTexture(sur: pygame.Surface, nearest: bool = False) -> int:
    """
    Turn a pygame surface into an openGL texture

    Args:
        sur: The surface to turn into a texture.
        nearest: Whether to use the nearest neighbour algorithm or use smoothing.

    Returns:
        The texture ID.
    """
    # Thanks to https://stackoverflow.com/questions/61396799/how-can-i-blit-my-pygame-game-onto-an-opengl-surface !
    textureData = pygame.image.tostring(sur, "RGBA", 1)
    width, height = sur.get_size()

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

class Mesh:
    def __init__(self, 
                 corner: Iterable[int],
                 heights: Iterable[Iterable[int]],
                 sze: int = 1,
                 texture: int|None = None
            ):
        """
        A Mesh object which renders the heightmap with an optional texture.

        Args:
            corner: The top left corner of the object.
            heights: The list of coordinate heights.
            sze: The distance between coordinates in the 3d space.
            texture: The texture ID (or None) to render.
        """
        self.ps = [[
            (corner[0] + x*sze, corner[1] + y*sze, corner[2] + heights[y][x])
            for x in range(len(heights[y]))
        ] for y in range(len(heights))]
        self.textureId = texture if texture is not None else None

    @property
    def tex_coords(self):
        amnt = (len(self.ps)-1)*(len(self.ps[0])-1)
        wid = math.floor(math.sqrt(amnt))
        return [tex_coord(i%wid, math.floor(i/wid), wid) for i in range(amnt)]

    @property
    def verts(self):
        return [j for i in self.ps for j in i]

    # Define surfaces for solid rendering
    @property
    def surfaces(self):
        def conv(x, y):
            return x + y * len(self.ps[0])
        return (
            (conv(x, y), conv(x, y+1), conv(x+1, y+1), conv(x+1, y)) for y in range(len(self.ps)-1) for x in range(len(self.ps[y])-1)
        )
    """A tuple of indices referring to the verts() function, which returns the cube's corner points

    What idx of vertex (in the verts func) goes for each solid surface (face)"""

    def render(self):
        if self.textureId is not None:
            glBindTexture(GL_TEXTURE_2D, self.textureId)
            block = self.tex_coords
        glBegin(GL_QUADS)
        vs = self.verts
        for i, surface in enumerate(self.surfaces):
            for j, vertex in enumerate(surface):
                if self.textureId is not None:
                    glTexCoord2f(block[i][2*j], block[i][2*j+1])
                glVertex3fv(vs[vertex])
        glEnd()
