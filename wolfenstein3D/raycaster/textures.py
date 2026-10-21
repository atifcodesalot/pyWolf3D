

from PIL import Image
import pygame


class Texture:
    def __init__(self, image: Image.Image, surf=None, converted=False, columns=None):  

        self.image = image.convert("RGBA") if not converted else image
        
        self.width, self.height = image.size
        self.half_height = self.height // 2

        self.surface = pygame.image.frombytes(
            self.image.tobytes(),
            self.image.size,
            "RGBA",
        ) if surf is None else surf

        self.columns = [
            self.surface.subsurface((x, 0, 1, self.height)).copy()
            for x in range(self.width)
        ] if columns is None else columns

    def scale_column(self, column, repeat, height, screen_height):
        if height > screen_height:
            # clip before scaling
            off = screen_height / height * self.half_height
            column = column.subsurface(
                (0, self.half_height - off, 1, off*2))
            height = screen_height
        height = max(height, 0)
        scaled = pygame.transform.scale(
            column, (repeat, height))
        return scaled

    def get_column(self, i, repeat, height, screen_height):
        column = self.columns[i]
        scaled = self.scale_column(column, repeat, height, screen_height)
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
