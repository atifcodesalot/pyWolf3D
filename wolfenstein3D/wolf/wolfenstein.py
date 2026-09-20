
from raycaster.aux_math import *
from raycaster.raycaster import Observer, Raycaster
from raycaster.renderer import RayRenderer, PointLight
from .maps import *
from .actors import *
from .assets import SPRITES, WALL_TEXTURES
from . import wolflogger, pygame

LIGHT_OPTIONS = [PointLight((0, 0))]


class WolfPlayer(Observer):
    def __init__(self, map_: WolfMap, fov=60,
                 ray_count=256, health=100, weapon=None):
        super().__init__(map_.init_pos, map_.init_look, fov, ray_count)
        self.map = map_
        self.health = health
        self.weapon = weapon
        self.pace = 2
        self.rot_pace = 3
        self.ammo = 0

    def move_forward(self):
        self.displace(plain_mul(self.look_dir, self.pace))

    def move_backward(self):
        self.displace(disp=plain_mul(self.look_dir, -self.pace*1.2))

    # collide with occupied cells
    def displace(self, disp):
        new_pos = plain_add(self.pos, plain_mul(disp, 4))
        if self.map.cell_occupied(new_pos):
            # wolflogger.debug(f"Can't displace to {new_pos}")
            return
        self.translate(disp)

    def turn_cc(self):
        self.rotate(self.rot_pace)

    def turn_cw(self):
        self.rotate(-self.rot_pace)

    def shoot(self):
        self.ammo -= 1

    def get_current_cell(self):
        block_pos = self.get_current_block()
        return self.map.get_cell(block_pos)

    def get_current_block(self):
        return self.map.to_block_pos(*self.pos)

    def get_front_cell(self):
        pblock = self.map.to_block_pos(*self.pos)
        offset = [0, 0]
        mag = max(self.look_dir, key=abs)
        # get if looking towards y
        vertical = self.look_dir.index(mag)
        offset[vertical] += sign(mag)
        front_block = plain_add(pblock, offset)
        front = self.map.raw[front_block[1]][front_block[0]]
        return front_block, front


class WolfRenderer(RayRenderer):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    def __init__(self, player: WolfPlayer, pgsurface: pygame.Surface):
        raycaster = Raycaster(player, player.map)
        super().__init__(raycaster, pgsurface,
                         topcolor="#282828",
                         bottomcolor="#707070",
                         wall_textures=WALL_TEXTURES)
        self.light = LIGHT_OPTIONS[0]
        self.init_weapon_sprites()

    def init_weapon_sprites(self):
        weapons: dict = SPRITES["weapons"]
        self.weapons = {}
        for i in weapons:
            w: Sprite = weapons[i]
            # transform each weapon sprite to match the screen size
            self.weapons[i] = Sprite(w.image.resize(self.pgsurface.get_size()))

    def render_weapon(self):
        self.pgsurface.blit(self.weapons[6].surface, (0,0))

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
        # game events to schedule: (ticks-> func)
        self.game_events = {}

    def init_keymappings(self):
        self.key_mappings = {
            pygame.K_w: self.player.move_forward,
            pygame.K_s: self.player.move_backward,
            pygame.K_a: self.player.turn_cw,
            pygame.K_d: self.player.turn_cc,
            pygame.K_SPACE: "interact"
        }

    def handle_player_requests(self):
        pblock: tuple = self.player.get_current_block()
        # if there is an item on the player block
        if pblock in self.map.items:
            item = self.map.pop_item(pblock)
            item.affect(self.player)

        fblock, fcell = self.player.get_front_cell()
        if fcell in self.map.DOOR:
            door = self.map.get_door(fblock)
            if not door.is_opening:
                door.begin_opening()

    def handle_doors(self):
        for door in self.map.doors.values():
            if door.is_opening:
                self.open_door(door)
            elif door.is_closing:
                self.close_door(door)

    def open_door(self, door: WolfDoor):
        if door.opening > 0:
            door.slide_open()
        else:
            # door has finished opening
            door.is_opening = False
            self.schedule_game_event(200, lambda _: door.begin_closing())

    def close_door(self, door: WolfDoor):
        if door.opening < 1:
            door.slide_close()
        else:
            # door has finished closing
            door.is_closing = False

    def handle_keystate(self):
        pressed = pygame.key.get_pressed()
        for key, action in self.key_mappings.items():
            if pressed[key]:
                if callable(action):
                    action()

    def handle_mouse(self):
        pass

    def handle_events(self, pgevents):
        for event in pgevents:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        self.handle_keystate()

    def schedule_game_event(self, future, action):
        self.game_events[self.beats + future] = action

    def handle_game_events(self):
        if not self.beats in self.game_events:
            return
        func = self.game_events[self.beats]
        if callable(func):
            try:
                func(self)
            except TypeError:
                return
            
    def handle_animations(self):
        pass

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
        self.handle_player_requests()
        self.handle_events(pgevents)
        self.handle_game_events()
        self.handle_doors()
        self.handle_animations()
        self.beats += 1
