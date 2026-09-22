
from raycaster.aux_math import *
from raycaster.raycaster import Observer, Raycaster
from raycaster.renderer import RayRenderer, PointLight
from .animations import Animation
from .maps import *
from .player import *
from .actors import *
from .assets import SPRITES, WALL_TEXTURES
from . import wolflogger, pygame


LIGHT_OPTIONS = [PointLight((0, 0))]


class WolfRenderer(RayRenderer):
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
        self.wpn_sprite_idx = self.player.weapon.value * 5
        self.font = pygame.font.SysFont("arial", 12)

    def middle_hitblock(self):
        if self.colls:
            middle_hit, _, _ = self.colls[self.player.ray_count // 2]
            return self.map.to_block_pos(*middle_hit)

    def init_weapon_sprites(self):
        weapons: dict = SPRITES["weapons"]
        self.weapons = {}
        for i in weapons:
            w: Sprite = weapons[i]
            # transform each weapon sprite to match the screen size
            self.weapons[i] = Sprite(w.image.resize(self.pgsurface.get_size()))

    def render_weapon(self):
        self.pgsurface.blit(
            self.weapons[self.wpn_sprite_idx].surface,
            (0, 0))

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

    def render(self):
        super().render(self.light)
        self.render_weapon()
        self.render_statusbar()

    def clear_screen(self):
        self.pgsurface.fill(self.WHITE)
        self.pgsurface.fill(self.BLACK)


class WolfGame:
    def __init__(self, player: WolfPlayer, renderer: WolfRenderer, framerate=50):
        self.player = player
        self.renderer = renderer
        self.map = self.player.map
        self.actors = self.map.actors
        self.framerate = framerate
        self.heartbeats = 0

        self.init_keymappings()

        self.clock = pygame.time.Clock()
        # game events to schedule: (ticks-> func)
        self.game_events = {}
        self.animations: list[Animation] = []

        self.ongoing = True
        self.interact = False

    def init_keymappings(self):
        self.key_mappings = {
            pygame.K_w: self.player.move_forward,
            pygame.K_s: self.player.move_backward,
            pygame.K_a: self.player.turn_cw,
            pygame.K_d: self.player.turn_cc,
            pygame.K_SPACE: lambda: setattr(self, "interact", True)
        }

    def handle_player_requests(self):
        pblock: tuple = self.player.get_current_block()
        # if there is an item on the player block
        if pblock in self.map.items:
            item = self.map.pop_item(pblock)
            item.affect(self.player)

        fblock, fcell = self.player.get_front_cell()
        if fcell in self.map.DOOR and self.interact:
            door = self.map.get_door(fblock)
            if not door.is_opening:
                door.begin_opening()

    def add_animation(self, anim, obj, target):
        anim.obj = obj
        anim.target_attr = target
        self.animations.append(anim)

    def shooting_animation_end(self):
        wolflogger.debug("shooting_animation_end called.")
        self.player.ammo -= 1
        self.renderer.wpn_sprite_idx = self.player.weapon.value * 5
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_RETURN] and self.player.has_automatic_weapon():
            # if the player is still holding down shoot_button
            # and they have an automatic weapon
            # don't stop
            return self.handle_shooting(ongoing=True)

        self.player.shooting = False

    def handle_shooting(self, ongoing=False):
        wolflogger.debug("called handle_shooting")
        rapid = ongoing.real
        cantshoot = (
            self.player.shooting and not ongoing) or self.player.out_of_ammo()
        if cantshoot:
            wolflogger.debug("player already shooting, or out of ammo")
            return
        self.player.shooting = True
        # handle shooting animation
        old = self.renderer.wpn_sprite_idx

        self.add_animation(Animation(
            None, None, 20-10*rapid, 5-3*rapid, 0,
            endcallback=self.shooting_animation_end, offset=old + 2*rapid),
            self.renderer, "wpn_sprite_idx")

        for act in self.actors:
            if self.player.hits_actor(self.renderer.raycaster, act):
                damage = self.player.hit_damage(act)
                act.get_shot(self, damage)

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
                self.ongoing = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.handle_shooting()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.interact = False
                
        self.handle_keystate()

    def schedule_game_event(self, _time, action):
        future = self.heartbeats + _time
        while future in self.game_events:
            # schedule one tick later so they dont collide
            future += 1
        self.game_events[future] = action

    def handle_game_events(self):
        if not self.heartbeats in self.game_events:
            return
        func = self.game_events[self.heartbeats]
        if callable(func):
            try:
                func(self)
            except TypeError:
                return

    def handle_animations(self, dt=1):
        for anim in self.animations:
            if anim.ended():
                self.animations.remove(anim)
                continue
            anim.tick(dt)

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
        self.heartbeats += 1
