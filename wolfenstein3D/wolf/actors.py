

from .assets import *
from raycaster.aux_math import *
from math import pi, atan2
from .game_objects import WolfItem, WolfActorType
import random
from . import wolflogger
import copy


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
        off = 0 if self.spcolumn < 2 else self.actor.move_frames-1
        col = (spps * (self.spcolumn + off))
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
        super().__init__(actor, 2, nextstate=self, lifetime=1000)

    def shapenum(self, _):
        col = self.colnum()
        return col + self.actor.dead_offset


class DyingState(ActorState):
    def __init__(self, actor):
        super().__init__(actor, 2, nextstate=DeadState(actor), lifetime=40)
        self.hb_perframe = self.lifetime // actor.death_frames
        self.heartbeats = 0

    def start(self, gamectx):
        ablock = self.actor.get_current_block()
        if ablock in self.actor.wolfmap.actor_lookup:
            del self.actor.wolfmap.actor_lookup[ablock]
        if snds := self.actor.death_sounds:
            deathsnd: pygame.mixer.Sound = random.choice(snds)
            gamectx.schedule_sound_effect(deathsnd, self.actor.pos, 3)

    def act(self, _):
        self.heartbeats += 1

    def shapenum(self, _):
        col = self.colnum()
        return col + self.heartbeats // self.hb_perframe

    def endcallback(self, game_ctx):
        if self.actor.drop is None:
            return
        game_ctx.map.add_item(self.actor.drop,
                              vec_add(self.actor.pos, (2, 0)))


class HurtState(ActorState):
    def __init__(self, actor):
        super().__init__(actor, 2, nextstate=None, lifetime=20)

    def think(self, game_ctx):
        if type(self.next) is not ChaseState:
            self.next = ChaseState(self.actor, 0, game_ctx)

    def shapenum(self, _):
        col = self.colnum()
        return col + self.actor.hurt_offset


class AttackState(ActorState):
    def __init__(self, actor):
        super().__init__(actor, 3, nextstate=None, lifetime=30)
        self.hb_perframe = self.lifetime // actor.attack_frames
        self.heartbeats = 0
        self.auto = False
        self.exit_auto = None

    def go_auto(self):
        if self.auto:
            return
        self.auto = True
        self.lifetime = 15
        self.before_auto = self.next
        self.next = self

    def quit_auto(self):
        self.auto = False
        self.next = self.before_auto
        self.exit_auto = True

    def set_sprite_offset(self, off):
        self.offset = off

    def shapenum(self, _):
        col = self.colnum()
        return col + (self.heartbeats // self.hb_perframe) + self.auto.real

    def attack(self, game_ctx):
        damage = game_ctx.calculate_damage(self.actor, reduction=0.2)
        game_ctx.dec_player_health(damage)
        if game_ctx.player.is_dead():
            # killed the player
            game_ctx.player_slayer = self.actor

    def try_attacking(self, game_ctx):
        if snd := self.actor.attack_sound:
            game_ctx.schedule_sound_effect(snd, self.actor.pos, 0)
        dist = euclidean_distance(self.actor.pos, game_ctx.player.pos)
        dist //= game_ctx.map.wall_width
        hitprob = int(dist * self.actor.accuracy)
        hitprob = 1 if hitprob == 0 else hitprob
        if random.randint(1, hitprob) in range(1, 3):
            self.attack(game_ctx)

    def act(self, game_ctx):
        if self.heartbeats + 2 == self.lifetime:
            self.try_attacking(game_ctx)
        self.heartbeats = (self.heartbeats + 1) % self.lifetime

    def think(self, game_ctx):
        if not self.auto:
            return
        if not self.actor.sees_player(game_ctx):
            self.quit_auto()

    def endcallback(self, _):
        if self.actor._type == WolfActorType.SCHUTZSTAFFEL:
            diceroll = random.randint(1, 2) == 1
            if diceroll and not self.exit_auto:
                self.go_auto()


class ChaseState(ActorState):
    def __init__(self, actor, walk_cycle, game_ctx):
        super().__init__(actor, 1, self, 20)
        if type(actor) is Shepherd:
            # dogs dont have standing sprites
            self.spcolumn = 0
        self.hb_perframe = self.lifetime // self.actor.move_frames
        self.move_off = walk_cycle
        self.heartbeats = 0
        self.fallback_chains = [[[0, -1], [-1, -1], [-1, 0]],
                                [[1, 0], [1, -1], [0, -1]]]

        self.decide_dir(game_ctx)
        self.committo_dest()

        self.waiting_door = False

    def virtual_block(self, dir_):
        return vec_add(self.actor.get_current_block(), dir_)

    def dir_occupied(self, dir_):
        occp = self.actor.occupied_forthis
        vblock = tuple(self.virtual_block(dir_))
        if all(dir_):
            # diagonal direction
            adj1 = tuple(self.virtual_block([dir_[0], 0]))
            adj2 = tuple(self.virtual_block([0, dir_[1]]))
            return vblock, occp(vblock) or occp(adj1) or occp(adj2)
        return vblock, occp(vblock)

    def valid_dir(self, dir_):
        if not any(vec_add(self.prev_dir, dir_)):
            wolflogger.debug(f"direction {dir_} would reversse prev direction: "
                             f"{self.prev_dir}, not allowed")
            # reverses previous direction
            return False
        else:
            pass
            wolflogger.debug(
                f"direction {dir_} does not reverse direction: {self.prev_dir}")
        m = self.actor.wolfmap
        vblock, occupied = self.dir_occupied(dir_)
        if occupied:
            wolflogger.debug(f"direction {dir_} is occupied.")
            if vblock in m.doors:
                door = m.get_door(vblock)
                if self.actor._type != WolfActorType.DOG:
                    self.open_door(door)
                    return True
                return False
            return False
        return True

    def random_dir_fallback(self):
        random.shuffle(self.fallback_chains)
        for chain in self.fallback_chains:
            for dir_ in chain:
                if self.valid_dir(dir_):
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
        if self.valid_dir(first_try):
            return self.actor.update_dir(first_try)
        # if the fallback delta is not zero
        if any(second_try):
            wolflogger.debug(
                f"tried {first_try}, first fallback: {second_try}")
            if self.valid_dir(second_try):
                return self.actor.update_dir(second_try)

        wolflogger.debug(
            f"third fallback, trying prev dir: {self.prev_dir}")
        # third fallback
        if self.valid_dir(self.prev_dir):
            return self.actor.update_dir(self.prev_dir)

        wolflogger.debug(f"fourth fallback, random chains")
        #  fourth fallback
        if not self.random_dir_fallback():
            wolflogger.debug(
                f"all failed; final fallback, reversing dir: {self.actor.look_dir}")
            self.actor.reverse_dir()

        wolflogger.debug(
            f"actor {self.actor._type}  decided look dir: {self.actor.look_dir}, at pos: {self.actor.pos}")

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
        if self.valid_dir(first_try):
            return self.actor.update_dir(first_try)
        # first fallback
        first_fb = [[first_try[0], 0], [0, first_try[1]]]
        random.shuffle(first_fb)
        for dir_ in first_fb:
            if self.valid_dir(dir_):
                return self.actor.update_dir(dir_)
        # second fallback
        second_fb = [vec_mul(first_fb[0], -1),
                     vec_mul(first_fb[1], -1)]
        for dir_ in second_fb:
            if self.valid_dir(dir_):
                return self.actor.update_dir(dir_)
        # final fallback
        self.actor.reverse_dir()
        wolflogger.debug(
            f"actor {self.actor._type}  \
                decided dodge direction: {self.actor.look_dir}, at pos: {self.actor.pos}")

    def decide_dir(self, game_ctx):
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
        ldir = self.actor.look_dir
        w = self.actor.wolfmap.wall_width
        self.mov_budget = w
        if all(ldir):
            # diagonal movement
            self.mov_budget *= math.sqrt(2)

        self.dest_block = vec_add(
            self.actor.pos, vec_mul(vec_norm(ldir), self.mov_budget))

    def seek_dest(self, game_ctx):
        self.actor.move()
        self.mov_budget = max(self.mov_budget - self.actor.pace, 0)
        if self.mov_budget == 0:
            # clamp to center
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

    def act(self, game_ctx):
        if self.gonna_attack:
            self.actor.interrupt_transition(AttackState(self.actor), game_ctx)
        self.heartbeats = (self.heartbeats + 1) % self.lifetime
        self.move_off = self.heartbeats // self.hb_perframe

        if not self.waiting_door:
            self.seek_dest(game_ctx)


class Actor:
    def __init__(self, wolfmap, _type: WolfActorType, pos, look_dir,
                 sprites: list[Sprite], sprite_layout,
                 death_frames, move_frames, attack_frames, dead_offset, hurt_offset,
                 health=100, drop=None, _range=100, accuracy=1,
                 death_sounds=[], attack_sound=None, alert_sound=None):
        self.wolfmap = wolfmap
        self._type = _type
        self.pos = list(pos)
        self.look_dir = look_dir
        self.left = [-self.look_dir[1], self.look_dir[0]]
        self.state = GuardingState(self)
        self.health = health
        self.drop = drop
        self.range = _range
        self.accuracy = accuracy

        self.sprites = [sprite.copy(self.pos) for sprite in sprites.values()]
        self.sprite_layout = sprite_layout
        self.sprite_per_state = self.sprite_layout[0]
        self.death_frames = death_frames
        self.move_frames = move_frames
        self.attack_frames = attack_frames
        self.dead_offset = dead_offset
        self.hurt_offset = hurt_offset

        self.ticks_since_trans = 0
        self.pace = 0.25
        self.proximity_radius = self.wolfmap.wall_width 
        self.interrupted = False

        self.death_sounds = death_sounds
        self.attack_sound = attack_sound
        self.alert_sound = alert_sound

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
        self.ticks_since_trans = 0
        old = self.state
        state.next = old
        self.state = state
        self.state.start(game_ctx)

    def alert(self, game_ctx):
        if type(self.state) is ChaseState:
            # already chasing
            return
        self.state.next = ChaseState(self, 0, game_ctx)
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

    def occupied_forthis(self, block_pos):
        m = self.wolfmap
        if m.cell_occupied(block_pos):
            return True
        if block_pos in m.actor_lookup:
            return m.actor_lookup[block_pos] != self

    def move(self):
        m = self.wolfmap
        disp = vec_mul(vec_norm(self.look_dir), self.pace)
        new_pos = vec_add(self.pos, disp)
        new_block = m.to_block_pos(*new_pos)
        old = self.get_current_block()
        if old != new_block:
            if old in self.wolfmap.actor_lookup:
                del self.wolfmap.actor_lookup[old]
            self.pos = vec_add(self.pos, disp)
            self.wolfmap.actor_lookup[new_block] = self
        self.pos = vec_add(self.pos, disp)

    def orientation_idx(self, observer, sectors=8):
        myspace = self.to_this_space(observer.pos)
        sx, sy = myspace
        return int((pi/2-atan2(-sy, sx)) // (2*pi / sectors) % sectors)

    def current_sprite(self, observer):
        self.shapenum = self.state.shapenum(observer)
        sprite = self.sprites[self.shapenum]
        sprite.pos = self.pos
        return sprite

    def dec_health(self, damage):
        self.health = max(0, self.health - damage)

    def is_dead(self):
        return self.health == 0

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
        return vec_add(ablock, offset)

    def sees_player(self, game_ctx):
        r = game_ctx.game_renderer.raycaster
        p = game_ctx.player
        to_player = vec_norm(vec_sub(self.pos, p.pos))
        # if vec_dot(self.look_dir, to_player) < 0:
        #     # player is behind the actor
        #     return False
        return p.get_current_block() in r.get_corridor(*to_player, self.pos)

    def hears_player(self, game_ctx):
        actor_area = self.get_current_area()
        if actor_area == 106:
            # in ambush tile
            return False
        can_hear = game_ctx.areabyplayer[actor_area]
        return game_ctx.player.shooting and can_hear

    def snapshot(self):
        state = self.pos, self.look_dir, self.health
        return tuple([copy.deepcopy(att) for att in state])

    def reload_snapshot(self, snapshot):
        self.pos = snapshot[0]
        self.look_dir = snapshot[1]
        self.health = snapshot[2]
        self.state = GuardingState(self)
        self.ticks_since_trans = 0


class Guard(Actor):
    def __init__(self, wolfmap, pos, look_dir):
        super().__init__(wolfmap, WolfActorType.GUARD, pos, look_dir,
                         sprites=SPRITES["characters"]["guard"],
                         sprite_layout=(8, 7),
                         death_frames=5,
                         move_frames=4,
                         attack_frames=3,
                         dead_offset=4,
                         hurt_offset=7,
                         health=100,
                         drop=WolfItem.AMMUNITION,
                         death_sounds=list(SOUNDS["death"].values()),
                         attack_sound=SOUNDS["common"]["NAZIFIRESND.WAV"],
                         alert_sound=SOUNDS["common"]["HALTSND.WAV"])
        self.pace = 0.15


class Shepherd(Actor):
    def __init__(self, wolfmap, pos, look_dir):
        super().__init__(wolfmap, WolfActorType.DOG, pos, look_dir,
                         sprites=SPRITES["characters"]["shepherd"],
                         sprite_layout=(8, 6),
                         death_frames=3,
                         move_frames=3,
                         attack_frames=3,
                         dead_offset=3,
                         hurt_offset=0,
                         health=60,
                         _range=(wolfmap.wall_width)*2,
                         attack_sound=SOUNDS["dogs"]["DOGATTACKSND.WAV"])
        self.pace = 0.5


class SS(Actor):
    def __init__(self, wolfmap, pos, look_dir):
        super().__init__(wolfmap, WolfActorType.SCHUTZSTAFFEL, pos, look_dir,
                         sprites=SPRITES["characters"]["SS"],
                         sprite_layout=(8, 7),
                         death_frames=5,
                         move_frames=4,
                         attack_frames=3,
                         dead_offset=5,
                         hurt_offset=0,
                         health=120,
                         drop=WolfItem.MACHINEGUN,
                         death_sounds=list(SOUNDS["death"].values()))


TYPE_ACTOR_OBJ = {
    WolfActorType.GUARD: Guard,
    WolfActorType.DOG: Shepherd,
    WolfActorType.SCHUTZSTAFFEL: SS,
}
