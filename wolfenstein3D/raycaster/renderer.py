
from .raycaster import Raycaster
from .aux_math import BASIS, plain_dot, plain_normalize
import pygame
from .textures import WALL_TEXTURES


RED = (255, 0, 0)


class PointLight:
    def __init__(self, pos):
        self.pos = pos
        
class DirectionLight:
    def __init__(self, pos, dir):
        self.pos = pos
        self.dir = dir


class RayRenderer:
    def __init__(self, raycaster: Raycaster, pgsurface: pygame.Surface):
        self.raycaster = raycaster
        self.pgsurface = pgsurface
        self.width, self.height = pgsurface.get_size()
        self.column_width = self.width // self.raycaster.observer.ray_count
        self.max_distance = self.raycaster.map.max_distance
        self.wall_width = raycaster.map.wall_width
        self.repeat = self.width // self.raycaster.observer.ray_count

    def distance_to_height(self, d, scaler):
        return (self.height / d) * scaler

    def cast(self):
        self.raycaster.raycast()

    def lamberts_cosine(self, coll, light: PointLight):
        pos, vertical, _ = coll
        n = BASIS[vertical]
        light_to_coll = (light.pos[0] - pos[0],
                         light.pos[1] - pos[1])
        light_to_coll = plain_normalize(light_to_coll)
        return abs(plain_dot(n, light_to_coll))

    def get_texture_col(self, coll, repeat, height, factor):
        offset = coll[0][~coll[1] + 2] % self.wall_width
        texture = WALL_TEXTURES[coll[2]-1]
        # map to 0 to len(columns)
        ci = offset / self.wall_width * (texture.width - 1)
        return texture.get_column(round(ci),
                                  int(repeat), int(height), factor)
        
    def render_sprites(self):
        pass
    
    def render_GUI(self):
        pass
    
    def render_walls(self, light):
        hh = self.height // 2
        for i, d in enumerate(self.raycaster.distance_buffer):
            coll = self.raycaster.collisions[i]
            start = self.repeat * i
            chh = self.distance_to_height(d, scaler=10) // 2
            cosine = self.lamberts_cosine(coll, light)
            column = self.get_texture_col(coll, self.repeat, chh*2, cosine)
            self.pgsurface.blit(column, (start, hh - chh))

    def render(self, light: PointLight):
        self.render_walls(light)
        self.render_sprites()
        self.render_GUI()
        
        
