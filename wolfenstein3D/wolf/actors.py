

from .assets import *
from raycaster.aux_math import *
from math import pi, atan2
from .animations import Animation
from .maps import WolfItem, WolfMap


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
        super().__init__(actor, 0, nextstate=self, lifetime=20)

    def think(self, game_ctx):
        pass

    def act(self, game_ctx):
        pass

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
        super().__init__(actor, 2, nextstate=DeadState(actor), lifetime=50)
        self.hb_perframe = self.lifetime // actor.death_frames
        self.anim_off = 0

    def act(self, _):
        self.anim_off += 1

    def shapenum(self, _):
        col = self.colnum()
        return col + self.anim_off // self.hb_perframe


class HurtState(ActorState):
    def __init__(self, actor, old_state):
        super().__init__(actor, 2, nextstate=old_state, lifetime=50)
        self.inflicted_damage = False

    def shapenum(self, _):
        col = self.colnum()
        return col + self.actor.hurt_offset


class Actor:
    def __init__(self, wolfmap: WolfMap, pos, look_dir, name: str,
                 sprites: list[Sprite], sprite_layout,
                 death_frames, move_frames, dead_offset,
                 hurt_offset, health=100):
        self.wolfmap = wolfmap
        self.pos = pos
        self.look_dir = look_dir
        self.left = [-self.look_dir[1], self.look_dir[0]]
        self.name = name
        self.state = GuardingState(self)
        self.health = health

        self.sprites = [sprite.copy(self.pos) for sprite in sprites.values()]
        self.sprite_layout = sprite_layout
        self.sprite_per_state = self.sprite_layout[0]
        self.death_frames = death_frames
        self.move_frames = move_frames
        self.dead_offset = dead_offset
        self.hurt_offset = hurt_offset

        self.ticks_since_trans = 0
        self.pace = 1

    def tick(self, game_ctx, heartbeats):
        self.ticks_since_trans += heartbeats
        if self.ticks_since_trans == self.state.lifetime:
            self.timeout_transition()
        self.state.think(game_ctx)
        self.state.act(game_ctx)

    def timeout_transition(self):
        self.ticks_since_trans = 0
        self.state = self.state.next

    def interrupt_transition(self, state: ActorState):
        self.ticks_since_trans = 0
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
                             plain_mul(self.look_dir * self.pace))

    def orientation_idx(self, observer, sectors=8):
        myspace = self.to_this_space(observer.pos)
        sx, sy = myspace
        return int((pi/2-atan2(-sy, sx)) // (2*pi / sectors) % sectors)

    def current_sprite(self, observer):
        self.shapenum = self.state.shapenum(observer)
        sprite = self.sprites[self.shapenum]
        return sprite

    def dec_health(self, damage):
        self.health = max(0, self.health - damage)

    def is_dead(self):
        return self.health == 0

    def get_shot(self, damage):
        self.dec_health(damage)
        old = self.state
        newst = DyingState(self) if self.is_dead() else HurtState(
            self, old)  # return to the old state after Hurt

        self.interrupt_transition(newst)


class Guard(Actor):
    def __init__(self, wolfmap, pos, look_dir):
        super().__init__(wolfmap, pos, look_dir, "Guard",
                         sprites=SPRITES["characters"]["guard"],
                         sprite_layout=(8, 7),
                         death_frames=5,
                         move_frames=4,
                         dead_offset=4,
                         hurt_offset=7,
                         health=100)

    def drop_ammunition(self):
        # drop ammunition upon death
        self.wolfmap.add_item(
            WolfItem.AMMUNITION,
            plain_add(self.pos, (2, 0)))


class Shepherd(Actor):
    def __init__(self, wolfmap, pos, look_dir):
        super().__init__(wolfmap, pos, look_dir, "Shepherd",
                         sprites=SPRITES["characters"]["shepherd"],
                         sprite_layout=(8, 6),
                         death_frames=4,
                         move_frames=3,
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
                         dead_offset=5,
                         hurt_offset=0,
                         health=120)
