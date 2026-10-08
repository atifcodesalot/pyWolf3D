

from . import pygame
from .assets import STATUSBAR, FACE_TEXTURES


class Wolf2DRenderer:
    def __init__(self, resolution, game_res):
        self.res = resolution
        self.game_res = game_res
        self.pgsurf = pygame.Surface(self.res)
        self.width, self.height = self.res
        self.game_off = ((self.width - game_res[0]) // 2, self.height // 16)

        self.hudsurf = STATUSBAR
        hudscale = self.game_res[0] / self.hudsurf.get_size()[0]
        print(hudscale)
        self.hudsurf = pygame.transform.scale_by(self.hudsurf, hudscale)
        self.hud_topmarg = 10
        self.hud_horizmarg = self.game_off[0]
        self.hud_off = (self.hud_horizmarg,
                        self.game_off[1] + self.game_res[1] + self.hud_topmarg)
        
        self.bgcolor = "#004141"
        self.pgsurf.fill(self.bgcolor)
    def draw_hud(self):
        self.pgsurf.blit(self.hudsurf, self.hud_off)

    def draw_game_screen(self, game_screen: pygame.Surface):
        rect = game_screen.get_rect()
        rect.move_ip(*self.game_off)
        self.pgsurf.blit(game_screen, self.game_off)
        pygame.draw.rect(self.pgsurf, "#000000", rect, width=3)

    def draw_everything(self, game_screen: pygame.Surface):
        self.draw_hud()
        self.draw_game_screen(game_screen)
