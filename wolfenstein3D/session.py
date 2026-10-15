

from wolfenstein3D.wolf.assets import FONT
from wolfenstein3D.wolf.wolfenstein import *
from wolfenstein3D.wolf.gamemaps import get_shareware_maps, SHAREWARE_PATH
import pygame


class PygameWolfMenu:
    BG_COLOR = "#890000"

    def __init__(self, version):
        self.version = version
        self.screen = pygame.display.set_mode((800, 600))

    def render_loading_screen(self, entity):
        text_surf = FONT.render(f"loading {entity}...", True, (255, 255, 255))
        self.screen.blit(text_surf, (400 - text_surf.get_width() //
                         2, 400 - text_surf.get_height() // 2))

    def render_press_key(self):
        text_surf = FONT.render(
            "Loading complete, press any key to play...", True, (255, 255, 255))
        self.screen.blit(text_surf, (400 - text_surf.get_width() //
                         2, 500 - text_surf.get_height() // 2))

    def render_version(self):
        version_surf = FONT.render(
            f"PYWOLF Version: {self.version}", True, True, (255, 255, 255))
        self.screen.blit(version_surf, (10, 10))

    def load_shareware_maps(self):
        global SHAREWAREMAPS
        SHAREWAREMAPS = []
        mapgen = get_shareware_maps()
        i = 0
        while True:
            try:
                wolfmap = next(mapgen)
                SHAREWAREMAPS.append(wolfmap)
            except StopIteration:
                self.loading = False
                break
            self.screen.fill(self.BG_COLOR)
            self.render(loading=f"shareware map {i} from {SHAREWARE_PATH}")
            pygame.display.flip()
            i += 1
        for i, map_ in enumerate(SHAREWAREMAPS):
            if i == len(SHAREWAREMAPS)-1:
                break
            map_.nextmap = SHAREWAREMAPS[i+1]

    def render(self, loading=None):
        if self.loading:
            self.render_loading_screen(loading)
        else:
            self.render_press_key()
        self.render_version()

    def run(self):
        pygame.display.flip()
        self.loading = True
        self.load_shareware_maps()
        self.loading = False

        play = False
        while not play:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    play = True
            self.screen.fill(self.BG_COLOR)
            self.render()
            pygame.display.flip()
        game = WolfGame(SHAREWAREMAPS[0], self.screen, framerate=75)
        game.mainloop()


def main():
    menu = PygameWolfMenu("Alpha")
    menu.run()
