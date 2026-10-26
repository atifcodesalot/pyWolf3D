

from wolfenstein3D.wolf.assets import ASSET_MANAGER
from wolfenstein3D.wolf.wolfenstein import *
from wolfenstein3D.gamemaps import GameMapsLoader
from wolfenstein3D.find_installation import WolfInstallationFinder
import pygame
from dataclasses import dataclass
import cProfile


@dataclass
class WolfMenu:
    label: str
    selections: list[str]
    sel_count: int


FONT = ASSET_MANAGER.font


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
        self.loader = GameMapsLoader()

    def render_loading_screen(self, entity):
        text_surf = FONT.render(f"[LOADING] {entity}...", True, (255, 255, 255))
        self.screen.blit(text_surf, (400 - text_surf.get_width() //
                         2, 400 - text_surf.get_height() // 2))

    def render_control_instructions(self):
        instructions = ["Use W and S to move, A and D to look left and right, and ENTER to shoot. Press Shift to run.",
                        "You can also use the mouse to look around and shoot with the left mouse button.",
                        "Finally, press ESC to chicken out and P to pause the carnage."]
        y_offset = 500

        for instruction in instructions:
            text_surf = FONT.render(instruction, True, (255, 255, 255))
            self.screen.blit(text_surf, (400 - text_surf.get_width() //
                             2, y_offset - text_surf.get_height() // 2))
            y_offset += text_surf.get_height() + 5

    def change_menu(self, menu: WolfMenu):
        self.player_selection = 0
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
        selection_rect = pygame.Rect(
            *vec_sub((5, 5), selsurf_offset), *vec_mul((selw, selh), 1.1))
        pygame.draw.rect(self.screen, (0, 0, 0), selection_rect, width=2)
        for surf in rendered_surfs:
            self.screen.blit(surf, selsurf_offset)
            selsurf_offset[1] += surf.get_height()

    def render_version(self):
        version_surf = FONT.render(
            f"PYWOLF Version: {self.version}", True, True, (255, 255, 255))
        self.screen.blit(version_surf, (10, 10))

    def load_shareware_episode(self) -> WolfEpisode:
        shareware_maps = []
        mapgen = self.loader.get_shareware_maps()
        i = 0
        while True:
            try:
                wolfmap = next(mapgen)
                shareware_maps.append(wolfmap)
            except StopIteration:
                break
            self.render(
                loading=f"shareware map {i} from {self.loader.maps_path}")
            pygame.display.flip()
            time.sleep(0.1)
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

        return WolfEpisode(
            shareware_maps, shareware_jukebox,
            "Episode 1 Escape from Wolfenstein, shareware version")

    def load_wl6_episodes(self):
        if not self.loader.wl6_maps_present():
            self.render(loading="Could not find GAMEMAPS.WL6 or MAPHEAD.WL6 files, trying to find them automatically.")
            pygame.display.flip()
            time.sleep(2)
            try:
                helper = WolfInstallationFinder()
                if not helper.find_installation():
                    return
                else:
                    self.loader.init_map_filenames()
            except:
                return
        wl6_maps = []
        mapgen = self.loader.get_wl6_maps()
        i = 0
        while True:
            try:
                wolfmap = next(mapgen)
                wl6_maps.append(wolfmap)
            except StopIteration:
                self.loading = False
                break
            self.render(loading=f"map {i} from {self.loader.maps_path}")
            pygame.display.flip()
            time.sleep(0.01)
            i += 1

        # placeholder until music assets are completed
        jukebox = {
            0: "level1_5.ogg"
        }

        epnames = [
            "Escape from Wolfenstein",
            "Operation: Eisenfaust",
            "Die, Führer, Die!",
            "A Dark Secret",
            "Trail of the Madman",
            "Confrontation"
        ]

        wl6_episodes = [WolfEpisode(
            wl6_maps[i*10: (i+1)*10], jukebox,
            f"Episode {i+1} {epnames[i]}") for i in range(6)]
        return wl6_episodes

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

    def wait_menu(self):
        choice = None
        while choice is None:
            self.render()
            choice = self.handle_input()
            pygame.display.flip()
        return choice

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.player_selection = max(0, self.player_selection - 1)
                elif event.key == pygame.K_DOWN:
                    self.player_selection = min(
                        self.current_menu.sel_count-1, self.player_selection + 1)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return self.player_selection

    def run(self):
        while True:
            self.loading = True
            episodes = []
            shareware_episode = self.load_shareware_episode()
            episodes.append(shareware_episode)
            wl6_episodes = self.load_wl6_episodes()
            if wl6_episodes:
                episodes.extend(wl6_episodes)
            else:
                self.render("Could not locate original 6 episodes in your maps folder.")
                pygame.display.flip()
                time.sleep(2)
            
            self.loading = False

            episode_selections = [
                ep.name for ep in episodes] + ["CHICKEN OUT",]

            self.change_menu(WolfMenu("Choose an episode to play or chicken out (quit)!",
                                      selections=episode_selections, sel_count=len(episodes) + 1))

            epchoice = self.wait_menu()
            if epchoice == self.current_menu.sel_count-1:
                break

            episode = episodes[epchoice]
            self.change_menu(self.difficulty_menu)
            diffchoice = self.wait_menu()

            game = WolfGame(
                episode, WolfDifficulty(diffchoice),
                self.screen, sound_off=False, framerate=75)

            game.mainloop()


def main():
    # with cProfile.Profile() as pr:
        menu_renderer = WolfMenuRenderer("Alpha")
        menu_renderer.run()

    # pr.dump_stats("wolf.prof")
