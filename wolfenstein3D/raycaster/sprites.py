

from wolfenstein3D.raycaster.textures import Texture, Image
from wolfenstein3D.raycaster.aux_math import *


class Sprite(Texture):
    def __init__(self, image: Image.Image, pos=None,
                 blocking=None, surf=None, converted=False, columns=None):
        super().__init__(image, surf=surf, converted=converted, columns=columns)
        self.pos = pos
        self.blocking = blocking
        self.screen_pos = None
        self.projected = None
        self.screen_width = None

    def to_observer_space(self, observer):
        self.obs_space = observer.to_this_space(self.pos)
        return self.obs_space[1]

    def project(self):
        # guard against 0
        w = 1e-10 if self.obs_space[1] == 0 else self.obs_space[1]
        self.projected = (self.obs_space[0] / w, 1)

    # takes RayRenderer object
    def to_screen_pos(self, renderer):
        o = renderer.raycaster.observer
        vpl = o.vp_length
        # transform to screen position
        self.screen_pos = (
            (self.projected[0] + vpl) / (2*vpl)) * renderer.width

    def get_perp_dist(self, observer):
        to_self = vec_sub(observer.pos, self.pos)
        self.perp_dist = vec_dot(to_self, observer.look_dir)

    def translate(self, tvec):
        self.pos = vec_add(self.pos, tvec)

    def get_column(self, i, repeat, height, screen_height):
        scaled = self.scale_column(
            self.columns[i], repeat, height, screen_height)
        return scaled

    def copy(self, pos):
        copied = object.__new__(self.__class__)
        copied.__init__(self.image, pos=pos,
                        blocking=self.blocking,
                        surf=self.surface,
                        converted=True,
                        columns=self.columns
                        )
        return copied


class Projectile:
    def __init__(self, direction, speed, pos, sprites: list[Sprite]):
        self.direction = direction
        self.speed = speed
        self.pos = pos
        self.sprites = [sp.copy(pos) for sp in sprites]
        self.sprite_amount = len(self.sprites)
        self.spidx = 0
        self.travel_counter = 0

    def current_sprite(self) -> Sprite:
        csp = self.sprites[self.spidx]
        csp.pos = self.pos
        return csp

    def travel(self):
        self.travel_counter = (self.travel_counter + 1) % 100
        self.pos = vec_add(self.pos, vec_mul(self.direction, self.speed))
        if not self.travel_counter % 25:
            self.spidx = (self.spidx + 1) % self.sprite_amount

    def stop(self):
        self.speed = 0

    def collides_map(self, map_ctx):
        pjblock = map_ctx.to_block_pos(*self.pos)
        return map_ctx.cell_occupied(pjblock)
    
    def collides_player(self, game_ctx):
        pblock = game_ctx.player.get_current_block()
        return game_ctx.wolfmap.to_block_pos(*self.pos) == pblock
            
