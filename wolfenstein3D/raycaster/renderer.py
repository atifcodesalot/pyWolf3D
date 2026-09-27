
from .raycaster import Raycaster
from .aux_math import *
import pygame
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
    def __init__(self, raycaster: Raycaster,
                 pgsurface: pygame.Surface,
                 topcolor, bottomcolor, wall_textures, scaler=8):
        self.raycaster = raycaster
        self.pgsurface = pgsurface
        self.width, self.height = pgsurface.get_size()
        self.column_width = self.width // self.raycaster.observer.ray_count
        self.wall_width = raycaster.map.wall_width
        self.repeat = self.width // self.raycaster.observer.ray_count
        self.topcolor = topcolor
        self.bottomcolor = bottomcolor
        self.bottrect = pygame.Rect(
            0, self.height//2, self.width, self.height//2)
        self.toprect = pygame.Rect(0, 0, self.width, self.height//2)

        self.sprite_wh_ratio = 1 / self.repeat
        self.wall_textures = wall_textures
        self.wall_scaler = scaler
        self.sprite_scaler = self.wall_scaler
        self.colls = []
        self.db = []

    def distance_to_height(self, d, sprite=False):
        scaler = self.sprite_scaler if sprite else self.wall_scaler
        d = d if d != 0 else 0.0001
        return (self.height / d) * scaler

    def cast(self):
        self.colls, self.db = self.raycaster.raycast()

    def lamberts_cosine(self, coll, light: PointLight):
        pos, vertical, _ = coll
        n = BASIS[~vertical + 2]
        light_to_coll = plain_sub(pos, light.pos)
        light_to_coll = plain_normalize(light_to_coll)
        return abs(plain_dot(n, light_to_coll))

    def get_wall_col(self, coll, repeat, height, factor):
        vertical = coll[1]
        m = self.raycaster.map
        offset = coll[0][vertical] % self.wall_width
        # if it is a door, take the opening into account
        if coll[2] in m.DOOR:
            door = m.get_door(m.to_block_pos(*coll[0]))
            if door:
                offset = m.wall_width * door.opening - offset

        texture = self.wall_textures[coll[2] - 1]
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
        o = self.raycaster.observer
        perp_dist = plain_dot(plain_sub(o.pos, sprite.pos), o.look_dir)
        if perp_dist < 1:
            return
        projected = sprite.project()
        if not self.sprite_is_visible(projected, sprite):
            return
        h = self.height
        hh = h // 2
        screen_pos = sprite.screen_pos(self, projected)

        height_to_draw = self.distance_to_height(perp_dist, sprite=True)
        width_to_draw = height_to_draw * self.sprite_wh_ratio

        skip = sprite.width / width_to_draw
        visible_height = min(self.height, height_to_draw)

        r = self.repeat
        ystart = hh - visible_height // 2
        xstart = screen_pos - (width_to_draw // 2) * r
        w_1 = self.width - 1

        for i in range(int(width_to_draw)):
            col_pos = xstart + (i * r)
            # if the column isn't in screen width
            if col_pos > w_1 or col_pos < 0:
                continue
            # if there is a wall that is closer
            if self.db[int(col_pos // r)] < perp_dist:
                continue
            column = sprite.get_column(
                int(i*skip), r, height_to_draw, 1, h)
            self.pgsurface.blit(
                column, (col_pos, ystart))

    def sort_sprites(self, sprites: list[Sprite]):
        sorted_sprites = sorted(
            sprites,
            key=lambda s: s.to_observer_space(self.raycaster.observer),
            reverse=True)
        return sorted_sprites

    def render_sprites(self):
        sorted_sprites = self.sort_sprites(self.raycaster.map.sprites)
        for sprite in sorted_sprites:
            self.draw_sprite(sprite)

    def render_walls(self, light):
        hh = self.height // 2
        for i, d in enumerate(self.db):
            coll = self.colls[i]
            start = self.repeat * i
            chh = self.distance_to_height(d) // 2
            cosine = self.lamberts_cosine(coll, light)
            column = self.get_wall_col(coll, self.repeat, chh*2, cosine)
            chh = min(chh, hh)
            self.pgsurface.blit(column, (start, hh - chh))

    def render(self, light: PointLight):
        self.cast()
        self.render_walls(light)
        self.render_sprites()
