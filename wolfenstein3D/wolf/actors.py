

from enum import Enum
from .assets import *
from raycaster.aux_math import *
from math import pi, atan2
from .animations import Animation
from .maps import WolfItem, WolfMap


class ActorState(Enum):
    # these values also used to point to the-
    # row numbers of general layout of the actor spritesheets
    STANDING = 0
    WALKING = 1
    # must be adjusted in the actor class if the walk cycle rows cary
    # e.g in the shepherd dog class
    DYING = 2
    SHOOTING = 3

# The actor class that is able to displace, shoot, do other stuff and "think".
# the amount of rows can vary: e.g:
# the dog spritesheet has one less row for walk cycle compared to the guard spritesheet
# it will assume the "hurt offset" is in the DYING row


class Actor:
    def __init__(self, wolfmap: WolfMap, pos, look_dir, name: str,
                 sprites: list[Sprite], sprite_layout,
                 death_frames, move_frames, dead_offset,
                 hurt_offset, state=ActorState(0), health=100):
        self.wolfmap = wolfmap
        self.pos = pos
        self.look_dir = look_dir
        self.left = [-self.look_dir[1], self.look_dir[0]]
        self.name = name
        self.state = state
        self.health = health

        self.sprites = [sprite.copy(self.pos) for sprite in sprites.values()]
        self.sprite_layout = sprite_layout
        self.sprite_per_row = self.sprite_layout[0]
        self.death_frames = death_frames
        self.move_frames = move_frames
        self.dead_offset = dead_offset
        self.hurt_offset = hurt_offset
        
        self.state_column = {
            0: 0,
            1: self.sprite_per_row,
            2: (1 + self.move_frames)*self.sprite_per_row,
            3: (2 + self.move_frames)*self.sprite_per_row
            
        }

        # not very nice
        self.being_shot = False
        self.dying = False
        #

        self.shapenum = self.state.value

    def tick(self, heartbeats):
        pass

    def decide_state(self):
        # placeholder
        return ActorState(0)

    def set_state(self, state=None):
        if self.is_dead():
            return
        if not state:
            self.state = self.decide_state()
        else:
            self.state = state

    def to_this_space(self, pos):
        to_self = plain_sub(pos, self.pos)
        obs_space = (plain_dot(to_self, self.left),
                     plain_dot(to_self, self.look_dir))
        return obs_space

    def get_current_sp_idx(self, observer, sectors=8):
        if self.is_dead():
            if self.dying:
                # animation playing will alter shapenum
                return int(self.shapenum)
            # if completely dead
            offset = self.dead_offset
        elif self.being_shot:
            # if being shot just return hurt offset
            offset = self.hurt_offset
        else:
            thispace = self.to_this_space(observer.pos)
            sx, sy = thispace
            offset = int((pi/2-atan2(-sy, sx)) // (2*pi / sectors) % sectors)
        return self.state_column[self.state.value] + offset

    def current_sprite(self, observer):
        self.shapenum = self.get_current_sp_idx(observer)
        sprite = self.sprites[self.shapenum]
        return sprite

    def dec_health(self, damage):
        self.health = max(0, self.health - damage)

    def is_dead(self):
        return self.health == 0

    # add_animation(self, anim, obj, target)
    def die(self, game):
        self.dying = True
        self.state = ActorState.DYING

        anim = Animation(None, None, 50, self.death_frames,
                         offset=self.state_column[2],
                         endcallback=self.death_end)
        game.add_animation(anim, self, "shapenum")

    def hurt_end(self, old_state):
        self.set_state(old_state)
        self.being_shot = False

    def death_end(self):
        self.dying = False

    # ouch
    def get_shot(self, game, damage):
        if self.dying or self.is_dead():
            return
        if self.being_shot:
            # if already being shot
            self.dec_health(damage)
            if self.is_dead():
                self.die(game)
            return
        # if not being already shot
        self.being_shot = True
        # placeholder damage model
        self.dec_health(damage)
        #
        if self.is_dead():
            self.die(game)
            return
        # if did not die
        old_state = self.state
        self.state = ActorState.DYING
        # schedule to return to old state after being hurt
        # after 20 ticks
        game.schedule_game_event(
            10, lambda _: self.hurt_end(old_state))


class Guard(Actor):
    def __init__(self, wolfmap, pos, look_dir, state=ActorState(0)):
        super().__init__(wolfmap, pos, look_dir, "Guard",
                         sprites=SPRITES["characters"]["guard"],
                         sprite_layout=(8, 7),
                         death_frames=5,
                         move_frames=4,
                         dead_offset=4,
                         hurt_offset=7,
                         state=state, health=100)

    def drop_ammunition(self):
        # drop ammunition upon death
        self.wolfmap.add_item(
            WolfItem.AMMUNITION,
            plain_add(self.pos, (2, 0)))

    def death_end(self):
        super().death_end()
        self.drop_ammunition()


class Shepherd(Actor):
    def __init__(self, wolfmap, pos, look_dir, state=ActorState(0)):
        super().__init__(wolfmap, pos, look_dir, "Shepherd",
                         sprites=SPRITES["characters"]["shepherd"],
                         sprite_layout=(8, 6),
                         death_frames=4,
                         move_frames=3,
                         dead_offset=3,
                         hurt_offset=0,
                         state=state, health=60)


class SS(Actor):
    def __init__(self, wolfmap, pos, look_dir, state=ActorState(0)):
        super().__init__(wolfmap, pos, look_dir, "Shepherd",
                         sprites=SPRITES["characters"]["SS"],
                         sprite_layout=(8, 7),
                         death_frames=6,
                         move_frames=4,
                         dead_offset=5,
                         hurt_offset=0,
                         state=state, health=120)
