

from wolfenstein3D.wolf.assets import ASSET_MANAGER, Sprite
from wolfenstein3D.raycaster.aux_math import *
from wolfenstein3D.wolf.game_objects import WolfItem, WolfActorType
from wolfenstein3D.wolf import pygame, wolflogger

from math import pi, atan2
import copy
import random
from dataclasses import dataclass
from typing import Callable, Optional


class ActorState:
    def __init__(self, actor, spcolumn, nextstate, lifetime):
        self.actor = actor
        self.spcolumn = spcolumn
        self.next = nextstate
        self.lifetime = lifetime

    def think(self, game_ctx):
        return

    def act(self, game_ctx):
        return

    def colnum(self):
        spps = self.actor.sprite_per_state
        col_off = 0 if self.spcolumn < 2 else self.actor.move_frames - 1
        col = (spps * (self.spcolumn + col_off))
        return col

    def start(self, game_ctx):
        return

    def endcallback(self, game_ctx):
        return


class GuardingState(ActorState):
    def __init__(self, actor):
        super().__init__(actor, 0, nextstate=self, lifetime=10)
        self.alerted = False

    def think(self, game_ctx):
        if self.alerted:
            # already alerted nothing to think
            return
        dist = euclidean_distance(self.actor.pos, game_ctx.player.pos)
        if self.actor.hears_player(game_ctx):
            self.actor.alert(game_ctx)
            self.alerted = True
        elif self.actor.sees_player(game_ctx):
            self.actor.alert(game_ctx)
            self.alerted = True
        elif dist < self.actor.proximity_radius:
            self.actor.alert(game_ctx)
            self.alerted = True
        # continue to guard

    def shapenum(self, observer):
        col = self.colnum()
        spps = self.actor.sprite_per_state
        ori = self.actor.orientation_idx(observer, sectors=spps)
        return col + ori


class DeadState(ActorState):
    def __init__(self, actor):
        super().__init__(actor, 2, nextstate=self, lifetime=5000)

    def shapenum(self, _):
        col = self.colnum()
        return col + self.actor.dead_offset


class DyingState(ActorState):
    def __init__(self, actor, frame_lifetime=12):
        if actor.type == WolfActorType.DOG:
            frame_lifetime += 3
        lifetime = frame_lifetime * actor.death_frames

        super().__init__(actor, 2, nextstate=DeadState(actor), lifetime=lifetime)
        self.hb_perframe = self.lifetime // actor.death_frames
        self.heartbeats = 0

    def start(self, gamectx):
        if snds := self.actor.death_sounds:
            deathsnd: pygame.mixer.Sound = random.choice(snds)
            gamectx.schedule_sound_effect(deathsnd, self.actor.pos, 3)

    def act(self, _):
        self.heartbeats += 1

    def shapenum(self, _):
        col = self.colnum()
        return col + self.heartbeats // self.hb_perframe

    def endcallback(self, game_ctx):
        game_ctx.player.score += 100
        self.actor.flush_occupancy()
        self.actor.drop_item()


class HurtState(ActorState):
    def __init__(self, actor):
        super().__init__(actor, 2, nextstate=None, lifetime=20)
        if self.actor.type == WolfActorType.SCHUTZSTAFFEL:
            self.lifetime = 10
        elif self.actor.type == WolfActorType.HANS:
            self.lifetime = 1

    def think(self, game_ctx):
        if type(self.next) is not ChaseState:
            if self.actor.chase is None:
                # shot before alerted
                self.next = ChaseState(self.actor, 0, game_ctx)
            else:
                self.next = self.actor.chase 

    def shapenum(self, _):
        col = self.colnum()
        return col + self.actor.hurt_offset


class AttackState(ActorState):
    def __init__(self, actor, frame_lifetime=12):
        self.frame_lifetime = frame_lifetime
        lifetime = frame_lifetime * actor.attack_frames
        super().__init__(actor, 3, nextstate=None, lifetime=lifetime)
        self.hb_perframe = self.lifetime // actor.attack_frames
        self.heartbeats = 0
        self.auto = False
        self.exit_auto = None

    def go_auto(self):
        if self.auto:
            return
        self.auto = True
        self.lifetime = 20
        self.before_auto = self.next
        self.next = self

    def quit_auto(self):
        self.auto = False
        self.next = self.before_auto
        self.exit_auto = True

    def shapenum(self, _):
        col = self.colnum()
        return col + (self.heartbeats // self.hb_perframe) + self.auto.real

    def attack(self, game_ctx):
        callback = getattr(self.actor, "attack_callback", None)
        if callable(callback):
            return callback(self.actor, game_ctx)

        damage = game_ctx.calc_actor_dmg(self.actor)
        game_ctx.hurt_player(damage)
        if game_ctx.player.is_dead():
            # killed the player
            game_ctx.player_slayer = self.actor

    def try_attacking(self, game_ctx):
        if snd := self.actor.attack_sound:
            game_ctx.schedule_sound_effect(snd, self.actor.pos, 0)
        dist = euclidean_distance(self.actor.pos, game_ctx.player.pos)
        dist //= game_ctx.wolfmap.wall_width
        hitprob = int(dist)
        hitprob = 1 if hitprob == 0 else hitprob
        if self.actor.type is WolfActorType.FAKEHITLER:
            if self.actor.sees_player(game_ctx):
                self.attack(game_ctx)
        elif random.randint(1, hitprob) in range(1, 3):
            if self.actor.sees_player(game_ctx):
                self.attack(game_ctx)

    def act(self, game_ctx):
        if self.heartbeats + 2 == self.lifetime:
            self.try_attacking(game_ctx)
        elif self.heartbeats == self.frame_lifetime \
                and self.actor.type is WolfActorType.MUTANT:
            # mutants attack twice
            self.try_attacking(game_ctx)
        self.heartbeats = (self.heartbeats + 1) % self.lifetime

    def think(self, game_ctx):
        if not self.auto:
            return
        if not self.actor.sees_player(game_ctx):
            self.quit_auto()

    def endcallback(self, _):
        if self.actor.type in [WolfActorType.SCHUTZSTAFFEL, WolfActorType.HANS]:
            diceroll = random.randint(1, 3) in [1, 2]
            if diceroll and not self.exit_auto:
                self.go_auto()


class ChaseState(ActorState):
    def __init__(self, actor, walk_cycle, game_ctx):
        super().__init__(actor, 1, self, 40)

        if self.actor.type is WolfActorType.DOG:
            # dogs and hans dont have standing sprites
            self.spcolumn = 0

        self.hb_perframe = self.lifetime // self.actor.move_frames

        self.move_off = walk_cycle
        self.heartbeats = 0
        self.fallback_chains = [[[0, -1], [-1, -1], [-1, 0]],
                                [[1, 0], [1, -1], [0, -1]]]

        self.decide_dir(game_ctx)
        self.dest_block = None
        self.mov_budget = 0
        self.committo_dest()

        self.waiting_door = False
        self.stuck = False

    def valid_dir(self, dir_, game_ctx):
        if not any(vec_add(self.prev_dir, dir_)):
            wolflogger.debug(f"direction {dir_} would reverse prev direction: "
                             f"{self.prev_dir}, not allowed")
            # reverses previous direction
            return False
        else:
            pass
            wolflogger.debug(
                f"direction {dir_} does not reverse direction: {self.prev_dir}")
        m = self.actor.wolfmap
        vblock, occupied = self.actor.dir_occupied(dir_, game_ctx)
        if occupied:
            wolflogger.debug(f"direction {dir_} is occupied.")
            # if not moving diagonally, open doors
            if vblock in m.doors and not all(dir_):
                if self.actor.occupied_by_other(vblock):
                    return False
                door = m.get_door(vblock)
                if self.actor.type != WolfActorType.DOG:
                    self.open_door(door)
                    return True
                return False
            return False
        return True

    def random_dir_fallback(self, game_ctx):
        random.shuffle(self.fallback_chains)
        for chain in self.fallback_chains:
            for dir_ in chain:
                if self.valid_dir(dir_, game_ctx):
                    self.actor.update_dir(list(dir_))
                    return True
        return False

    def find_cardinals(self, game_ctx):
        delta = vec_sub(self.actor.pos, game_ctx.player.pos)
        maxd = max(delta, key=abs)
        vertical = delta.index(maxd)
        mind = delta[~vertical + 2]
        dirs = [[1, 0], [0, 1]]
        return vec_mul(dirs[vertical], sign(maxd)), \
            vec_mul(dirs[~vertical + 2], sign(mind))

    def decide_chase_dir(self, game_ctx):
        wolflogger.debug("decide chase dir called")
        self.prev_dir = self.actor.look_dir.copy()
        first_try, second_try = self.find_cardinals(game_ctx)
        if self.valid_dir(first_try, game_ctx):
            return self.actor.update_dir(first_try)
        # if the fallback delta is not zero
        if any(second_try):
            wolflogger.debug(
                f"tried {first_try}, first fallback: {second_try}")
            if self.valid_dir(second_try, game_ctx):
                return self.actor.update_dir(second_try)

        wolflogger.debug(
            f"third fallback, trying prev dir: {self.prev_dir}")
        # third fallback
        if self.valid_dir(self.prev_dir, game_ctx):
            return self.actor.update_dir(self.prev_dir)

        wolflogger.debug(f"fourth fallback, random chains")
        #  fourth fallback
        if not self.random_dir_fallback(game_ctx):
            wolflogger.debug(
                f"all failed; final fallback, reversing dir: {self.actor.look_dir}")
            self.actor.reverse_dir()
            if not self.valid_dir(self.actor.look_dir, game_ctx):
                self.stuck = True

        wolflogger.debug(
            f"actor {self.actor.type}  decided look dir: {self.actor.look_dir}, at pos: {self.actor.pos}")

    def decide_dodge_dir(self, game_ctx):
        wolflogger.debug("decide dodge dir called")
        self.prev_dir = self.actor.look_dir.copy()
        delx, dely = vec_sub(self.actor.pos, game_ctx.player.pos)
        # if the deltas are 0, prefer NE
        # like the original
        delx = -1 if delx == 0 else delx
        dely = -1 if dely == 0 else dely
        #
        first_try = [int(delx // abs(delx)), int(dely // abs(dely))]
        if self.valid_dir(first_try, game_ctx):
            return self.actor.update_dir(first_try)
        # first fallback
        first_fb = [[first_try[0], 0], [0, first_try[1]]]
        random.shuffle(first_fb)
        for dir_ in first_fb:
            if self.valid_dir(dir_, game_ctx):
                return self.actor.update_dir(dir_)
        # second fallback
        second_fb = [vec_mul(first_fb[0], -1),
                     vec_mul(first_fb[1], -1)]
        for dir_ in second_fb:
            if self.valid_dir(dir_, game_ctx):
                return self.actor.update_dir(dir_)
        # final fallback
        self.actor.reverse_dir()
        if not self.valid_dir(self.actor.look_dir, game_ctx):
            self.stuck = True
        wolflogger.debug(
            f"actor {self.actor.type}  \
                decided dodge direction: {self.actor.look_dir}, at pos: {self.actor.pos}")

    def decide_dir(self, game_ctx):
        self.stuck = False
        if self.actor.sees_player(game_ctx):
            self.decide_dodge_dir(game_ctx)
        else:
            self.decide_chase_dir(game_ctx)

    def open_door(self, door):
        self.waiting_door = door
        if not (door.is_opening or door.is_open()):
            wolflogger.debug(f"{self.actor}, openned door!")
            door.begin_opening()

    def committo_dest(self):
        if self.stuck:
            self.dest_block = None
            return
        if self.dest_block:
            self.actor.unoccupy_block(
                self.actor.wolfmap.to_block_pos(*self.dest_block))
        ldir = self.actor.look_dir
        w = self.actor.wolfmap.wall_width
        self.mov_budget = w
        if all(ldir):
            # diagonal movement
            self.mov_budget *= math.sqrt(2)

        self.dest_block = vec_add(
            self.actor.pos, vec_mul(vec_norm(ldir), self.mov_budget))
        self.actor.occupy_block(
            self.actor.wolfmap.to_block_pos(*self.dest_block))

    def seek_dest(self):
        if not self.stuck:
            self.actor.move()

        self.mov_budget = max(self.mov_budget - self.actor.pace, 0)

    def budget_end(self, game_ctx):
        # clamp to center
        if not self.stuck:
            if self.dest_block is not None:
                self.actor.pos = self.dest_block
        #
        self.decide_dir(game_ctx)
        self.committo_dest()

    def colnum(self):
        return super().colnum() + \
            self.move_off*self.actor.sprite_per_state

    def shapenum(self, observer):
        spps = self.actor.sprite_per_state
        col = self.colnum()
        ori = self.actor.orientation_idx(observer, sectors=spps)
        return col + ori

    def think(self, game_ctx):
        dist = euclidean_distance(self.actor.pos, game_ctx.player.pos)
        dist = 1 if dist < 1 else dist
        diceroll = random.randint(1, int(dist)) == 1
        self.gonna_attack = diceroll and dist < self.actor.range \
            and self.actor.sees_player(game_ctx)
        if self.waiting_door:
            if self.waiting_door.is_open():
                self.waiting_door = False
        if self.mov_budget == 0:
            self.budget_end(game_ctx)

    def act(self, game_ctx):
        if self.gonna_attack:
            self.actor.interrupt_transition(AttackState(self.actor), game_ctx)
        self.heartbeats = (self.heartbeats + 1) % self.lifetime
        self.move_off = self.heartbeats // self.hb_perframe

        if not self.waiting_door:
            self.seek_dest()


class PatrolState(ChaseState):
    PATROL_DIR = {
        90: [1,  0],
        91: [1, -1],
        92: [0, -1],
        93: [-1, -1],
        94: [-1,  0],
        95: [-1,  1],
        96: [0,  1],
        97: [1,  1],
    }

    def __init__(self, actor, map_ctx):
        super().__init__(actor, 0, map_ctx)
        self.alerted = False
        self.gonna_alert = False

    def decide_dir(self, map_ctx):
        ablock = self.actor.get_current_block()
        if ablock not in map_ctx.patrol_lookup:
            return
        patrol = map_ctx.patrol_lookup[ablock]
        self.actor.update_dir(self.PATROL_DIR[patrol].copy())
        wolflogger.debug(
            f"actor {self.actor.type}\
                decided patrol direction: {self.actor.look_dir}, at pos: {ablock}")

    def committo_dest(self):
        ldir = self.actor.look_dir
        w = self.actor.wolfmap.wall_width
        self.mov_budget = w
        if all(ldir):
            # diagonal movement
            self.mov_budget *= math.sqrt(2)

        self.dest_block = vec_add(
            self.actor.pos, vec_mul(vec_norm(ldir), self.mov_budget))

    def think(self, game_ctx):
        if not self.alerted:
            if self.actor.hears_player(game_ctx):
                self.alerted = True
            elif self.actor.sees_player(game_ctx):
                self.alerted = True
        if self.waiting_door:
            if self.waiting_door.is_open():
                self.waiting_door = False
        # continue to patrol

    def seek_dest(self):
        self.actor.move()
        self.mov_budget = max(self.mov_budget - self.actor.pace, 0)

    def budget_end(self, game_ctx):
        # clamp to center
        self.actor.pos = self.dest_block
        #
        if self.alerted:
            self.actor.transition(ChaseState(
                self.actor, 0, game_ctx), game_ctx)
            return
        fblock = self.actor.get_front_block()
        if fblock in game_ctx.wolfmap.doors:
            door = game_ctx.wolfmap.doors[fblock]
            self.open_door(door)
        self.decide_dir(game_ctx.wolfmap)
        self.committo_dest()

    def act(self, game_ctx):
        self.heartbeats = (self.heartbeats + 1) % self.lifetime
        self.move_off = self.heartbeats // self.hb_perframe
        if not self.waiting_door:
            self.seek_dest()
        if self.mov_budget == 0:
            self.budget_end(game_ctx)

# the prototype actor class
# its specifics get built by its builder class


class Actor:
    def __init__(self, wolfmap, _type: WolfActorType, pos, look_dir, patrol=False):
        self.wolfmap = wolfmap
        self.type = _type
        self.pos = list(pos)
        self.occupancy = set()
        self.look_dir = look_dir
        self.left = [-self.look_dir[1], self.look_dir[0]]
        self.ticks_since_trans = 0
        self.proximity_radius = self.wolfmap.wall_width
        self.interrupted = False
        self.patrol = patrol

        self.current_sp = None
        
        self.chase = None

    def tick(self, game_ctx, heartbeats):
        self.ticks_since_trans += heartbeats
        if self.ticks_since_trans >= self.state.lifetime:
            self.timeout_transition(game_ctx)
        self.state.think(game_ctx)
        self.state.act(game_ctx)

    def timeout_transition(self, game_ctx):
        self.state.endcallback(game_ctx)
        self.state = self.state.next
        # if the state was interrupted, restore old ticks
        if self.interrupted:
            self.ticks_since_trans = getattr(self.state, "heartbeats", 0)
        else:
            self.ticks_since_trans = 0
        self.state.start(game_ctx)

    def interrupt_transition(self, state: ActorState, game_ctx):
        self.interrupted = True
        old = self.state
        state.next = old
        self.transition(state, game_ctx)

    def transition(self, state, game_ctx):
        self.ticks_since_trans = 0
        self.state = state
        self.state.start(game_ctx)

    def alert(self, game_ctx):
        if type(self.state) is ChaseState:
            # already chasing
            return
        self.chase = ChaseState(self, 0, game_ctx)
        self.state.next = self.chase
        if alrtsnd := self.alert_sound:
            game_ctx.schedule_sound_effect(alrtsnd, origin=self.pos, _time=1)

    def to_this_space(self, pos):
        to_self = vec_sub(pos, self.pos)
        obs_space = (vec_dot(to_self, self.left),
                     vec_dot(to_self, self.look_dir))
        return obs_space

    def get_current_block(self):
        return self.wolfmap.to_block_pos(*self.pos)

    def get_current_area(self):
        ablock = self.get_current_block()
        if not self.wolfmap.in_boundary(ablock):
            return 106
        cell = self.wolfmap.raw[ablock[1]][ablock[0]]
        if cell in self.wolfmap.DOOR_INDICES:
            # if inside door tile, return the second area
            return self.wolfmap.get_door(ablock).area1
        return cell - 107

    def update_dir(self, dir_):
        self.look_dir = dir_
        self.left = [-self.look_dir[1], self.look_dir[0]]

    def reverse_dir(self):
        self.look_dir = vec_mul(self.look_dir, -1)
        self.left = [-self.look_dir[1], self.look_dir[0]]

    def occupied_by_other(self, block_pos):
        m = self.wolfmap
        if block_pos in m.actor_lookup:
            return m.actor_lookup[block_pos] != self
        return False

    def occupied_forthis(self, block_pos, game_ctx):
        m = self.wolfmap
        if m.cell_occupied(block_pos):
            return True
        return self.occupied_by_other(block_pos) \
            or block_pos == game_ctx.player.get_current_block()

    def occupy_block(self, block_pos):
        bpos = tuple(block_pos)
        self.occupancy.add(bpos)
        if bpos in self.wolfmap.actor_lookup:
            return
        self.wolfmap.actor_lookup[bpos] = self

    def unoccupy_block(self, block_pos):
        bpos = tuple(block_pos)
        if bpos in self.occupancy:
            self.occupancy.remove(bpos)
        if bpos in self.wolfmap.actor_lookup:
            del self.wolfmap.actor_lookup[bpos]

    def flush_occupancy(self):
        mirror = self.occupancy.copy()
        for bpos in mirror:
            if bpos not in self.wolfmap.actor_lookup:
                return
            self.unoccupy_block(bpos)

    def move(self):
        m = self.wolfmap
        disp = vec_mul(vec_norm(self.look_dir), self.pace)
        new_pos = vec_add(self.pos, disp)
        new_block = m.to_block_pos(*new_pos)
        old = self.get_current_block()
        self.pos = vec_add(self.pos, disp)
        if old != new_block:
            self.unoccupy_block(old)
            self.occupy_block(new_block)

    def orientation_idx(self, observer, sectors=8):
        myspace = self.to_this_space(observer.pos)
        sx, sy = myspace
        return int((pi/2-atan2(-sy, sx)) // (2*pi / sectors) % sectors)

    def current_sprite(self, observer):
        self.shapenum = self.state.shapenum(observer)
        self.current_sp = self.sprites[self.shapenum]
        self.current_sp.pos = self.pos
        return self.current_sp

    def hitpos(self, sw):
        return self.current_sp.screen_pos - sw // 2

    def dec_health(self, damage):
        self.health = max(0, self.health - damage)

    def is_dead(self):
        return self.health == 0

    def drop_item(self):
        rp = self.wolfmap.to_real_pos
        if self.drop is None:
            return
        dblock = self.wolfmap.to_block_pos(*vec_add(self.pos, (2, 0)))
        if dblock not in self.wolfmap.item_lookup:
            return self.wolfmap.add_item(self.drop, vec_add(self.pos, (2, 0)))
        # the drop block has another item
        for adj in ADJACENT_MATRIX:
            dblock = tuple(vec_add(dblock, adj))
            if dblock not in self.wolfmap.item_lookup:
                return self.wolfmap.add_item(self.drop, rp(*dblock))
        # all drop blocks occupied, there is nothing we can do

    def get_shot(self, damage, game_ctx):
        self.dec_health(damage)
        dead = self.is_dead()
        if dead:
            self.state = DeadState(self)
        newst = DyingState(self) if dead else HurtState(self)
        self.interrupt_transition(newst, game_ctx)

    def get_front_block(self):
        ablock = self.wolfmap.to_block_pos(*self.pos)
        offset = [0, 0]
        mag = max(self.look_dir, key=abs)
        vertical = self.look_dir.index(mag)
        offset[vertical] += sign(mag)
        return tuple(vec_add(ablock, offset))

    def virtual_block(self, dir_):
        return vec_add(self.get_current_block(), dir_)

    def dir_occupied(self, dir_, game_ctx):
        occp = self.occupied_forthis
        vblock = tuple(self.virtual_block(dir_))
        if all(dir_):
            # diagonal direction
            adj1 = tuple(self.virtual_block([dir_[0], 0]))
            adj2 = tuple(self.virtual_block([0, dir_[1]]))
            return vblock, occp(vblock, game_ctx) or occp(adj1, game_ctx) or occp(adj2, game_ctx)
        return vblock, occp(vblock, game_ctx)

    def sees_player(self, game_ctx):
        r = game_ctx.game_renderer.raycaster
        p = game_ctx.player
        to_player = vec_norm(vec_sub(self.pos, p.pos))
        # if vec_dot(self.look_dir, to_player) < 0:
        #     # player is behind the actor
        #     return False
        return p.get_current_block() in r.get_corridor(to_player, self.pos)

    def hears_player(self, game_ctx):
        actor_area = self.get_current_area()
        if actor_area == 106:
            # in ambush tile
            return False
        try:
            can_hear = game_ctx.areabyplayer[actor_area]
        except IndexError:
            return False
        return game_ctx.player.shooting and can_hear

    def snapshot(self):
        state = self.pos, self.look_dir, self.health
        return tuple([copy.deepcopy(att) for att in state])

    def reload_snapshot(self, snapshot, map_ctx):
        self.pos = snapshot[0]
        self.look_dir = snapshot[1]
        self.health = snapshot[2]
        self.state = GuardingState(
            self) if not self.patrol else PatrolState(self, map_ctx)
        self.ticks_since_trans = 0

    def throw_projectile(self, speed, sprites, game_ctx):
        pj_dir = vec_norm(vec_sub(self.pos, game_ctx.player.pos))
        game_ctx.spawn_projectile(pj_dir, speed, self.pos, sprites)


@dataclass
class ActorRecipe:
    sprites: dict
    sprite_layout: list
    death_frames: int
    move_frames: int
    attack_frames: int
    dead_offset: int
    hurt_offset: int

    death_sounds: list[pygame.mixer.Sound]
    attack_sound: pygame.mixer.Sound
    alert_sound: pygame.mixer.Sound

    health: int
    range_: int
    accuracy: float
    drop: WolfItem
    pace: float

    no_orientation: bool = False

    attack_callback: Optional[Callable[[], None]] = None


SOUNDS = ASSET_MANAGER.sounds
SPRITES = ASSET_MANAGER.sprites


def pacman_ghost_recipe(gn): return ActorRecipe(
    sprites=SPRITES["characters"][gn],
    sprite_layout=(2, 5),
    death_frames=5,
    move_frames=2,
    attack_frames=1,
    dead_offset=0,
    hurt_offset=0,
    death_sounds=list(SOUNDS["death"].values()),
    attack_sound=None,
    alert_sound=None,
    health=1000000000000,
    range_=8,
    accuracy=1,
    drop=WolfItem.EXTRALIFE,
    pace=0.2,
    no_orientation=True
)


ACTOR_RECIPES = {
    WolfActorType.GUARD: ActorRecipe(
        sprites=SPRITES["characters"]["guard"],
        sprite_layout=(8, 7),
        death_frames=5,
        move_frames=4,
        attack_frames=3,
        dead_offset=4,
        hurt_offset=7,
        death_sounds=list(SOUNDS["death"].values()),
        attack_sound=SOUNDS["fire"]["NAZIFIRESND.WAV"],
        alert_sound=SOUNDS["alert"]["HALTSND.WAV"],
        health=25,
        range_=200,
        accuracy=1,
        drop=WolfItem.AMMUNITION,
        pace=0.2
    ),
    WolfActorType.DOG: ActorRecipe(
        sprites=SPRITES["characters"]["shepherd"],
        sprite_layout=(8, 6),
        death_frames=3,
        move_frames=3,
        attack_frames=3,
        dead_offset=3,
        hurt_offset=0,
        death_sounds=[SOUNDS["dogs"]["DOGDEATHSND.WAV"],],
        attack_sound=SOUNDS["dogs"]["DOGATTACKSND.WAV"],
        alert_sound=SOUNDS["dogs"]["DOGBARKSND.WAV"],
        health=1,
        range_=8,
        accuracy=1,
        drop=None,
        pace=0.4
    ),


    WolfActorType.SCHUTZSTAFFEL: ActorRecipe(
        sprites=SPRITES["characters"]["SS"],
        sprite_layout=(8, 7),
        death_frames=5,
        move_frames=4,
        attack_frames=3,
        dead_offset=5,
        hurt_offset=1,
        death_sounds=[SOUNDS["death"]["DEATHSCREAM6SND.WAV"],
                      SOUNDS["common"]["LEBENSND.WAV"]],
        attack_sound=SOUNDS["fire"]["SSFIRESND.WAV"],
        alert_sound=SOUNDS["alert"]["SCHUTZADSND.WAV"],
        health=100,
        range_=50,
        accuracy=1,
        drop=WolfItem.MACHINEGUN,
        pace=0.15
    ),


    WolfActorType.OFFICER: ActorRecipe(
        sprites=SPRITES["characters"]["officer"],
        sprite_layout=(8, 7),
        death_frames=6,
        move_frames=4,
        attack_frames=3,
        dead_offset=6,
        hurt_offset=1,
        death_sounds=[SOUNDS["common"]["NEINSOVASSND.WAV"],],
        attack_sound=SOUNDS["fire"]["NAZIFIRESND.WAV"],
        alert_sound=SOUNDS["alert"]["SPIONSND.WAV"],
        health=50,
        range_=200,
        accuracy=1,
        drop=WolfItem.AMMUNITION,
        pace=0.3
    ),

    WolfActorType.MUTANT: ActorRecipe(
        sprites=SPRITES["characters"]["mutant"],
        sprite_layout=(8, 7),
        death_frames=6,
        move_frames=4,
        attack_frames=4,
        dead_offset=6,
        hurt_offset=0,
        death_sounds=[SOUNDS["common"]["AHHHGSND.WAV"]],
        attack_sound=SOUNDS["fire"]["NAZIFIRESND.WAV"],
        alert_sound=None,
        health=45,
        range_=150,
        accuracy=1,
        drop=WolfItem.AMMUNITION,
        pace=0.35
    ),

    WolfActorType.FAKEHITLER: ActorRecipe(
        sprites=SPRITES["characters"]["fakehitler"],
        sprite_layout=(6, 6),
        death_frames=6,
        move_frames=3,
        attack_frames=2,
        dead_offset=5,
        hurt_offset=0,
        death_sounds=[SOUNDS["common"]["HITLERHASND.WAV"]],
        attack_sound=None,
        alert_sound=SOUNDS["alert"]["TOT_HUNDSND.WAV"],
        health=15,
        range_=300,
        accuracy=1,
        drop=None,
        pace=0.35,
        no_orientation=True,
        attack_callback=lambda self, game_ctx: self.throw_projectile(
            0.5, SPRITES["projectiles"]["fireballs"], game_ctx)
    ),

    WolfActorType.HANS: ActorRecipe(
        sprites=SPRITES["characters"]["boss"]["hans"],
        sprite_layout=(4, 7),
        death_frames=4,
        move_frames=4,
        attack_frames=3,
        dead_offset=3,
        hurt_offset=0,
        death_sounds=[SOUNDS["hans"]["MUTTISND.WAV"]],
        attack_sound=SOUNDS["boss"]["BOSSFIRESND.WAV"],
        alert_sound=SOUNDS["hans"]["GUTENTAGSND.WAV"],
        health=1200,
        range_=150,
        accuracy=1,
        drop=WolfItem.GOLDKEY,
        pace=0.15,
        no_orientation=True
    ),

    WolfActorType.BLINKY: pacman_ghost_recipe("blinky"),
    WolfActorType.PINKY: pacman_ghost_recipe("pinky"),
    WolfActorType.INKY: pacman_ghost_recipe("inky"),
    WolfActorType.CLYDE: pacman_ghost_recipe("clyde"),

}


class ActorBuilder:
    def __init__(self, wolfmap, _type: WolfActorType, pos, look_dir, patrol=False):
        self.actor = Actor(wolfmap, _type, pos, look_dir, patrol)

    def build_sprites(self, sprites: list, sprite_layout):
        self.actor.sprites = []
        for i in range(sprite_layout[0]*sprite_layout[1]):
            sp = sprites.get(i, None)
            if sp is not None:
                self.actor.sprites.append(sp.copy(self.actor.pos))
            else:
                self.actor.sprites.append(None)
        self.actor.sprite_per_state = sprite_layout[0]

    def build_frame_count(self, death: int, move: int, attack: int):
        self.actor.death_frames = death
        self.actor.move_frames = move
        self.actor.attack_frames = attack

    def build_sprite_offsets(self, dead_offset, hurt_offset):
        self.actor.dead_offset = dead_offset
        self.actor.hurt_offset = hurt_offset

    def build_moving_sprites(self):
        pass

    def build_standing_sprites(self):
        pass

    def build_sounds(self, death_sounds, attack_sound, alert_sound):
        self.actor.death_sounds = death_sounds
        self.actor.attack_sound = attack_sound
        self.actor.alert_sound = alert_sound

    def build_characteristics(self, health: int, _range: int,
                              accuracy, drop: WolfItem, pace: float):
        self.actor.health = health
        self.actor.range = _range
        self.actor.accuracy = accuracy
        self.actor.drop = drop
        self.actor.pace = pace

    def build_state(self):
        state = GuardingState(
            self.actor) if not self.actor.patrol else PatrolState(self.actor, self.actor.wolfmap)
        self.actor.state = state

    def build(self, recipe: ActorRecipe) -> Actor:
        self.build_sprites(recipe.sprites, recipe.sprite_layout)
        self.build_frame_count(recipe.death_frames,
                               recipe.move_frames, recipe.attack_frames)
        self.build_sprite_offsets(recipe.dead_offset, recipe.hurt_offset)
        self.build_sounds(recipe.death_sounds,
                          recipe.attack_sound, recipe.alert_sound)
        self.build_characteristics(
            recipe.health, recipe.range_, recipe.accuracy,
            recipe.drop, recipe.pace)

        self.build_state()

        if recipe.no_orientation:
            self.actor.orientation_idx = lambda *_, **__: 0
        if recipe.attack_callback:
            self.actor.attack_callback = recipe.attack_callback
        return self.actor
