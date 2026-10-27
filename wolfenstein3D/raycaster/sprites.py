

from wolfenstein3D.raycaster.textures import Texture, Image
from wolfenstein3D.raycaster.aux_math import *
from math import atan2, pi


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
    def __init__(self, direction, speed, pos, sprites: list[Sprite],
                 no_orientation=True, sprite_per_ori=None, explosion_sprites=None,
                 explosion_snd=None):
        self.dir = direction
        self.left = [-self.dir[1], self.dir[0]]
        self.speed = speed
        self.pos = pos
        self.no_orientation = no_orientation
        self.sprite_amount = len(sprites)
        self.sprites = [sp.copy(pos) for sp in sprites]
        if not self.no_orientation:
            rows = [
                self.sprites[i*sprite_per_ori: (i + 1) * sprite_per_ori]
                for i in range(self.sprite_amount // sprite_per_ori)]
            self.sprites = []
            for row in rows:
                self.sprites.extend(row)
        self.spidx = 0
        self.spoff = 0
        self.travel_counter = 0
        self.sprite_per_ori = len(
            sprites) if no_orientation else sprite_per_ori

        self.exploding = False
        self.explosion_sprites = explosion_sprites
        if explosion_sprites:
            self.explosion_amount = len(explosion_sprites)
            self.explosion_counter = 0
        self.explosion_snd = explosion_snd

    def update_direction(self, newdir):
        self.dir = newdir
        self.left = [-self.dir[1], self.dir[0]]

    def current_sprite(self) -> Sprite:
        exploding_anim = self.exploding and self.explosion_sprites is not None
        csp = self.sprites[self.spidx] if not exploding_anim \
            else self.explosion_sprites[(self.spidx) % self.explosion_amount]
        csp.pos = self.pos
        return csp

    def travel(self, game_ctx):
        self.travel_counter = (self.travel_counter + 1) % 100
        self.pos = vec_add(self.pos, vec_mul(self.dir, self.speed))
        ori_idx = 0 if self.no_orientation else self.orientation_idx(
            game_ctx.player)
        if not self.travel_counter % 10:
            self.spoff = (self.spoff + 1) % self.sprite_per_ori
        self.spidx = self.sprite_per_ori * ori_idx + self.spoff

    def collides_map(self, map_ctx):
        pjblock = map_ctx.to_block_pos(*self.pos)
        collides = map_ctx.cell_occupied(pjblock)
        return collides

    def collides_player(self, game_ctx):
        dist = euclidean_distance(self.pos, game_ctx.player.pos)
        return dist < 8

    def collides(self, game_ctx):
        return self.collides_map(game_ctx.wolfmap) \
            or self.collides_player(game_ctx)

    def to_this_space(self, pos):
        to_self = vec_sub(pos, self.pos)
        myspace = (vec_dot(to_self, self.left),
                   vec_dot(to_self, self.dir))
        return myspace

    def orientation_idx(self, observer, sectors=8):
        myspace = self.to_this_space(observer.pos)
        sx, sy = myspace
        return int((pi/2-atan2(-sy, sx)) // (2*pi / sectors) % sectors)

    # returns True if explosion is done
    def explode(self) -> bool:
        if not self.explosion_sprites:
            return True
        self.spidx = int(self.explosion_counter)
        self.explosion_counter += 0.2
        if int(self.explosion_counter) == self.explosion_amount:
            return True
