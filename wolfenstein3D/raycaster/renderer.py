
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
        self.wall_width = raycaster.map.wall_width
        self.repeat = self.width // self.raycaster.observer.ray_count
        self.sprites = []

    def add_sprite(self, sprite_src: Sprite, pos):
        if type(sprite_src) is not Sprite:
            raise TypeError("Expected Sprite object")
        copy = sprite_src.copy(pos=pos)
        self.sprites.append(copy)

    def distance_to_height(self, d, scaler):
        return (self.height / d) * scaler

    def cast(self):
        self.colls, self.db = self.raycaster.raycast()

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
                                  int(repeat), int(height), factor, self.height)

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
        projected = sprite.project(o)
        if not self.sprite_is_visible(projected, sprite):
            return
        screen_pos = sprite.screen_pos(self, projected)
        perp_dist = plain_dot(plain_sub(o.pos, sprite.pos), o.look_dir)
        height_to_draw = self.distance_to_height(perp_dist, scaler=10)
        width_to_draw = height_to_draw // 3
        sw = sprite.width
        start = screen_pos - (width_to_draw // 2) * self.repeat
        skip = sw / width_to_draw
        visible_height = min(self.height, height_to_draw)
        for i in range(int(width_to_draw)):
            col_pos = start + (i * self.repeat)
            # if the column isn't in screen width
            if col_pos > self.width - 1 or col_pos < 0:
                continue
            # if there is a wall that is closer
            if self.db[int(col_pos // self.repeat)] < perp_dist:
                continue
            column = sprite.get_column(
                int(i*skip), self.repeat, height_to_draw, 1, self.height)
            self.pgsurface.blit(
                column, (col_pos, hh - visible_height//2))

    def sort_sprites(self):
        def get_y(s): return s.to_observer_space(self.raycaster.observer)[1]
        self.sprites = sorted(self.sprites, key=get_y)

    def render_sprites(self):
        self.sort_sprites()
        for sprite in self.sprites:
            self.draw_sprite(sprite)

    def render_walls(self, light):
        hh = self.height // 2
        for i, d in enumerate(self.db):
            coll = self.colls[i]
            start = self.repeat * i
            chh = self.distance_to_height(d, scaler=10) // 2
            cosine = self.lamberts_cosine(coll, light)
            column = self.get_wall_col(coll, self.repeat, chh*2, cosine)
            chh = min(chh, hh)
            self.pgsurface.blit(column, (start, hh - chh))

    def render(self, light: PointLight):
        self.render_walls(light)
        self.render_sprites()


class GUIRenderer:
    def __init__(self):
        pass
