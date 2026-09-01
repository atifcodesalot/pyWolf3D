
from .raycaster import Raycaster
from .aux_math import BASIS, plain_dot, plain_normalize
import pygame
from .textures import WALL_TEXTURES


RED = (255, 0, 0)


class PointLight:
    def __init__(self, pos):
        self.pos = pos


class RayRenderer:
    def __init__(self, raycaster: Raycaster, pgsurface: pygame.Surface):
        self.raycaster = raycaster
        self.pgsurface = pgsurface
        self.width, self.height = pgsurface.get_size()
        self.column_width = self.width // self.raycaster.observer.ray_count
        self.max_distance = self.raycaster.map.max_distance
        self.wall_width = raycaster.map.wall_width

    def distance_to_height(self, d, scaler):
        return (self.height / d) * scaler

    def cast(self):
        self.raycaster.raycast()

    def lamberts_cosine(self, coll, light: PointLight):
        pos, vertical = coll
        n = BASIS[vertical]
        light_to_coll = (light.pos[0] - pos[0],
                         light.pos[1] - pos[1])
        light_to_coll = plain_normalize(light_to_coll)
        return abs(plain_dot(n, light_to_coll))

    def get_texture(self, coll, repeat, height):
        offset = coll[0][~coll[1] + 2] % self.wall_width
        texture = WALL_TEXTURES[coll[2]-1]
        # map to 0 to len(columns)
        ci = offset / self.wall_width * (texture.width - 1)
        return texture.get_column(round(ci), int(repeat), int(height))

    def render(self, light: PointLight):
        # placeholder
        cw = self.column_width
        hh = self.height // 2
        for i, d in enumerate(self.raycaster.distance_buffer):
            coll = self.raycaster.collisions[i]
            start = cw * i
            chh = self.distance_to_height(d, scaler=10) // 2
            # cosine = self.lamberts_cosine(coll, light)
            column = self.get_texture(coll, cw, chh*2)
            self.pgsurface.blit(column, (start, hh - chh))
            # pygame.draw.line(self.pgsurface, (RED[0] * cosine, RED[1] * cosine, RED[2] * cosine),
            #                  (start, hh + chh), (start, hh - chh), width=cw)
