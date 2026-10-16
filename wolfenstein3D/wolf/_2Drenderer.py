

from wolfenstein3D.wolf import pygame
from wolfenstein3D.wolf.assets import (
    STATUSBAR, HUD_FACES, HUD_NUMBERS, HUD_WEAPONS, HUD_KEYS)


class Wolf2DRenderer:
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    def __init__(self, resolution, game_res):
        self.res = resolution
        self.game_res = game_res
        self.pgsurf = pygame.Surface(self.res)
        self.width, self.height = self.res
        self.game_off = ((self.width - game_res[0]) // 2, self.height // 16)
        self.game_rect = pygame.Rect(self.game_off, game_res)

        self.init_hud()

        self.bgcolor = "#004141"
        self.pgsurf.fill(self.bgcolor)

        self.heartbeats = 0

    def init_hud(self):
        self.hudscale = self.game_res[0] / STATUSBAR.get_size()[0]
        def scale(surf): return pygame.transform.scale_by(surf, self.hudscale)
        self.hud = scale(STATUSBAR)
        self.hudsurf = pygame.Surface(self.hud.get_size())
        self.hud_size = self.hudsurf.get_size()
        self.hud_topmarg = 10
        self.hud_horizmarg = self.game_off[0]
        self.hud_off = (self.hud_horizmarg,
                        self.game_off[1] + self.game_res[1] + self.hud_topmarg)
        self.hud_rect = pygame.Rect(self.hud_off, self.hud_size)
        self.hud_faces = [scale(face) for face in HUD_FACES]
        self.hud_nums = [scale(num) for num in HUD_NUMBERS]
        self.hud_weapons = [scale(weap) for weap in HUD_WEAPONS]
        self.hud_keys = [scale(key) for key in HUD_KEYS]

        swap = self.hud_weapons[1].copy()
        self.hud_weapons[1] = self.hud_weapons[2]
        self.hud_weapons[2] = swap

        self.hud_floor_off = (16 * self.hudscale, 16 * self.hudscale)
        self.hud_score_off = (48 * self.hudscale, 16 * self.hudscale)
        self.hud_faces_off = (136 * self.hudscale, 4 * self.hudscale)
        self.hud_health_off = (168 * self.hudscale, 16 * self.hudscale)
        self.hud_weapon_off = (256 * self.hudscale, 8 * self.hudscale)
        self.hud_ammo_off = (216 * self.hudscale, 16 * self.hudscale)
        self.hud_lives_off = (112 * self.hudscale, 16 * self.hudscale)
        self.hud_skey_off = (240 * self.hudscale, 20 * self.hudscale)
        self.hud_gkey_off = (240 * self.hudscale, 4 * self.hudscale)

        self.face_off = 0
        self.look_around = False

    def get_face(self, player) -> pygame.Surface:
        if player.excited_to_kill_nazis:
            return self.hud_faces[-3]

        if player.health == 0:
            return self.hud_faces[22]
        face_idx = ((100 - player.health) // 15) * 3
        return self.hud_faces[face_idx + (self.face_off) % 3]

    def draw_number(self, decimal, offset, max_digits):
        off = list(offset)
        if decimal == 0:
            digitsurf = self.hud_nums[0]
            off[0] += 16*self.hudscale
            self.hudsurf.blit(digitsurf, off)
            return
        prev = False
        for i in range(max_digits-1, -1, -1):
            digit = (decimal // pow(10, i)) % 10
            digit_nz = digit != 0
            if digit_nz or prev:
                digitsurf = self.hud_nums[digit]
                self.hudsurf.blit(digitsurf, off)
                prev = True
            else:
                prev = False
            off[0] += 8*self.hudscale

    def update_hud(self, player_ctx):
        self.hudsurf.blit(self.hud, (0, 0))
        face = self.get_face(player_ctx)
        self.hudsurf.blit(face, self.hud_faces_off)
        weap = self.hud_weapons[player_ctx.weapon.value]
        self.hudsurf.blit(weap, self.hud_weapon_off)
        self.draw_number(player_ctx.score, self.hud_score_off, 5)
        self.draw_number(player_ctx.health, self.hud_health_off, 3)
        self.draw_number(player_ctx.ammo, self.hud_ammo_off, 2)
        self.draw_number(player_ctx.lives, self.hud_lives_off, 1)
        if player_ctx.has_silver_key:
            self.hudsurf.blit(self.hud_keys[2], self.hud_skey_off)
        if player_ctx.has_gold_key:
            self.hudsurf.blit(self.hud_keys[1], self.hud_gkey_off)
        self.pgsurf.blit(self.hudsurf, self.hud_off)

    def draw_game_screen(self, game_screen: pygame.Surface):
        self.pgsurf.blit(game_screen, self.game_rect)
        pygame.draw.rect(self.pgsurf, "#000000", self.game_rect, width=5)

    def draw_everything(self, game_screen: pygame.Surface, player_ctx):
        self.clear_game_screen()
        # update the hud per 5 heartbeats
        if not self.heartbeats % 5:
            self.update_hud(player_ctx)
        self.draw_game_screen(game_screen)
        # draw what else??

    def handle_look_around(self):
        if not self.heartbeats % 300:
            self.look_around = True
        elif self.look_around:
            if self.face_off == 3:
                self.look_around = False
                self.face_off = 0
            elif not self.heartbeats % 15:
                self.face_off += 1

    def heartbeat(self, game_screen, player_ctx, heartbeats=1):
        self.handle_look_around()
        self.draw_everything(game_screen, player_ctx)
        self.heartbeats += heartbeats

    def clear_game_screen(self):
        self.pgsurf.fill(self.WHITE, rect=self.game_rect)
