
from raycaster.aux_math import *
from raycaster.raycaster import Observer, Raycaster
from raycaster.renderer import RayRenderer, PointLight
from .animations import Animation
from .maps import *
from .player import *
from .actors import *
from .assets import SPRITES, WALL_TEXTURES
from . import wolflogger, pygame
import numpy as np


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
        # insert 0 for empty
        self.wall_textures.insert(0, None)
        #
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
            w: Sprite = weapons[i]
            # transform each weapon sprite to match the screen size
            self.weapons[i] = Sprite(w.image.resize(self.pgsurface.get_size(),
                                                    resample=Image.Resampling.NEAREST))
            surf = self.weapons[i].surface
            self.wpn_xoffset = self.width // 6
            x = self.wpn_xoffset
            self.weapons[i].surface = surf.subsurface(
                (x, surf.get_height()//2,
                 surf.get_width()-x*2, surf.get_height()//2))

    def render_weapon(self):
        self.pgsurface.blit(
            self.weapons[self.weap_sp].surface,
            (self.wpn_xoffset, self.height // 2))

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

    def render(self, heartbeats):
        self.pgsurface.fill(self.topcolor, rect=self.toprect)
        self.pgsurface.fill(self.bottomcolor, rect=self.bottrect)
        super().render(self.light)
        if self.glow:
            self.handle_glow()
        self.render_weapon()
        self.render_statusbar()
        self.heartbeats += heartbeats

    def fizzle_fade(self):
        # grab a cheap pixel reference
        pixelref = pygame.PixelArray(self.pgsurface)
        #
        w, h = pixelref.shape
        red = 0
        for i in self.shuffled_indices:
            pos = (i % w, i // h)
            pixelref[pos] = 0xFF0000
            red += 1
            if not red % 15:
                # update display per 15 writes
                pygame.display.flip()
                pass

        del pixelref

    def glow_end(self):
        self.rgb_offset = [0, 0, 0]
        self.glow = False
        self.glow_cycle = 0

    def clear_screen(self):
        self.pgsurface.fill(self.WHITE)
        self.pgsurface.fill(self.BLACK)


class WolfGame:
    def __init__(self, player: WolfPlayer, renderer: WolfRenderer, framerate=50):
        self.player = player
        self.wolfmap = self.player.map
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

    def handle_item_pickup(self, player_block):
        item = self.map.items[player_block]
        if not item.is_health_item:
            self.map.pop_item(player_block)
            item.affect(self.player)
            self.renderer.glow = (0, 1)
        else:
            if self.player.health != 100:
                self.map.pop_item(player_block)
                item.affect(self.player)
                self.renderer.glow = (0, 1)

    def handle_interaction(self):
        fblock, fcell = self.player.get_front_cell()
        if fcell in self.map.DOOR:
            door = self.map.get_door(fblock)
            if not door.is_opening:
                door.begin_opening()
        elif fblock in self.map.pushwalls:
            pushwall = self.map.get_pushwall(fblock)
            if not pushwall.sliding:
                sliding_dir = [0, 0]
                ldir = self.player.look_dir
                maxdir = max(ldir, key=abs)
                # get where the player looks,
                # i.e closest to which axis
                vertical = ldir.index(maxdir)
                sliding_dir[vertical] = sign(ldir[vertical])
                wolflogger.debug(
                    f"player interacted with pushwall: {sliding_dir}")
                pushwall.begin_sliding(sliding_dir)

    def handle_player_requests(self):
        # placeho0lder
        self.renderer.weap_sp = self.player.weapon.value * self.renderer.sp_per_weap
        pblock: tuple = self.player.get_current_block()
        # if there is an item on the player block
        if pblock in self.map.items:
            self.handle_item_pickup(pblock)
            # set glow false after 40 frames
            self.schedule_game_event(
                self.renderer.glow_duration, lambda s: s.renderer.glow_end())
        if self.interact:
            self.handle_interaction()

    def dec_player_health(self, dmg):
        self.renderer.glow = (0,)
        self.player.dec_health(dmg)
        self.schedule_game_event(
            self.renderer.glow_duration, lambda s: s.renderer.glow_end())

    def add_animation(self, anim, obj, target):
        anim.obj = obj
        anim.target_attr = target
        self.animations.append(anim)

    def shooting_animation_end(self):
        wolflogger.debug("shooting_animation_end called.")
        self.renderer.weap_sp = self.player.weapon.value * 5
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_RETURN] and self.player.has_auto():
            # if the player is still holding down the shoot button
            # and they have an automatic weapon
            # don't stop
            return self.handle_shooting(ongoing=True)

        self.player.shooting = False
        if self.player.out_of_ammo() and not self.player.has_knife():
            self.player.switch_weapon(WolfWeapon.KNIFE, forced_switch=True)

    def handle_hitscan(self):
        for act in self.actors:
            if act.is_dead():
                continue
            if self.player.hits_actor(self.renderer.raycaster, act):
                if self.player.has_knife():
                    ablock = self.map.to_block_pos(*act.pos)
                    pblock = self.player.get_current_block()
                    if euclidean_distance(ablock, pblock) < 2:
                        act.get_shot(damage=75)
                else:
                    damage = self.calculate_damage(act)
                    act.get_shot(damage)

    def calculate_damage(self, actor: Actor, reduction=1):
        pblock = self.player.get_current_block()
        ablock = self.wolfmap.to_block_pos(*actor.pos)
        d = euclidean_distance(pblock, ablock)
        d = 1 if d == 0 else d
        inflicted = (1 / d) * 175
        # cap to 100
        return min(int(inflicted * reduction), 100)

    def handle_shooting(self, ongoing=False):
        wolflogger.debug("called handle_shooting")
        no_ammo = self.player.out_of_ammo()
        cant_shoot = (
            (self.player.shooting and not ongoing) or
            (no_ammo and not self.player.has_knife())
        )
        if cant_shoot:
            wolflogger.debug("player can't shoot.")
            return
        # can shoot
        self.player.shooting = True
        self.player.dec_ammo()

        # handle shooting animation
        old = self.renderer.weap_sp
        rapid = ongoing.real
        self.add_animation(Animation(
            None, None, 20-10*rapid, 5-3*rapid, 0,
            endcallback=self.shooting_animation_end, offset=old + 2*rapid),
            self.renderer, "weap_sp")
        self.handle_hitscan()

    def handle_doors(self):
        for door in self.map.doors.values():
            if door.is_opening:
                self.open_door(door)
            elif door.is_closing:
                self.close_door(door)

    def handle_secrets(self):
        revealed = list(filter(lambda p: p.sliding,
                        self.map.pushwalls.values()))
        for pushwall in revealed:
            if pushwall.sliding:
                pushwall.slide_open(self.map)

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

    def handle_animations(self, heartbeats=1):
        for anim in self.animations:
            if anim.ended():
                self.animations.remove(anim)
                continue
            anim.tick(heartbeats)

    def heartbeat(self):
        self.clock.tick(self.framerate)
        # render everything
        if type(self.renderer.light) is PointLight:
            self.renderer.light.pos = self.player.pos
        self.renderer.clear_screen()
        self.renderer.render(heartbeats=1)
        #
        for actor in self.actors:
            actor.tick(self, 1)
        pgevents = pygame.event.get()
        self.handle_player_requests()
        self.handle_events(pgevents)
        self.handle_game_events()
        self.handle_doors()
        self.handle_secrets()
        self.handle_animations()
        self.heartbeats += 1

    def mainloop(self):
        self.ongoing = True
        while self.ongoing:
            self.heartbeat()
            if self.player.is_dead():
                if self.player.lives == 0:
                    return self.game_end()
                self.life_end()
            pygame.display.flip()

    def floor_end(self):
        pass

    def life_end(self):
        print("YOU ARE DEAD, BJ!")
        self.renderer.fizzle_fade()
        
    def game_end(self):
        pass
        
        
