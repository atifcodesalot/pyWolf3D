

from enum import Enum
from .assets import *
from raycaster.aux_math import *
from math import pi, atan2
from .animations import Animation


class ActorState(Enum):
    STANDING = 0
    WALKING = 1
    DYING = 5
    SHOOTING = 6

# The actor class that is able to displace, shoot, do other stuff and "think".


class Actor:
    def __init__(self, pos, look_dir, name: str,
                 sprites: list[Sprite], state=ActorState(0), health=100):
        self.pos = pos
        self.look_dir = look_dir
        self.left = [-self.look_dir[1], self.look_dir[0]]
        self.name = name
        self.state = state
        self.health = health

        self.sprites = [sprite.copy(self.pos) for sprite in sprites.values()]
        self.sprite_per_state = 8

        # not very nice
        self.being_shot = False
        self.dying = False
        self.shapenum = self.state.value

    def tick(self, dt):
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
            offset = 4
        elif self.being_shot:
            offset = 7
        else:
            thispace = self.to_this_space(observer.pos)
            sx, sy = thispace
            offset = int((pi/2-atan2(-sy, sx)) // (2*pi / sectors) % sectors)
        return self.sprite_per_state * self.state.value + offset

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
        self.state = ActorState(5)

        def death_end():
            self.dying = False
        anim = Animation(None, None, 50, 5,
                         offset=ActorState.DYING.value *
                         self.sprite_per_state, endcallback=death_end)
        game.add_animation(anim, self, "shapenum")

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
        # placeholder, no damage model
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
        def return_(_):
            self.set_state(old_state)
            self.being_shot = False
            
        game.schedule_game_event(
            10, return_)
