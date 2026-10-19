
from wolfenstein3D.raycaster.raycaster import Raycaster
from wolfenstein3D.raycaster.aux_math import vec_mul
from wolfenstein3D.raycaster.renderer import RayRenderer, PointLight
from wolfenstein3D.wolf import pygame
from wolfenstein3D.wolf.player import WolfPlayer
from wolfenstein3D.wolf.assets import SPRITES, WALL_TEXTURES, FONT
from wolfenstein3D.raycaster.sprites import *
import random
import numpy as np


LIGHT_OPTIONS = [PointLight((0, 0))]


class Wolf3DRenderer(RayRenderer):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    def __init__(self, player: WolfPlayer, pgsurface: pygame.Surface):
        self.player = player
        super().__init__(Raycaster(player), pgsurface,
                         topcolor="#5C5602",
                         bottomcolor="#707070",
                         wall_textures=WALL_TEXTURES)
        self.light = LIGHT_OPTIONS[0]
        self.init_weapon_sprites()
        self.font = pygame.font.SysFont("arial", 6)

        # for when items are picked up or other stuff
        self.glow = False

        self.heartbeats = 0
        self.rgb_offset = [0, 0, 0]
        # in heartbeats
        self.glow_duration = 22
        self.glow_cycle = 0

        # for fizzle fade
        self.shuffled_indices = list(range(self.width*self.height))
        random.shuffle(self.shuffled_indices)
        #

    def init_weapon_sprites(self):
        self.sp_per_wpn = 5
        self.wpn_sp = self.player.weapon.value * self.sp_per_wpn
        weapons: dict = SPRITES["weapons"]

        scaled_weapons = [pygame.transform.scale(
            weapons[k].surface, (self.width*0.7, self.height)) for k in weapons]
        bound_rects = [surf.get_bounding_rect(
            min_alpha=1) for surf in scaled_weapons]
        widest = max(bound_rects, key=lambda r: r.w)
        longest = max(bound_rects, key=lambda r: r.h)
        biggest = pygame.Rect(widest.x, longest.y, widest.w, longest.h)
        self.weapons = dict((i, wpnsurf.subsurface(biggest))
                            for i, wpnsurf in enumerate(scaled_weapons))
        self.wpn_off = (self.width - biggest.w) // 2, self.height - biggest.h

    def render_weapon(self):
        wpnsp = self.weapons[self.wpn_sp]
        self.pgsurface.blit(
            wpnsp,
            self.wpn_off)

    def render_sprites(self):
        # also render actors
        actor_sprites = [act.current_sprite(self.raycaster.observer)
                         for act in self.player.map.get_actors()]
        self.sort_sprites(
            actor_sprites + self.player.map.sprites)
        for sprite in self.sorted_sprites:
            sprite.project()
            if not self.sprite_is_visible(sprite):
                sprite.screen_width = None
                continue
            self.draw_sprite(sprite)

    def handle_glow(self):
        self.glow_cycle += 1
        half_cycle: bool = (self.glow_duration // self.glow_cycle) == 1
        pixelref = pygame.surfarray.pixels3d(self.pgsurface)
        offchannels = [pixelref[:, :, i].astype(
            np.uint16) + self.rgb_offset[i] for i in self.glow]
        for i in self.glow:
            pixelref[:, :, i] = np.minimum(offchannels[i], 255)

        addition = -8 if half_cycle else 8
        for i in self.glow:
            # cap between 255 and 0
            self.rgb_offset[i] = max(
                min(self.rgb_offset[i] + addition, 255), 0)

        del pixelref

    def render(self, heartbeats, weapon=True):
        self.pgsurface.fill(self.topcolor, rect=self.toprect)
        self.pgsurface.fill(self.bottomcolor, rect=self.bottrect)
        offset = vec_mul(self.player.look_dir, -1)
        camera_pos = vec_add(self.player.pos, offset)
        super().render(camera_pos, self.light)
        if self.glow:
            self.handle_glow()
        if weapon:
            self.render_weapon()
        # self.render_statusbar()
        self.heartbeats += heartbeats

    def fizzle_fade(self, master, update_dest):
        red = 0
        for i in self.shuffled_indices:
            # grab a cheap pixel reference
            pixelref = pygame.PixelArray(self.pgsurface)
            w, h = pixelref.shape
            #
            pos = (i % w, i // w)
            pixelref[pos] = 0xFF0000
            red += 1
            if not red % 60:
                # update display per 15 writes
                del pixelref
                master.blit(self.pgsurface, update_dest)
                pygame.display.flip()

    def unfizzle(self, master, update_dest):
        self.render(1)
        mirror = self.pgsurface.copy()
        self.pgsurface.fill("0xff0000")
        pixelref = pygame.PixelArray(self.pgsurface)
        unfizzled = 0
        for i in self.shuffled_indices[::-1]:
            pixelref = pygame.PixelArray(self.pgsurface)
            w, h = pixelref.shape
            pos = (i % w, i // w)
            pixelref[pos] = mirror.get_at(pos)
            unfizzled += 1
            if not unfizzled % 80:
                # update display per 15 writes
                del pixelref
                master.blit(self.pgsurface, update_dest)
                pygame.display.flip()
                pass

    def glow_end(self):
        self.rgb_offset = [0, 0, 0]
        self.glow = False
        self.glow_cycle = 0
        
    def begin_glow(self, data, duration):
        self.glow = data
        self.glow_duration = duration

    def clear_screen(self):
        self.pgsurface.fill(self.WHITE)
        self.pgsurface.fill(self.BLACK)
