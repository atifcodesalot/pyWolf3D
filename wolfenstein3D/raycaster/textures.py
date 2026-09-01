

from PIL import Image
import pygame
import numpy as np
import os


TEXTURE_PATH = os.path.join('.', 'textures')


class Texture:
    def __init__(self, image: Image.Image):
        image = image.convert("RGBA")

        self.width, self.height = image.size

        self.surface = pygame.image.frombytes(
            image.tobytes(),
            image.size,
            "RGBA",
        )

        self.columns = [
            self.surface.subsurface((x, 0, 1, self.height)).copy()
            for x in range(self.width)
        ]

    def get_column(self, i, repeat, height):
        return pygame.transform.scale(self.columns[i], (repeat, height))


def init_wall_textures():
    global WALL_TEXTURES
    WALL_TEXTURES = []
    wall_size = (128, 128)
    ww, wh = wall_size
    texture_layout = (6, 6)
    walls = Image.open(os.path.join(TEXTURE_PATH, 'wallmap.png'))
    for i in range(texture_layout[0]):
        for j in range(texture_layout[1]):
            WALL_TEXTURES.append(
                Texture(walls.crop((i*ww, j*wh, (i+1)*ww, (j+1)*wh)))
            )


def init_textures():
    init_wall_textures()
    # init more textures in the future


init_textures()
