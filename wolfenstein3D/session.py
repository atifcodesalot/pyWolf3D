

from wolfenstein3D.wolf.assets import FONT
from wolfenstein3D.wolf.wolfenstein import *
from wolfenstein3D.wolf.gamemaps import get_shareware_maps, SHAREWARE_PATH
import pygame
from dataclasses import dataclass


@dataclass
class WolfMenu:
    label: str
    selections: list[str]
    sel_count: int


class WolfMenuRenderer:
    BG_COLOR = "#890000"

    def __init__(self, version):
        self.version = version
        self.screen = pygame.display.set_mode((800, 600))
        self.scw, self.sch = self.screen.get_size()
        self.player_selection = 0

        self.difficulty_menu = WolfMenu("How tough are you?",
                                        ["Can I play, Daddy?",
                                         "Don't hurt me.",
                                         "Bring 'em on!",
                                         "I am Death incarnate! (And a pygame developer)"],
                                        4)

        self.current_menu = self.difficulty_menu

    def render_loading_screen(self, entity):
        text_surf = FONT.render(f"loading {entity}...", True, (255, 255, 255))
        self.screen.blit(text_surf, (400 - text_surf.get_width() //
                         2, 400 - text_surf.get_height() // 2))

    def render_control_instructions(self):
        instructions = ["Use W and S to move, A and D to look left and right, and ENTER to shoot. Press Shift to run.",
                       "You can also use the mouse to look around and shoot with the left mouse button. "]
        y_offset = 500

        for instruction in instructions:
            text_surf = FONT.render(instruction, True, (255, 255, 255))
            self.screen.blit(text_surf, (400 - text_surf.get_width() //
                             2, y_offset - text_surf.get_height() // 2))
            y_offset += text_surf.get_height() + 5

    def change_menu(self, menu: WolfMenu):
        self.current_menu = menu

    def render_label(self, label: str, labelpos=None):
        if labelpos is None:
            labelpos = (self.scw - FONT.size(label)[0]) // 2, self.sch // 6
        label_surf = FONT.render(label, True, (255, 255, 255))
        self.screen.blit(label_surf, labelpos)

    def render_selections(self, selections: list[str], yoff=0, xoff=0):
        rendered_surfs = [FONT.render(
            sel, True, (255, 255, 255), True if i == self.player_selection else None)
            for i, sel in enumerate(selections)]
        selw = max(rendered_surfs, key=lambda s: s.get_width()).get_width()
        selh = sum(s.get_height() for s in rendered_surfs)
        selsurf_offset = [(self.scw - selw) // 2 + xoff,
                          (self.sch - selh) // 2 + yoff]
        for surf in rendered_surfs:
            self.screen.blit(surf, selsurf_offset)
            selsurf_offset[1] += surf.get_height()

    def render_version(self):
        version_surf = FONT.render(
            f"PYWOLF Version: {self.version}", True, True, (255, 255, 255))
        self.screen.blit(version_surf, (10, 10))

    def load_shareware_episode(self):
        shareware_maps = []
        mapgen = get_shareware_maps()
        i = 0
        while True:
            try:
                wolfmap = next(mapgen)
                shareware_maps.append(wolfmap)
            except StopIteration:
                self.loading = False
                break
            self.screen.fill(self.BG_COLOR)
            self.render(loading=f"shareware map {i} from {SHAREWARE_PATH}")
            pygame.display.flip()
            i += 1

        shareware_jukebox = {
            0: "level1_5.ogg",
            1: "level2_6.ogg",
            2: "level3_7.ogg",
            3: "level4_8.ogg",
            4: "level1_5.ogg",
            5: "level2_6.ogg",
            6: "level3_7.ogg",
            7: "level4_8.ogg",
            8: None,
            9: "secret.ogg"
        }

        return WolfEpisode(shareware_maps, shareware_jukebox)

    def render(self, loading=None):
        self.screen.fill(self.BG_COLOR)
        self.render_version()
        self.render_control_instructions()
        if self.loading:
            return self.render_loading_screen(loading)

        self.render_menu()

    def render_menu(self):
        self.render_label(self.current_menu.label)
        self.render_selections(self.current_menu.selections)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.player_selection = max(0, self.player_selection - 1)
                elif event.key == pygame.K_DOWN:
                    self.player_selection = min(
                        self.current_menu.sel_count-1, self.player_selection + 1)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return self.player_selection

    def run(self):
        self.loading = True
        shareware_episode = self.load_shareware_episode()
        self.loading = False
        choice = None
        while choice is None:
            self.render()
            choice = self.handle_input()
            pygame.display.flip()
        game = WolfGame(
            shareware_episode, WolfDifficulty(choice),
            self.screen, sound_off=False, framerate=75)
        game.mainloop()


def main():
    menu_renderer = WolfMenuRenderer("Alpha")
    menu_renderer.run()
