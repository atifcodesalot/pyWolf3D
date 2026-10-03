

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

    def endcallback(self, game_ctx):
        return


class GuardingState(ActorState):
    def __init__(self, actor):
        super().__init__(actor, 0, nextstate=self, lifetime=10)

    def think(self, game_ctx):
        dist = euclidean_distance(self.actor.pos, game_ctx.player.pos)
        if dist < self.actor.proximity_radius:
            if self.actor._type == WolfActorType.DOG:
                self.next = ChaseState(self.actor, 0, game_ctx)
            elif self.actor.sees_player(game_ctx):
                self.next = ChaseState(self.actor, 0, game_ctx)

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
        self.inflicted_damage = False

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
    
    def go_auto(self):
        self.auto = True
        self.lifetime = 20
        self.next = self
            
    def set_sprite_offset(self, off):
        self.offset = off

    def shapenum(self, _):
        col = self.colnum()
        return col + (self.heartbeats // self.hb_perframe) + self.auto.real

    def attack(self, game_ctx):
        damage = game_ctx.calculate_damage(self.actor, reduction=0.4)
        game_ctx.dec_player_health(damage)
        if game_ctx.player.is_dead():
            # killed the player
            game_ctx.player_slayer = self.actor

    def try_attacking(self, game_ctx):
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
        
    def endcallback(self, _):
        if self.actor._type == WolfActorType.SCHUTZSTAFFEL:
            diceroll = random.randint(1, 2) == 2
            if diceroll:
                self.go_auto()

class ChaseState(ActorState):
    def __init__(self, actor, walk_cycle, game_ctx):
        super().__init__(actor, 1, self, 16)
        if type(actor) is Shepherd:
            # dogs dont have standing sprites
            self.spcolumn = 0
        self.hb_perframe = self.lifetime // self.actor.move_frames
        self.move_off = walk_cycle
        self.heartbeats = 0
        self.prev_dir = [0, 0]
        self.decide_dir(game_ctx)

        self.waiting_door = False

    def decide_dir(self, game_ctx):
        self.prev_dir = self.actor.look_dir.copy()
        delta = vec_sub(self.actor.pos, game_ctx.player.pos)
        wolflogger.debug(f"delta: {delta}")
        wolflogger.debug(f"actor pos: {self.actor.pos}")
        maxd = max(delta, key=abs)
        vertical = delta.index(maxd)
        mind = delta[~vertical + 2]
        dirs = [[1, 0], [0, 1]]
        dirs[vertical] = vec_mul(dirs[vertical], sign(maxd))
        dirs[~vertical + 2] = vec_mul(dirs[~vertical + 2], sign(mind))
        first_try = dirs[vertical]
        if not self.try_direction(first_try):
            if delta[~vertical + 2]:
                self.try_direction(dirs[~vertical + 2], allow_reverse=True)
        wolflogger.debug(f"actor look dir: {self.actor.look_dir}")

    def try_direction(self, dir_, allow_reverse=False):
        m = self.actor.wolfmap
        self.actor.update_direction(dir_)
        fblock = self.actor.get_front_block()
        lookup = tuple(fblock)
        if self.actor.wolfmap.cell_occupied(lookup):
            if lookup in m.doors:
                door = m.get_door(lookup)
                self.waiting_door = door
                if not (door.is_opening or door.is_open()):
                    wolflogger.debug(f"{self.actor}, openned door!")
                    door.begin_opening()
            return False
        if not any(vec_add(self.prev_dir, dir_)) and not allow_reverse:
            return False
        return True

    def actor_in_middle(self):
        w = self.actor.wolfmap.wall_width
        hw = w // 2
        pos = self.actor.pos
        return int(pos[0]) % w == hw or int(pos[1]) % w == hw

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

    def act(self, _):
        if self.gonna_attack:
            self.actor.interrupt_transition(AttackState(self.actor))
        self.heartbeats = (self.heartbeats + 1) % self.lifetime
        self.move_off = self.heartbeats // self.hb_perframe

        if not self.waiting_door:
            self.actor.move()

    def endcallback(self, game_ctx):
        if not self.waiting_door:
            self.decide_dir(game_ctx)


class Actor:
    def __init__(self, wolfmap, _type: WolfActorType, pos, look_dir,
                 sprites: list[Sprite], sprite_layout,
                 death_frames, move_frames, attack_frames, dead_offset, hurt_offset,
                 health=100, drop=None, _range=100, accuracy=1):
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
        self.pace = 0.5
        self.proximity_radius = self.wolfmap.wall_width * 6
        self.interrupted = False

    def tick(self, game_ctx, heartbeats):
        self.ticks_since_trans += heartbeats
        if self.ticks_since_trans == self.state.lifetime:
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

    def interrupt_transition(self, state: ActorState):
        self.interrupted = True
        self.ticks_since_trans = 0
        old = self.state
        state.next = old
        self.state = state

    def to_this_space(self, pos):
        to_self = vec_sub(pos, self.pos)
        obs_space = (vec_dot(to_self, self.left),
                     vec_dot(to_self, self.look_dir))
        return obs_space

    def get_current_block(self):
        return self.wolfmap.to_block_pos(*self.pos)

    def update_direction(self, dir_):
        self.look_dir = dir_
        self.left = [-self.look_dir[1], self.look_dir[0]]

    def move(self):
        m = self.wolfmap
        disp = vec_mul(self.look_dir, self.pace)
        new_pos = vec_add(self.pos, vec_mul(disp, self.pace))
        new_block = m.to_block_pos(*new_pos)
        if m.cell_occupied(new_block):
            return
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

    def get_shot(self, damage):
        self.dec_health(damage)
        dead = self.is_dead()
        if dead:
            self.state = DeadState(self)
        newst = DyingState(self) if dead else HurtState(self)
        self.interrupt_transition(newst)

    def get_front_block(self):
        pblock = self.wolfmap.to_block_pos(*self.pos)
        offset = [0, 0]
        mag = max(self.look_dir, key=abs)
        vertical = self.look_dir.index(mag)
        offset[vertical] += sign(mag)
        return vec_add(pblock, offset)

    def sees_player(self, game_ctx):
        r = game_ctx.renderer.raycaster
        p = game_ctx.player
        to_player = vec_norm(vec_sub(self.pos, p.pos))
        if vec_dot(self.look_dir, to_player) < 0:
            # player is behind the actor
            return False
        return p.get_current_block() in r.get_corridor(*to_player, self.pos)

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
                         drop=WolfItem.AMMUNITION)


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
                         _range=(wolfmap.wall_width)*2)
        self.pace = 0.7


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
                         drop=WolfItem.MACHINEGUN)


TYPE_ACTOR_OBJ = {
    WolfActorType.GUARD: Guard,
    WolfActorType.DOG: Shepherd,
    WolfActorType.SCHUTZSTAFFEL: SS,
}
