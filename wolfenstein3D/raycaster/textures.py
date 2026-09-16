

from PIL import Image
import pygame
import numpy as np
import os


TEXTURE_PATH = os.path.join('.', 'textures')


class Texture:
    def __init__(self, image: Image.Image):
        image = image.convert("RGBA")

        self.width, self.height = image.size
        self.half_height = self.height // 2

        self.surface = pygame.image.frombytes(
            image.tobytes(),
            image.size,
            "RGBA",
        )

        self.columns = [
            self.surface.subsurface((x, 0, 1, self.height)).copy()
            for x in range(self.width)
        ]

        self.shade_cache = {}

    def get_column(self, i, repeat, height, shade_factor, screen_height):
        column = self.shade(shade_factor, i)

        if height > screen_height:
            # clip before scaling
            off = screen_height / height * self.half_height
            column = column.subsurface(
                (0, self.half_height - off, 1, off*2))
            height = screen_height

        scaled = pygame.transform.scale(
            column, (repeat, height))
        return scaled

    def shade(self, factor, i):
        factor = max(0.0, min(1.0, factor))
        multiplier = round(255 * factor)

        shaded = self.columns[i].copy()
        shaded.fill(
            (multiplier, multiplier, multiplier),
            special_flags=pygame.BLEND_RGB_MULT,
        )
        return shaded


def init_wall_textures():
    global WALL_TEXTURES
    # 100 slot texture table
    WALL_TEXTURES = [None]*100
    wall_size = (128, 128)
    ww, wh = wall_size
    texture_layout = (6, 6)
    walls = Image.open(os.path.join(TEXTURE_PATH, 'wallmap.png'))
    for j in range(texture_layout[1]):
        for i in range(texture_layout[0]):
            WALL_TEXTURES[i + j*texture_layout[0]
                          ] = Texture(walls.crop((i*ww, j*wh, (i+1)*ww, (j+1)*wh)))

    WALL_TEXTURES[31 << 1] = WALL_TEXTURES[31]


def init_textures():
    init_wall_textures()
    # init more textures in the future


init_textures()
