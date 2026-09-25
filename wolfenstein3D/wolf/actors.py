

from .assets import *
from raycaster.aux_math import *
from math import pi, atan2
from .maps import WolfItem, WolfMap
import random


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
            self.next = ChaseState(self.actor, 0)

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
                              plain_add(self.actor.pos, (2, 0)))


class HurtState(ActorState):
    def __init__(self, actor):
        super().__init__(actor, 2, nextstate=None, lifetime=20)
        self.inflicted_damage = False

    def shapenum(self, _):
        col = self.colnum()
        return col + self.actor.hurt_offset


class AttackState(ActorState):
    def __init__(self, actor):
        super().__init__(actor, 3, nextstate=None, lifetime=20)
        self.hb_perframe = self.lifetime // actor.attack_frames
        self.heartbeats = 0
        self.attacked = False
        
    def shapenum(self, _):
        col = self.colnum()
        return col + self.heartbeats // self.hb_perframe

    def act(self, game_ctx):
        if not self.attacked:
            if random.randint(1, 2) == 2:
                game_ctx.player.dec_health(20)
            self.attacked = True
        self.heartbeats += 1


class ChaseState(ActorState):
    def __init__(self, actor, walk_cycle):
        super().__init__(actor, 1, self, 20)
        if type(actor) is Shepherd:
            # dogs dont have standing sprites
            self.spcolumn = 0
        self.hb_perframe = self.lifetime // self.actor.move_frames
        self.move_off = walk_cycle
        self.heartbeats = 0

    def colnum(self):
        return super().colnum() + \
            self.move_off*self.actor.sprite_per_state

    def shapenum(self, observer):
        spps = self.actor.sprite_per_state
        col = self.colnum()
        ori = self.actor.orientation_idx(observer, sectors=spps)
        return col + ori

    def think(self, game_ctx):
        if random.randint(1, 100) == 2:
            self.actor.interrupt_transition(AttackState(self.actor))

    def act(self, game_ctx):
        self.heartbeats = (self.heartbeats + 1) % self.lifetime
        self.move_off = self.heartbeats // self.hb_perframe
        self.actor.turn_towards(game_ctx.player.pos)
        self.actor.move()


class Actor:
    def __init__(self, wolfmap: WolfMap, pos, look_dir, name: str,
                 sprites: list[Sprite], sprite_layout,
                 death_frames, move_frames, attack_frames, 
                 dead_offset, hurt_offset, health=100, drop=None):
        self.wolfmap = wolfmap
        self.pos = pos
        self.look_dir = look_dir
        self.left = [-self.look_dir[1], self.look_dir[0]]
        self.name = name
        self.state = GuardingState(self)
        self.health = health
        self.drop = drop

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
        self.proximity_radius = 50

    def tick(self, game_ctx, heartbeats):
        self.ticks_since_trans += heartbeats
        if self.ticks_since_trans == self.state.lifetime:
            self.timeout_transition(game_ctx)
        self.state.think(game_ctx)
        self.state.act(game_ctx)

    def timeout_transition(self, game_ctx):
        self.ticks_since_trans = 0
        self.state.endcallback(game_ctx)
        self.state = self.state.next

    def interrupt_transition(self, state: ActorState):
        self.ticks_since_trans = 0
        old = self.state
        state.next = old
        self.state = state

    def to_this_space(self, pos):
        to_self = plain_sub(pos, self.pos)
        obs_space = (plain_dot(to_self, self.left),
                     plain_dot(to_self, self.look_dir))
        return obs_space

    def turn_towards(self, point):
        self.look_dir = plain_normalize(
            plain_sub(self.pos, point))

    def move(self):
        self.pos = plain_add(self.pos,
                             plain_mul(self.look_dir, self.pace))

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


class Guard(Actor):
    def __init__(self, wolfmap, pos, look_dir):
        super().__init__(wolfmap, pos, look_dir, "Guard",
                         sprites=SPRITES["characters"]["guard"],
                         sprite_layout=(8, 7),
                         death_frames=5,
                         move_frames=4,
                         attack_frames=2,
                         dead_offset=4,
                         hurt_offset=7,
                         health=100,
                         drop=WolfItem.AMMUNITION)


class Shepherd(Actor):
    def __init__(self, wolfmap, pos, look_dir):
        super().__init__(wolfmap, pos, look_dir, "Shepherd",
                         sprites=SPRITES["characters"]["shepherd"],
                         sprite_layout=(8, 6),
                         death_frames=3,
                         move_frames=3,
                         attack_frames=2,
                         dead_offset=3,
                         hurt_offset=0,
                         health=60)


class SS(Actor):
    def __init__(self, wolfmap, pos, look_dir):
        super().__init__(wolfmap, pos, look_dir, "SS",
                         sprites=SPRITES["characters"]["SS"],
                         sprite_layout=(8, 7),
                         death_frames=5,
                         move_frames=4,
                         attack_frames=2,
                         dead_offset=5,
                         hurt_offset=0,
                         health=120,
                         drop=WolfItem.MACHINEGUN)
