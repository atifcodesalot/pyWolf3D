
from raycaster.aux_math import *
from .maps import *
from .player import *
from .actors import *
from .sound import WolfSoundManager
from ._3Drenderer import Wolf3DRenderer, PointLight
from ._2Drenderer import Wolf2DRenderer
from . import wolflogger, pygame
import time
from .game_objects import WEAPON_SOUND


class Animation:
    def __init__(self, obj, target_attr: str, duration,
                 frame_count, shapenum=0, endcallback=None, offset=0):
        # in heartbeats
        self.duration = duration
        #
        self.obj = obj
        self.target_attr = target_attr
        self.frame_count = frame_count
        self.shapenum = shapenum
        self.hb_perframe = self.duration / self.frame_count

        self.lifetime = 0
        self.endcallback = endcallback
        self.offset = offset

    def tick(self, heartbeats):
        self.lifetime += heartbeats
        if self.ended():
            if callable(self.endcallback):
                self.endcallback()
            return
        self.shapenum = self.lifetime // self.hb_perframe
        setattr(self.obj, self.target_attr, self.shapenum + self.offset)

    def ended(self) -> bool:
        return self.lifetime >= self.duration


class WolfGame:
    jukebox = [
        "level1_5.ogg",
        None,
        None,
    ]

    def __init__(self, player: WolfPlayer, root_display, framerate=60, sound_off=False, noclip=False):
        self.player = player
        self.root_display = root_display
        self.wolfmap = self.player.map
        self.game_res = (640, 420)
        self.game_surf = pygame.Surface(self.game_res)
        self.game_renderer = Wolf3DRenderer(self.player, self.game_surf)
        self.renderer = Wolf2DRenderer(root_display.get_size(), self.game_res)
        self.map = self.player.map
        self.actors = self.map.get_actors()
        self.framerate = framerate
        self.heartbeats = 0

        self.init_keymappings()

        self.clock = pygame.time.Clock()
        # game events to schedule: (ticks-> func)
        self.game_events = {}
        self.animations: list[Animation] = []

        self.ongoing = True
        self.interact = False

        self.areabyplayer = [[0,]*37]*37

        self.sound_manager = WolfSoundManager(master=1)

        if sound_off:
            self.sound_manager.set_master(0)
        self.noclip = noclip

    def init_keymappings(self):
        self.key_mappings = {
            pygame.K_w: self.move_player,
            pygame.K_s: lambda: self.move_player(sign_=-1),
            pygame.K_a: self.player.turn_cw,
            pygame.K_d: self.player.turn_cc,
            pygame.K_SPACE: lambda: setattr(self, "interact", True),
            pygame.K_LSHIFT: lambda: setattr(self.player, "running", True)
        }

    def handle_item_pickup(self, player_block):
        item = self.map.item_lookup[player_block]
        if not item.is_health_item:
            self.map.pop_item(player_block)
            item.affect(self.player)
            self.game_renderer.glow = (0, 1)
        else:
            if self.player.health != 100:
                self.map.pop_item(player_block)
                item.affect(self.player)
                self.game_renderer.glow = (0, 1)

    def move_player(self, sign_=1):
        pace = self.player.pace*2 if self.player.running else self.player.pace
        disp = vec_mul(self.player.look_dir, pace * sign_)
        m = self.map
        pos = self.player.pos
        xdisp = vec_mul(BASIS[0], vec_dot(BASIS[0], disp))
        ydisp = vec_mul(BASIS[1], vec_dot(BASIS[1], disp))
        if self.noclip:
            return self.player.translate(vec_add(xdisp, ydisp))
        xtry = m.to_block_pos(*vec_add(pos, vec_mul(xdisp, 5)))
        if not self.player.occupied_forthis(xtry):
            self.player.pos = vec_add(pos, xdisp)
        ytry = m.to_block_pos(*vec_add(pos, vec_mul(ydisp, 5)))
        if not self.player.occupied_forthis(ytry):
            self.player.pos = vec_add(self.player.pos, ydisp)

    def handle_areas(self):
        player_area = self.player.get_current_area()
        if player_area > 37 or 0 > player_area:
            wolflogger.warning("player area out of bounds!")
            return
        self.areabyplayer = self.map.area_matrix[player_area]
        self.areabyplayer[player_area] = 1

    def door_alert(self, door: WolfDoor):
        actors = self.wolfmap.actorsby_areas(door.area0, door.area1)
        for act in actors:
            act.alert(self)

    def handle_interaction(self):
        fblock, fcell = self.player.get_front_cell()
        if self.map.cell_is_door(fcell):
            door = self.map.get_door(fblock)
            if not door.is_opening:
                if type(door) is WolfDoor:
                    self.open_door(door)
                    return
                # door is locked
                if getattr(self.player, door.key, None):
                    self.open_door(door)

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
                slidesnd = SOUNDS["doors"]["PUSHWALLSND.WAV"]
                self.schedule_sound_effect(slidesnd, None, 5)

    def handle_player_requests(self):
        # placeholder
        self.game_renderer.weap_sp = self.player.weapon.value * \
            self.game_renderer.sp_per_weap
        pblock: tuple = self.player.get_current_block()
        # if there is an item on the player block
        if pblock in self.map.item_lookup:
            self.handle_item_pickup(pblock)
            # set glow false after 40 frames
            self.schedule_game_event(
                self.game_renderer.glow_duration,
                lambda s: s.game_renderer.glow_end())
        if self.interact:
            self.handle_interaction()

    def dec_player_health(self, dmg):
        self.game_renderer.glow = (0,)
        self.player.dec_health(dmg)
        self.schedule_game_event(
            self.game_renderer.glow_duration,
            lambda s: s.game_renderer.glow_end())
        self.renderer.update_hud(self.player)

    def add_animation(self, anim, obj, target):
        anim.obj = obj
        anim.target_attr = target
        self.animations.append(anim)

    def shooting_animation_end(self):
        wolflogger.debug("shooting_animation_end called.")
        self.game_renderer.weap_sp = self.player.weapon.value * 5
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
            if self.player.hits_actor(self.game_renderer.raycaster, act):
                if self.player.has_knife():
                    ablock = self.map.to_block_pos(*act.pos)
                    pblock = self.player.get_current_block()
                    if euclidean_distance(ablock, pblock) < 2:
                        act.get_shot(damage=75, game_ctx=self)
                else:
                    damage = self.calculate_damage(act)
                    act.get_shot(damage, self)

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
            if ongoing and no_ammo:
                self.player.shooting = False
                self.player.switch_weapon(WolfWeapon.KNIFE, forced_switch=True)
            wolflogger.debug("player can't shoot.")
            return
        # can shoot
        shootsnd = SOUNDS["weapons"].get(WEAPON_SOUND[self.player.weapon])
        if shootsnd:
            self.schedule_sound_effect(shootsnd, None, 1)
        self.player.shooting = True
        self.player.dec_ammo()

        # handle shooting animation
        old = self.game_renderer.weap_sp
        rapid = ongoing.real
        if rapid:
            if self.player.weapon.value == 2:
                # machine gun
                rate = 10
            else:
                # chain gun
                rate = 5
        else:
            rate = 25
        self.add_animation(Animation(
            None, None, rate, 5-3*rapid, 0,
            endcallback=self.shooting_animation_end, offset=old + 2*rapid),
            self.game_renderer, "weap_sp")
        self.handle_hitscan()

    def handle_doors(self):
        for door in self.map.doors.values():
            if door.is_opening:
                self.slide_door_open(door)
            elif door.is_closing:
                self.slide_door_close(door)

    # door related methods start here
    #
    def open_door(self, door):
        door.begin_opening()
        self.door_alert(door)
        snd = SOUNDS["doors"]["OPENDOORSND.WAV"]
        self.schedule_sound_effect(snd, origin=door.globpos, _time=1)

    def shut_door(self, door):
        snd = SOUNDS["doors"]["CLOSEDOORSND.WAV"]
        self.schedule_sound_effect(snd, origin=door.globpos, _time=1)
        door.is_closing = False

    def slide_door_open(self, door: WolfDoor):
        if door.opening > 0:
            door.slide_open()
        else:
            # door has finished opening
            door.is_opening = False
            self.schedule_game_event(200, lambda _: door.begin_closing())

    def slide_door_close(self, door: WolfDoor):
        if door.opening < 1:
            door.slide_close()
        else:
            # door has finished closing
            self.shut_door(door)

    # door related methods end here

    def handle_secrets(self):
        revealed = list(filter(lambda p: p.sliding,
                        self.map.pushwalls.values()))
        for pushwall in revealed:
            if pushwall.sliding:
                pushwall.slide_open(self.wolfmap)

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
                if event.key == pygame.K_LSHIFT:
                    self.player.running = False
        self.handle_keystate()

    def schedule_game_event(self, _time, action):
        future = self.heartbeats + _time
        while future in self.game_events:
            # schedule one tick later so they dont collide
            future += 1
        self.game_events[future] = action

    def schedule_sound_effect(self, snd, origin, _time):
        self.sound_manager.queue_sound_effect(snd, origin, self, _time)

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

    def handle_actors(self):
        for actor in self.actors:
            actor.tick(self, 1)

    def render_game(self):
        if type(self.game_renderer.light) is PointLight:
            self.game_renderer.light.pos = self.player.pos
        self.game_renderer.clear_screen()
        self.game_renderer.render(heartbeats=1)

    def render(self):
        self.render_game()
        game_screen = self.game_renderer.pgsurface
        self.renderer.heartbeat(game_screen, self.player)

    def heartbeat(self):
        self.heartbeats += 1
        self.clock.tick(self.framerate)
        pgevents = pygame.event.get()
        self.handle_actors()
        self.handle_player_requests()
        self.handle_events(pgevents)
        self.handle_game_events()
        self.handle_doors()
        self.handle_secrets()
        self.handle_animations()
        self.handle_areas()
        self.sound_manager.handle_sound(self)
        # render everything
        self.render()
        #

    def mainloop(self, music=None):
        if music is None:
            music = self.jukebox[0]
        self.sound_manager.play_music(music)
        self.ongoing = True
        while self.ongoing:
            self.heartbeat()
            # self.root_display.fill("#ffffff")
            self.root_display.blit(self.renderer.pgsurf, (0, 0))
            pygame.display.flip()
            if self.player.is_dead():
                self.life_end()

    def floor_end(self):
        pass

    def life_end(self):
        self.player.lives -= 1
        self.renderer.update_hud(self.player)
        self.render()
        self.sound_manager.handle_sound(self)
        pygame.display.flip()
        killer = getattr(self, "player_slayer", None)
        if killer:
            self.player.turn_to_killer(
                self, killer=killer, master_surf=self.root_display,
                update_dest=self.renderer.game_off)

        self.game_renderer.fizzle_fade(
            self.root_display, update_dest=self.renderer.game_off)
        self.player.reset()
        self.map.reset()
        self.game_renderer.glow = False
        time.sleep(0.6)
        if self.player.lives == 0:
            return self.game_end()
        self.game_renderer.unfizzle(
            self.root_display, update_dest=self.renderer.game_off)

    def game_end(self):
        exit("game over!")
