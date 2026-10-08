
from raycaster.raycaster import Raycaster
from raycaster.aux_math import vec_mul
from raycaster.renderer import RayRenderer, PointLight
from . import pygame
from .player import WolfPlayer
from .assets import SPRITES, WALL_TEXTURES, FONT
from raycaster.sprites import *
import random
import numpy as np



LIGHT_OPTIONS = [PointLight((0, 0))]


class Wolf3DRenderer(RayRenderer):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    def __init__(self, player: WolfPlayer, pgsurface: pygame.Surface):
        self.player = player
        self.map = self.player.map
        raycaster = Raycaster(player, player.map)
        super().__init__(raycaster, pgsurface,
                         topcolor="#6B6404",
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
        self.glow_duration = 16
        self.glow_cycle = 0

        # for fizzle fade
        self.shuffled_indices = list(range(self.width*self.height))
        random.shuffle(self.shuffled_indices)
        #

    def init_weapon_sprites(self):
        self.sp_per_weap = 5
        self.weap_sp = self.player.weapon.value * self.sp_per_weap
        weapons: dict = SPRITES["weapons"]
        self.weapons = {}
        for i in weapons:
            wepspr: Sprite = weapons[i]
            # transform each weapon sprite to match the screen size
            scres = self.pgsurface.get_size()
            wepres = (int(scres[0]*0.8), scres[1])
            self.weapons[i] = Sprite(wepspr.image.resize(wepres,
                                                         resample=Image.Resampling.NEAREST))
            self.wpn_xoffset = (scres[0] - wepres[0]) // 2
            self.wpn_yoffset = scres[1]//3
            surf = self.weapons[i].surface
            self.weapons[i].surface = surf.subsurface(
                (0, surf.get_height()//3,
                 surf.get_width(), 2*surf.get_height()//3))

    def render_weapon(self):
        self.pgsurface.blit(
            self.weapons[self.weap_sp].surface,
            (self.wpn_xoffset, self.wpn_yoffset))

    def render_statusbar(self):
        sfont = FONT.render(
            f"Score: {self.player.score} Health: {self.player.health}  Ammo: {self.player.ammo}", True, self.WHITE)
        self.pgsurface.blit(sfont, (150, 10))

    def render_sprites(self):
        # also render actors
        actor_sprites = [act.current_sprite(
            self.player) for act in self.map.actors]
        all_sprites = self.sort_sprites(actor_sprites + self.map.sprites)
        for sprite in all_sprites:
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
            self.rgb_offset[i] += addition

        del pixelref

    def render(self, heartbeats, weapon=True):
        self.pgsurface.fill(self.topcolor, rect=self.toprect)
        self.pgsurface.fill(self.bottomcolor, rect=self.bottrect)
        offset = vec_mul(self.player.look_dir, -0.6)
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
            try:
                pixelref[pos] = 0xFF0000
            except:
                exit()
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

    def clear_screen(self):
        self.pgsurface.fill(self.WHITE)
        self.pgsurface.fill(self.BLACK)