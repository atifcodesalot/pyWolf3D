

from wolfenstein3D.wolf.assets import ASSET_MANAGER
from wolfenstein3D.wolf.wolfenstein import *
from wolfenstein3D.gamemaps import GameMapsLoader
from wolfenstein3D.find_installation import WolfInstallationFinder
import pygame
from dataclasses import dataclass
import cProfile
import pygame_gui


@dataclass
class WolfMenu:
    label: str
    selections: list[str]
    callbacks: list
    sel_count: int
    font: pygame.font.Font
    labelsep: int = 25


class WolfMenuNode:
    def __init__(self, menu: WolfMenu, parent, children):
        self.menu = menu
        self.parent = parent
        self.children = children

    def add_back_selection(self):
        exitstr = "Exit" if self.is_root() else "Back"
        if exitstr in self.menu.selections:
            return
        self.menu.selections.append(exitstr)

        def goback(sesctl, _):
            if self.is_root():
                exit("Chicken!")
            else:
                sesctl.menu_handler.transition_node(self.parent)

        self.menu.callbacks.append(goback)

        self.menu.sel_count += 1

    def is_root(self):
        return self.parent is None

    def is_leaf(self):
        return not any(self.children)


@dataclass
class WolfMenuTree:
    root: WolfMenuNode


FONT = ASSET_MANAGER.font


class WolfMenuHandler:
    def __init__(self, session_control, tree: WolfMenuTree, font=FONT):
        self.sesctl = session_control
        self.tree = tree
        self.display = self.sesctl.screen
        self.scw, self.sch = self.display.get_size()
        self.font = font

        self.current = tree.root
        self.playersel = 0

    def render_selections(self, selections: list[str], labely, xoff=0):
        rendered_surfs = [self.font.render(
            sel, True, (255, 255, 255), True if i == self.playersel else None)
            for i, sel in enumerate(selections)]
        selw = max(rendered_surfs, key=lambda s: s.get_width()).get_width()
        selh = sum(s.get_height() for s in rendered_surfs)
        selsurf_offset = [(self.scw - selw) // 2 + xoff,
                          labely + self.current.menu.labelsep]
        sely = selsurf_offset[1]
        selection_rect = pygame.Rect(
            *vec_sub((5, 5), selsurf_offset), *vec_mul((selw, selh), 1.1))
        pygame.draw.rect(self.display, (0, 0, 0), selection_rect, width=2)
        for surf in rendered_surfs:
            self.display.blit(surf, selsurf_offset)
            selsurf_offset[1] += surf.get_height()
        return sely

    def render_label(self, label: str):
        ly = self.sch // 4
        labelpos = (self.scw - self.font.size(label)
                    [0]) // 2, ly
        label_surf = self.font.render(label, True, (200, 200, 200))
        self.display.blit(label_surf, labelpos)
        return ly + self.font.size(label)[1]

    def render_menu(self):
        self.display.fill(self.sesctl.BG_COLOR)
        self.font = self.current.menu.font
        ly = self.render_label(self.current.menu.label)
        self.render_selections(self.current.menu.selections,
                               labely=ly)

        self.sesctl.render(clear=False)

    def transition_node(self, node):
        self.playersel = 0
        self.current = node

    def handle_input(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.playersel = max(0, self.playersel - 1)
                elif event.key == pygame.K_DOWN:
                    self.playersel = min(
                        self.current.menu.sel_count-1, self.playersel + 1)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return self.playersel

    def wait_menu(self):
        clock = pygame.time.Clock()
        choice = None
        while choice is None:
            events = pygame.event.get()
            dt = clock.tick(30)
            self.render_menu()
            choice = self.handle_input(events)
            if self.current.menu.label.lower() == "options":
                self.sesctl.handle_options(events, dt)

            pygame.display.flip()
        callback = self.current.menu.callbacks[choice]
        if not callable(callback):
            self.transition_node(self.current.children[choice])
        else:
            ready_to_play = False
            if self.current.is_leaf() and \
                    self.playersel != self.current.menu.sel_count-1:
                # game ready to build!
                ready_to_play = True
            callback(self.sesctl, self.playersel)

            return ready_to_play

    def start(self):
        while True:
            if self.wait_menu():
                break


class WolfSessionController:
    BG_COLOR = "#890000"

    def __init__(self, version):
        self.version = version
        self.screen = pygame.display.set_mode((800, 600))

        self.main_menu = WolfMenu("pyWolf3D",
                                  ["Play",
                                   "Options"],
                                  [None, None],
                                  2,
                                  ASSET_MANAGER.biggerfont,
                                  labelsep=75)

        self.difficulty_menu = WolfMenu("How tough are you?",
                                        ["Can I play, Daddy?",
                                         "Don't hurt me.",
                                         "Bring 'em on!",
                                         "I am Death incarnate! (And a pygame developer)"],
                                        [lambda sesctl,
                                            sel: sesctl.set_difficulty(sel)] * 4,
                                        4,
                                        FONT)

        self.widget_off = (350, 180)
        self.widget_hsep = 50
        self.ui_manager = pygame_gui.UIManager(self.screen.get_size())
        self.options_widgets = [
            pygame_gui.elements.UICheckBox(
                pygame.Rect(self.widget_off, (30, 30)), "Sound", self.ui_manager, initial_state=True),
            pygame_gui.elements.UILabel(pygame.Rect(
                vec_add(self.widget_off, (0, self.widget_hsep)), (140, 20)), "Raycaster ray count", self.ui_manager),
            pygame_gui.elements.UIDropDownMenu(["160", "128", "80", "64", "32", "16", "10", "8", "4", "2"], "160",
                                               pygame.Rect(
                vec_add(self.widget_off, (0, self.widget_hsep*1.5)), (100, 25)), self.ui_manager
            ),

            pygame_gui.elements.UILabel(pygame.Rect(
                vec_add(self.widget_off, (0, self.widget_hsep*2.5)), (140, 20)), "Field of view", self.ui_manager),
            pygame_gui.elements.UIDropDownMenu(["54", "60", "90", "120"], "54",
                                               pygame.Rect(
                vec_add(self.widget_off, (0, self.widget_hsep*3)), (100, 25)), self.ui_manager
            )
        ]
        self.raycount = 160
        self.soundoff = False
        self.fov = 54

        self.loader = GameMapsLoader()

    def handle_options(self, events, dt):
        self.ui_manager.draw_ui(self.screen)
        self.ui_manager.update(dt)
        for event in events:
            if event.type in (
                pygame.KEYDOWN,
                pygame.KEYUP,
                pygame.TEXTINPUT,
                pygame.TEXTEDITING,
            ):
                continue
            self.ui_manager.process_events(event)
            if event.type == pygame_gui.UI_CHECK_BOX_CHECKED:
                self.soundoff = False
            elif event.type == pygame_gui.UI_CHECK_BOX_UNCHECKED:
                self.soundoff = True
            elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                if event.ui_element == self.options_widgets[4]:
                    self.fov = int(event.ui_element.selected_option[1])
                elif event.ui_element == self.options_widgets[2]:
                    self.raycount = int(event.ui_element.selected_option[1])

    def build_episode_node(self):
        def epsel_callback(sesctl, sel):
            sesctl.set_episode(sel)
            sesctl.menu_handler.transition_node(self.node_diff)

        self.episode_menu = WolfMenu("Which Episode to play?",
                                     selections=[
                                         ep.name for ep in self.episodes],
                                     callbacks=[epsel_callback] *
                                     len(self.episodes),
                                     sel_count=len(self.episodes),
                                     font=FONT)
        self.node_ep = WolfMenuNode(
            self.episode_menu, None, [self.node_diff] * 4)

    def build_options_subtree(self):
        self.options_menu = WolfMenu("Options", [], [], 0, FONT, labelsep=200)
        self.node_opts = WolfMenuNode(self.options_menu, None, [])

    def build_menu_tree(self) -> WolfMenuTree:
        self.node_diff = WolfMenuNode(self.difficulty_menu, None, [None,]*4)
        self.build_episode_node()
        self.build_options_subtree()
        self.node_diff.parent = self.node_ep
        self.root = WolfMenuNode(self.main_menu, None, [
                                 self.node_ep, self.node_opts])
        self.node_ep.parent = self.root
        self.node_opts.parent = self.root

        self.root.add_back_selection()
        self.node_ep.add_back_selection()
        self.node_diff.add_back_selection()
        self.node_opts.add_back_selection()
        self.menu_handler = WolfMenuHandler(self, WolfMenuTree(self.root))

    def set_difficulty(self, diffsel):
        self.difficulty = WolfDifficulty(diffsel)

    def set_episode(self, episode_idx):
        if getattr(self, "episodes", None) is None:
            return
        self.episode = self.episodes[episode_idx]

    def render_loading_screen(self, entity):
        text_surf = FONT.render(
            f"[LOADING] {entity}...", True, (128, 128, 128))
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
            time.sleep(0.02)
            i += 1

        if not self.loaded_music:
            self.render(loading="now synthesizing shareware music")
            pygame.display.flip()
            self.loader.dump_shareware_music()
            ASSET_MANAGER.init_sounds(root=ASSET_MANAGER.sound_path, depth=1)

        return WolfEpisode(
            shareware_maps,
            "Episode 1 Escape from Wolfenstein, shareware version", 0, shareware=True)

    def load_wl6_episodes(self):
        if not self.loader.wl6_maps_present():
            self.render(
                loading="Could not find GAMEMAPS.WL6 or MAPHEAD.WL6 files, trying to find them automatically.")
            pygame.display.flip()
            time.sleep(1)
            try:
                helper = WolfInstallationFinder()
                if not helper.find_installation():
                    return
                else:
                    self.loader.init_map_filepaths()
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
                break
            self.render(loading=f"map {i} from {self.loader.maps_path}")
            pygame.display.flip()
            time.sleep(0.01)
            i += 1

        if not self.loaded_music:
            self.render(loading="now synthesizing wl6 music")
            pygame.display.flip()
            self.loader.dump_wl6_music()
            ASSET_MANAGER.init_sounds(root=ASSET_MANAGER.sound_path, depth=1)

        epnames = [
            "Escape from Wolfenstein",
            "Operation: Eisenfaust",
            "Die, Führer, Die!",
            "A Dark Secret",
            "Trail of the Madman",
            "Confrontation"
        ]

        wl6_episodes = [WolfEpisode(
            wl6_maps[i*10: (i+1)*10],
            f"Episode {i+1} {epnames[i]}", i) for i in range(6)]
        return wl6_episodes

    def render(self, loading=None, clear=True):
        if clear:
            self.screen.fill(self.BG_COLOR)
        self.render_version()
        self.render_control_instructions()
        if self.loading:
            return self.render_loading_screen(loading)

    def load_all(self):
        self.loading = True
        self.episodes = []
        shareware_episode = self.load_shareware_episode()
        self.episodes.append(shareware_episode)
        self.wl6_episodes = self.load_wl6_episodes()
        if self.wl6_episodes:
            self.episodes.extend(self.wl6_episodes)
        else:
            self.render(
                "Could not locate original 6 episodes in your maps folder.")
            pygame.display.flip()
            time.sleep(2)

        self.loading = False
        self.loaded_music = True

    def build_game(self):
        wolflogger.info(
            f"Game starting with episode {self.episode.name} and difficulty {self.difficulty}")
        self.game = WolfGame(
            self.episode, self.difficulty,
            self.screen, sound_off=self.soundoff,
            framerate=75, player_rays=self.raycount, player_fov=self.fov)

    def start_game(self):
        if getattr(self, "game", None) is None:
            return
        self.game.mainloop()

    def run(self):
        self.loaded_music = False
        while True:
            self.load_all()
            self.build_menu_tree()
            self.menu_handler.start()

            self.build_game()
            self.start_game()


def main():
    # with cProfile.Profile() as pr:
    controller = WolfSessionController("Alpha")
    controller.run()

    # pr.dump_stats("wolf.prof")
