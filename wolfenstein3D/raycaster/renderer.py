
from .raycaster import Raycaster
from .aux_math import *
import pygame
from .textures import WALL_TEXTURES
from .sprites import Sprite


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

        self.sprites = []

    def add_sprite(self, sprite: Sprite):
        if type(sprite) is not Sprite:
            raise TypeError("Expected Sprite object")
        self.sprites.append(sprite)

    def distance_to_height(self, d, scaler):
        return (self.height / d) * scaler

    def cast(self):
        self.raycaster.raycast()

    def lamberts_cosine(self, coll, light: PointLight):
        pos, vertical, _ = coll
        n = BASIS[vertical]
        light_to_coll = plain_sub(pos, light.pos)
        light_to_coll = plain_normalize(light_to_coll)
        return abs(plain_dot(n, light_to_coll))

    def get_wall_col(self, coll, repeat, height, factor):
        offset = coll[0][~coll[1] + 2] % self.wall_width
        texture = WALL_TEXTURES[coll[2]-1]
        # map to 0 to len(columns)
        ci = offset / self.wall_width * (texture.width - 1)
        return texture.get_column(round(ci),
                                  int(repeat), int(height), factor)

    def sprite_is_visible(self, projected, sprite) -> bool:
        o = self.raycaster.observer
        shw = sprite.width // 2
        vpl = o.vp_length
        on_vp = vpl + shw > projected[0] > -vpl - shw 
        in_front = plain_dot(o.look_dir, plain_sub(o.pos, sprite.pos)) > 0
        return on_vp and in_front

    def draw_sprite(self, sprite: Sprite):
        hh = self.height // 2
        o = self.raycaster.observer
        db = self.raycaster.distance_buffer
        projected = sprite.project(o)
        if not self.sprite_is_visible(projected, sprite):
            return
        screen_pos = sprite.screen_pos(self, projected)
        perp_dist = plain_dot(plain_sub(o.pos, sprite.pos), o.look_dir)
        length = self.distance_to_height(perp_dist, scaler=10)
        sw = sprite.width
        start = screen_pos - (length//2) * self.repeat
        skip = sw / length
        for i in range(int(length)):
            col_pos = start + (i * self.repeat)
            # if the column isn't in screen width 
            if col_pos > self.width or col_pos < 0:
                continue
            # if there is a wall that is closer
            if db[int(col_pos // self.repeat)] < perp_dist:
                continue
            column = sprite.get_column(int(i*skip), self.repeat, length, 1)
            self.pgsurface.blit(
                column, (col_pos, hh - length//2))

    def render_sprites(self):
        for sprite in self.sprites:
            self.draw_sprite(sprite)

    def render_walls(self, light):
        hh = self.height // 2
        for i, d in enumerate(self.raycaster.distance_buffer):
            coll = self.raycaster.collisions[i]
            start = self.repeat * i
            chh = self.distance_to_height(d, scaler=10) // 2
            cosine = self.lamberts_cosine(coll, light)
            column = self.get_wall_col(coll, self.repeat, chh*2, cosine)
            self.pgsurface.blit(column, (start, hh - chh))

    def render(self, light: PointLight):
        self.render_walls(light)
        self.render_sprites()
