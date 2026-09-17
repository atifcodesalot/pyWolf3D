
from raycaster.aux_math import *
from raycaster.raycaster import Observer, Raycaster
from raycaster.renderer import RayRenderer, PointLight, pygame
from .maps import *
from .actors import *


LIGHT_OPTIONS = [PointLight((0, 0))]


class WolfPlayer(Observer):
    def __init__(self, pos, map: WolfMap, look_dir=[1, 0],
                 fov=60, ray_count=256, health=100, weapon=None):
        super().__init__(pos, look_dir, fov, ray_count)
        self.map = map
        self.health = health
        self.weapon = weapon
        self.pace = 1
        self.rot_pace = 3

    def move_forward(self):
        self.translate(plain_mul(self.look_dir, self.pace))

    def move_backward(self):
        self.translate(plain_mul(self.look_dir, -self.pace*1.2))

    def turn_cc(self):
        self.rotate(self.rot_pace)

    def turn_cw(self):
        self.rotate(-self.rot_pace)

    def pickup_item(self):
        pass

    def shoot(self):
        pass


class WolfRenderer(RayRenderer):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    def __init__(self, player: WolfPlayer, pgsurface):
        raycaster = Raycaster(player, player.map)
        super().__init__(raycaster, pgsurface,
                         topcolor="#282828", bottomcolor="#707070")
        self.light = LIGHT_OPTIONS[0]

    def render_weapon(self):
        pass

    def render_statusbar(self):
        pass

    def render(self):
        super().render(self.light)
        self.render_weapon()
        self.render_statusbar()

    def clear_screen(self):
        self.pgsurface.fill(self.WHITE)
        self.pgsurface.fill(self.BLACK)


class WolfGame:
    def __init__(self, player: WolfPlayer, renderer: WolfRenderer,
                 actors: list[Actor], framerate=50):
        self.player = player
        self.renderer = renderer
        self.map = self.player.map
        self.actors = actors
        self.framerate = framerate
        self.beats = 0

        self.init_keymappings()

        self.clock = pygame.time.Clock()

    def init_keymappings(self):
        self.key_mappings = {
            pygame.K_w: self.player.move_forward,
            pygame.K_s: self.player.move_backward,
            pygame.K_a: self.player.turn_cw,
            pygame.K_d: self.player.turn_cc,
            pygame.K_SPACE: "interact"
        }

    def handle_keystate(self):
        pressed = pygame.key.get_pressed()
        for key, action in self.key_mappings.items():
            if pressed[key]:
                if callable(action):
                    action()
                elif action == "interact":
                    self.player.pickup_item()

    def handle_mouse(self):
        pass

    def handle_events(self, pgevents):
        for event in pgevents:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        self.handle_keystate()

    def heartbeat(self):
        dt = self.clock.tick(self.framerate)
        # render everything
        if type(self.renderer.light) is PointLight:
            self.renderer.light.pos = self.player.pos
        self.renderer.clear_screen()
        self.renderer.render()
        #
        for actor in self.actors:
            actor.tick(dt)
        pgevents = pygame.event.get()
        self.handle_events(pgevents)
        self.beats += 1
