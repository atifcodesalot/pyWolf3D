
from wolfenstein3D.raycaster.aux_math import *
from wolfenstein3D.raycaster.sprites import Projectile
from wolfenstein3D.wolf.maps import *
from wolfenstein3D.wolf.player import *
from wolfenstein3D.wolf.actors import *
from wolfenstein3D.wolf.sound import WolfSoundManager
from wolfenstein3D.wolf.assets import ASSET_MANAGER
from wolfenstein3D.wolf._3Drenderer import Wolf3DRenderer, PointLight
from wolfenstein3D.wolf._2Drenderer import Wolf2DRenderer
from wolfenstein3D.wolf import wolflogger, pygame
from wolfenstein3D.wolf.game_objects import WEAPON_SOUND
import time


SOUNDS = ASSET_MANAGER.sounds
SPRITES = ASSET_MANAGER.sprites


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
    SECRET_TILE = 107
    SWITCH_UP = 42

    def __init__(self, episode: WolfEpisode, difficulty: WolfDifficulty, root_display, framerate=60,
                 sound_off=False, noclip=False, lvl_offset=0, player_rays=160, player_fov=50):
        self.episode = episode
        self.difficulty = difficulty
        self.begin_episode(lvl_offset)

        self.player = WolfPlayer(self, fov=player_fov, ray_count=player_rays)
        self.init_renderers(root_display)

        self.framerate = framerate
        self.heartbeats = 0

        self.init_keymappings()
        self.init_mouse()

        # game events to schedule: (ticks-> func)
        self.game_events = {}
        self.animations: list[Animation] = []
        self.projectiles: list[Projectile] = []

        self.ongoing = True
        self.interact = False

        # used for sound propagation
        self.areabyplayer = [[0,]*37]*37
        self.noclip = noclip

        self.clock = pygame.time.Clock()
        self.sound_manager = WolfSoundManager(master=1)
        if sound_off:
            self.sound_manager.set_master(0)

        self.new_floor = False
        self.new_life = False
        self.floor_fin = False
        self.music_paused = False

        self.wait_between_states = 0.25

    def init_renderers(self, root):
        self.game_res = (640, 420)
        self.game_surf = pygame.Surface(self.game_res)
        self.root_display = root
        self.game_renderer = Wolf3DRenderer(self.player, self.game_surf)
        self.renderer = Wolf2DRenderer(root.get_size(), self.game_res)

    def init_map(self):
        self.wolfmap.set_difficulty(self.difficulty)
        self.wolfmap.init_snap = self.wolfmap.snapshot()
        self.wolfmap.init_actor_lookup()
        self.player.map = self.wolfmap
        self.player.pos = self.wolfmap.init_pos.copy()
        self.player.update_look_dir(self.wolfmap.init_look.copy())
        self.actors = self.wolfmap.get_actors()

        music = self.get_music()
        self.sound_manager.play_music(
            music, _dir="shareware" if self.episode.shareware else "originals")

    def begin_episode(self, lvl_offset):
        self.wolfmap = self.episode[lvl_offset]
        self.jukebox = self.episode.jukebox

    def start_timer(self):
        self.start_time = time.monotonic()

    def init_keymappings(self):
        self.key_mappings = {
            pygame.K_w: self.move_player,
            pygame.K_s: lambda: self.move_player(sign_=-1),
            pygame.K_a: self.player.turn_cw,
            pygame.K_d: self.player.turn_cc,
            pygame.K_SPACE: lambda: setattr(self, "interact", True),
            pygame.K_LSHIFT: lambda: setattr(self.player, "running", True),
            pygame.K_ESCAPE: lambda: self.game_end(chicken=True)
        }

    def toggle_pause(self):
        pygame.event.clear()
        self.paused = not self.paused

    def init_mouse(self):
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

    def handle_item_pickup(self, player_block):
        item = self.wolfmap.item_lookup[player_block]
        if item.pickup_condition(self.player):
            item = self.wolfmap.pop_item(player_block)
            item.pickup(self)

    def move_player(self, sign_=1):
        pace = self.player.pace*2 if self.player.running else self.player.pace
        disp = vec_mul(self.player.look_dir, pace * sign_)
        if self.noclip:
            return self.player.translate(disp)
        m = self.wolfmap
        pos = self.player.pos
        xdisp = vec_mul(BASIS[0], vec_dot(BASIS[0], disp))
        ydisp = vec_mul(BASIS[1], vec_dot(BASIS[1], disp))

        adj_actors = self.player.get_adjacent_actors()
        xtry = vec_add(pos, vec_mul(xdisp, 5))
        xblock = m.to_block_pos(*xtry)
        if self.wolfmap.cell_occupied(xblock) or \
                self.player.actors_too_close(xtry, adj_actors):
            disp = vec_sub(xdisp, disp)
        ytry = vec_add(pos, vec_mul(ydisp, 5))
        yblock = m.to_block_pos(*ytry)
        if self.wolfmap.cell_occupied(yblock) or \
                self.player.actors_too_close(ytry, adj_actors):
            disp = vec_sub(ydisp, disp)
        xytry = vec_add(pos, vec_mul(disp, 5))
        xyblock = m.to_block_pos(*xytry)
        if self.wolfmap.cell_occupied(xyblock) or \
                self.player.actors_too_close(xytry, adj_actors):
            disp = [0, 0]
        self.player.translate(disp)

    def handle_areas(self):
        player_area = self.player.get_current_area()
        if player_area > 37 or 0 > player_area:
            wolflogger.debug("player area out of bounds!")
            return
        self.areabyplayer = self.wolfmap.area_matrix[player_area]
        self.areabyplayer[player_area] = 1

    def handle_interaction(self):
        fblock, fcell = self.player.get_front_cell()
        if self.wolfmap.cell_is_door(fcell):
            door = self.wolfmap.get_door(fblock)
            if not door.is_opening and door.opening == 1:
                if type(door) is WolfDoor:
                    self.open_door(door)
                    return
                # door is locked
                if getattr(self.player, door.key, None):
                    self.open_door(door)
                else:
                    self.schedule_sound_effect(
                        SOUNDS["adlib_effects"]["ALNOWAY.wav"], None, 1)

        elif fblock in self.wolfmap.pushwalls:
            pushwall = self.wolfmap.get_pushwall(fblock)
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

        elif self.wolfmap.cell_is_elevator(fcell):
            # check the player tile for secret floor
            self.wolfmap.raw[fblock[1]][fblock[0]] = self.SWITCH_UP
            self.schedule_sound_effect(
                SOUNDS["doors"]["LEVELDONESND.WAV"], None, 0)
            self.floor_fin = True

        else:
            self.schedule_sound_effect(
                SOUNDS["adlib_effects"]["ALNOTHIN.wav"], None, 1)

    def calm_player_down(self):
        self.player.excited_to_kill_nazis = False
        self.music_paused = False
        self.sound_manager.continue_music()

    def handle_player_requests(self):
        if self.player.excited_to_kill_nazis:
            if not self.music_paused:
                self.schedule_sound_effect(
                    SOUNDS["pickup"]["ALCGUNUP.wav"], None, 1)
                self.sound_manager.pause_music()
                self.schedule_game_event(
                    150, lambda _: self.calm_player_down())
                self.music_paused = True
        # placeholder
        self.game_renderer.wpn_sp = self.player.weapon.value * \
            self.game_renderer.sp_per_wpn
        #
        pblock: tuple = self.player.get_current_block()
        # if there is an item on the player block
        if pblock in self.wolfmap.item_lookup:
            self.handle_item_pickup(pblock)
            # set glow false after 40 frames
            self.schedule_game_event(
                self.game_renderer.glow_duration,
                lambda s: s.game_renderer.glow_end())
        if self.interact:
            self.handle_interaction()

    def hurt_player(self, dmg):
        if dmg == 0:
            # actor missed
            return
        self.game_renderer.begin_glow((0,), dmg*2)
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
        self.game_renderer.wpn_sp = self.player.weapon.value * 5
        pressed = pygame.key.get_pressed()
        ongoing = pressed[pygame.K_RETURN] or pygame.mouse.get_pressed()[0]
        if ongoing and self.player.has_auto():
            # if the player is still holding down the shoot button
            # and they have an automatic weapon
            # don't stop
            return self.handle_shooting(ongoing=ongoing)

        self.player.shooting = False
        if self.player.out_of_ammo() and not self.player.has_knife():
            self.player.switch_weapon(WolfWeapon.KNIFE)

    def handle_hitscan(self):
        # by now, because of the order of operations in a heartbeat,
        # visible sprites are already determined
        # use them for hitscan
        for act in self.wolfmap.get_actors():
            if act.is_dead() or act is None:
                continue
            if act.get_current_block() not in self.game_renderer.visited:
                continue
            if self.player.hits_actor(act, self.game_renderer.width):
                if self.player.has_knife():
                    ablock = self.wolfmap.to_block_pos(*act.pos)
                    pblock = self.player.get_current_block()
                    if euclidean_distance(ablock, pblock) <= 2:
                        act.get_shot(damage=10, game_ctx=self)
                else:
                    damage = self.calc_player_dmg(act)
                    act.get_shot(damage, self)

    def handle_projectiles(self):
        for pj in self.projectiles:
            if pj.exploding:
                if pj.explode():
                    self.projectiles.remove(pj)
                continue
            pj.travel(self)
            cm = pj.collides_map(self.wolfmap)
            cp = pj.collides_player(self)
            if cp or cm:
                pj.exploding = True
                if pj.explosion_snd:
                    self.schedule_sound_effect(pj.explosion_snd, pj.pos, 1)
                if cp:
                    self.hurt_player(20)

    def spawn_projectile(self, dir_, speed, pos, projectile: Projectile):
        projectile.update_direction(dir_)
        projectile.speed = speed
        projectile.pos = pos
        self.projectiles.append(projectile)

    def calc_player_dmg(self, actor: Actor):
        pblock = self.player.get_current_block()
        ablock = self.wolfmap.to_block_pos(*actor.pos)
        d = euclidean_distance(pblock, ablock)
        diceroll = random.randint(0, 255)
        divider = 6
        missed = None
        if d >= 2:
            divider = 4
        if d >= 4:
            missed = (diceroll // 12) < d

        if missed is not None:
            if missed:
                inflicted = 0
            else:
                diceroll2 = random.randint(0, 255)
                inflicted = diceroll2 // divider
        else:
            inflicted = diceroll // divider if not missed else 0

        return inflicted

    def calc_actor_dmg(self, actor: Actor):
        pblock = self.player.get_current_block()
        ablock = self.wolfmap.to_block_pos(*actor.pos)
        d = euclidean_distance(pblock, ablock)
        if actor.type is WolfActorType.SCHUTZSTAFFEL:
            d *= 2/3
        elif actor.is_boss:
            d *= 1/3
        chance = 0x100 - (0x10 // (1 + self.player.running.real)) * d
        diceroll = random.randint(0, 256)
        if chance < diceroll:
            return 0
        divider = 4
        if d >= 2:
            divider = 8
        if d >= 4:
            divider = 16
        inflicted = diceroll / divider
        if self.difficulty is WolfDifficulty.BABY:
            # take it easy
            inflicted /= 4
        return int(inflicted)

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
                self.player.switch_weapon(WolfWeapon.KNIFE)
            wolflogger.debug("player can't shoot.")
            return
        # can shoot
        shootsnd = SOUNDS["weapons"].get(WEAPON_SOUND[self.player.weapon])
        if shootsnd:
            self.schedule_sound_effect(shootsnd, None, 1)
        self.player.shooting = True
        self.player.dec_ammo()

        # handle shooting animation
        old = self.game_renderer.wpn_sp
        rapid = ongoing.real
        if rapid:
            if self.player.weapon.value == 2:
                # machine gun
                rate = 15
            else:
                # chain gun
                rate = 10
        else:
            rate = 30

        self.add_animation(Animation(
            None, None, rate, 5-3*rapid, 0,
            endcallback=self.shooting_animation_end, offset=old + 2*rapid),
            self.game_renderer, "wpn_sp")
        self.handle_hitscan()

    # door related methods start here
    #

    def handle_doors(self):
        for door in self.wolfmap.doors.values():
            if door.is_opening:
                self.slide_door_open(door)
            elif door.is_closing:
                self.slide_door_close(door)

    def open_door(self, door):
        door.begin_opening()
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
            self.schedule_game_event(
                200, lambda _: self.try_closing_door(door))

    def try_closing_door(self, door: WolfDoor):
        pblock = self.player.get_current_block()
        if door.block_pos in self.wolfmap.actor_lookup\
                or pblock == door.block_pos:
            # retry 200 heartbeats later
            self.schedule_game_event(
                200, lambda _: self.try_closing_door(door))
        else:
            door.begin_closing()

    def slide_door_close(self, door: WolfDoor):
        if door.opening < 1:
            door.slide_close()
        else:
            # door has finished closing
            self.shut_door(door)

    # door related methods end here

    def handle_secrets(self):
        revealed = list(filter(lambda p: p.sliding,
                        self.wolfmap.pushwalls.values()))
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
        rel = pygame.mouse.get_rel()
        # discard relative y movement
        xdisp = rel[0] / 8
        if xdisp > 0:
            self.player.turn_cc(abs(xdisp))
        elif xdisp < 0:
            self.player.turn_cw(abs(xdisp))

        if pygame.mouse.get_pressed()[0]:
            self.handle_shooting()

    def handle_pgevents(self, pgevents, paused=False):
        for event in pgevents:
            if paused:
                if event.type == pygame.QUIT:
                    self.ongoing = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.toggle_pause()
                return
            if event.type == pygame.QUIT:
                self.ongoing = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.toggle_pause()
                elif event.key == pygame.K_RETURN:
                    self.handle_shooting()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.interact = False
                if event.key == pygame.K_LSHIFT:
                    self.player.running = False

    def handle_events(self, pgevents):
        self.handle_pgevents(pgevents)
        self.handle_mouse()
        self.handle_keystate()

    def schedule_game_event(self, _time, action):
        future = self.heartbeats + _time
        while future in self.game_events:
            # schedule one tick later so they dont collide
            future += 1
        self.game_events[future] = action

    def schedule_sound_effect(self, snd, origin, _time, repeat=True):
        self.sound_manager.queue_sound_effect(
            snd, origin, self, _time, repeat=repeat)

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
        # bandaid for the actor lookup bug
        # todo: fix it and remove this
        mirror = self.wolfmap.actor_lookup.copy()
        for pos in mirror:
            if mirror[pos].is_dead():
                del self.wolfmap.actor_lookup[pos]

    def render_game(self):
        if type(self.game_renderer.light) is PointLight:
            self.game_renderer.light.pos = self.player.pos
        self.game_renderer.clear_screen()
        self.game_renderer.render(heartbeats=1, game_ctx=self)

    def render_all(self):
        self.render_game()
        game_screen = self.game_renderer.pgsurface
        self.renderer.heartbeat(game_screen, self.player)
        self.root_display.blit(self.renderer.pgsurf, (0, 0))

    def heartbeat(self):
        self.heartbeats += 1
        self.clock.tick(self.framerate)
        pgevents = pygame.event.get()
        self.handle_actors()
        # render everything
        self.render_all()
        #
        self.handle_player_requests()
        self.handle_events(pgevents)
        self.handle_game_events()
        self.handle_doors()
        self.handle_secrets()
        self.handle_animations()
        self.handle_projectiles()
        self.handle_areas()
        self.sound_manager.handle_sound(self)

    def get_music(self):
        mapid = self.wolfmap._id
        music = self.jukebox.get(mapid, None)
        if music is not None:
            return music
        return self.jukebox[0]

    def mainloop(self):
        self.ongoing = True
        self.paused = False

        self.floor_start()
        while self.ongoing:
            self.heartbeat()
            self.check_flags()
            pygame.display.flip()

    def check_flags(self):
        while self.paused:
            self.handle_pgevents(pygame.event.get(), paused=True)
            self.clock.tick(self.framerate)
        if self.new_life:
            self.life_start()
        elif self.new_floor:
            self.floor_start()
        elif self.floor_fin:
            self.floor_end()
        elif self.player.is_dead():
            self.life_end()

    def floor_end(self):
        # in seconds
        self.end_time = time.monotonic()
        completion_time = self.end_time - self.start_time
        end_duration = 0
        self.render_all()
        self.renderer.fade(self.root_display, out=True)
        while end_duration < 800:
            self.renderer.render_floor_end(end_duration,
                                           self.wolfmap, completion_time, self.root_display)
            end_duration += 1
            self.clock.tick(self.framerate)
        # check for the tile player is on,
        # if it is 107, go to the secret level
        # the shareware version checks if the player block x is 10
        pblock = self.player.get_current_block()
        pcell = self.player.get_current_cell()
        if pblock[0] == 10 or pcell == self.SECRET_TILE:
            self.wolfmap = self.episode[-1]
        else:
            self.wolfmap = self.wolfmap.nextmap
        self.player.has_gold_key = False
        self.player.has_silver_key = False

        self.floor_fin = False
        self.new_floor = True
        time.sleep(self.wait_between_states)

    def floor_start(self):
        time.sleep(self.wait_between_states)
        self.init_map()
        self.new_floor = False
        self.render_all()
        self.renderer.fade(self.root_display)
        self.start_timer()

    def life_end(self):
        self.player.excited_to_kill_nazis = False
        self.sound_manager.stop_music()
        self.player.lives -= 1
        self.renderer.update_hud(self.player)
        self.render_all()
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
        self.wolfmap.reset()
        self.game_renderer.glow = False
        self.new_life = True
        pygame.event.clear()
        self.animations.clear()
        time.sleep(self.wait_between_states)

    def life_start(self):
        time.sleep(self.wait_between_states)
        self.new_life = False
        if self.player.lives == 0:
            return self.game_end()
        self.render_all()
        self.game_renderer.unfizzle(
            self.root_display, update_dest=self.renderer.game_off)
        music = self.get_music()
        self.sound_manager.play_music(
            music, _dir="shareware" if self.episode.shareware else "originals")
        pygame.event.clear()
        self.start_timer()

    def game_end(self, chicken=False):
        beats = 300
        while beats != 0:
            self.renderer.render_gameover(self.root_display, chicken=chicken)
            self.clock.tick(self.framerate)
            beats -= 1
        self.ongoing = False
        self.sound_manager.stop_music()
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
        del self
