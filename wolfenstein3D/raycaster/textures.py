

from PIL import Image
import pygame
import numpy as np
import os


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



