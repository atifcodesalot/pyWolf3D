
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
                 topcolor, bottomcolor, wall_textures, scaler=10):
        self.raycaster = raycaster
        self.pgsurface = pgsurface
        self.width, self.height = pgsurface.get_size()
        rayc = self.raycaster.observer.ray_count
        self.column_width = self.width // rayc
        self.wall_width = raycaster.observer.map.wall_width
        self.repeat = self.width // rayc
        self.topcolor = topcolor
        self.bottomcolor = bottomcolor
        self.bottrect = pygame.Rect(
            0, self.height//2, self.width, self.height//2)
        self.toprect = pygame.Rect(0, 0, self.width, self.height//2)

        self.sprite_wh_ratio = 1 / self.repeat
        self.wall_textures = wall_textures
        self.wall_scaler = scaler
        self.sprite_scaler = self.wall_scaler
        self.distbuff = []

    def distance_to_height(self, dist, sprite=False):
        scaler = self.sprite_scaler if sprite else self.wall_scaler
        dist = dist if dist != 0 else 0.0001
        return (self.height / dist) * scaler

    def lamberts_cosine(self, coll, light: PointLight):
        _, pos, vertical, _, _ = coll
        n = BASIS[~vertical + 2]
        light_to_coll = vec_sub(pos, light.pos)
        light_to_coll = vec_norm(light_to_coll)
        return abs(vec_dot(n, light_to_coll))

    def get_wall_col(self, coll, height):
        vertical = coll[2]
        m = self.raycaster.observer.map
        offset = coll[1][vertical] % self.wall_width
        # if it is a door, take the opening into account
        if coll[3] in m.DOOR_INDICES:
            door = m.get_door(m.to_block_pos(*coll[1]))
            if door:
                offset = m.wall_width * door.opening - offset
            tex_src = self.wall_textures[coll[3]]
        else:
            tex_src = self.wall_textures[coll[3] + vertical]

        # map to 0 to len(columns)
        ci = offset / self.wall_width * (tex_src.width - 1)
        return tex_src.get_column(round(ci),
                              self.repeat, int(height), self.height)

    def sprite_is_visible(self, projected, sprite) -> bool:
        o = self.raycaster.observer
        to_sprite = vec_sub(o.pos, sprite.pos)
        if vec_mag(to_sprite) > self.maxd:
            # too far away to be visible
            return False
        shw = sprite.width // 2
        vpl = o.vp_length
        on_vp = vpl + shw > projected[0] > -vpl - shw
        in_front = vec_dot(o.look_dir, vec_sub(o.pos, sprite.pos)) > 0
        return on_vp and in_front

    def spcol_visible(self, dist, col_pos):
        w_1 = self.width - 1
        if col_pos > w_1 or col_pos < 0:
            return False

        return self.distbuff[int(col_pos // self.repeat)] > dist

    def draw_sprite(self, sprite: Sprite):
        o = self.raycaster.observer
        perp_dist = vec_dot(vec_sub(o.pos, sprite.pos), o.look_dir)
        if perp_dist < 6:
            return
        projected = sprite.project()
        if not self.sprite_is_visible(projected, sprite):
            return
        h = self.height
        hh = h // 2
        screen_pos = sprite.screen_pos(self, projected)

        height_to_draw = self.distance_to_height(perp_dist, sprite=True)
        if height_to_draw > 1000:
            return
        width_to_draw = height_to_draw * self.sprite_wh_ratio

        skip = sprite.width / width_to_draw
        visible_height = min(self.height, height_to_draw)

        r = self.repeat

        ystart = hh - visible_height // 2
        xstart = screen_pos - (width_to_draw // 2) * r

        for i in range(int(width_to_draw)):
            col_pos = xstart + (i * r)
            if not self.spcol_visible(perp_dist, col_pos):
                continue
            column = sprite.get_column(
                int(i*skip), r, height_to_draw, h)
            self.pgsurface.blit(
                column, (col_pos, ystart))

    def sort_sprites(self, sprites: list[Sprite]):
        sorted_sprites = sorted(
            sprites,
            key=lambda s: s.to_observer_space(self.raycaster.observer),
            reverse=True)
        return sorted_sprites

    def render_sprites(self):
        m = self.raycaster.observer.map
        sorted_sprites = self.sort_sprites(m.sprites)
        for sprite in sorted_sprites:
            self.draw_sprite(sprite)

    def render_walls(self, camera_pos, light):
        self.distbuff = []
        hh = self.height // 2
        dirs = self.raycaster.observer.directions
        cast = 0
        for ray in dirs:
            coll = self.raycaster.raycast(ray, camera_pos)
            self.distbuff.append(coll[0])
            start = self.repeat * cast
            chh = self.distance_to_height(coll[0]) // 2
            column = self.get_wall_col(coll, chh*2)
            chh = min(chh, hh)
            self.pgsurface.blit(column, (start, hh - chh))
            cast += 1

    def render(self, camera_pos, light: PointLight):
        self.render_walls(camera_pos, light)
        self.maxd = max(self.distbuff)
        self.render_sprites()
