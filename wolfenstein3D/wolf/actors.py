

from enum import Enum
from .assets import *
from raycaster.aux_math import *
from math import pi, atan2


class ActorState(Enum):
    STANDING = 0
    WALKING = 1
    DYING = 5
    SHOOTING = 6

# The actor class that is able to displace, shoot, do other stuff and "think".


class Actor:
    def __init__(self, pos, look_dir, name: str,
                 sprites: list[Sprite], state=ActorState(0)):
        self.pos = pos
        self.look_dir = look_dir
        self.left = [-self.look_dir[1], self.look_dir[0]]
        self.name = name
        self.state = state
        self.sprites = [sprite.copy(self.pos) for sprite in sprites.values()]

    def tick(self, dt):
        pass

    def decide_state(self):
        # placeholder
        return ActorState(0)

    def change_state(self):
        self.state = self.decide_state()

    def to_this_space(self, pos):
        to_self = plain_sub(pos, self.pos)
        obs_space = (plain_dot(to_self, self.left),
                     plain_dot(to_self, self.look_dir))
        return obs_space

    def current_orientation(self, observer, sectors=8):
        thispace = self.to_this_space(observer.pos)
        sx, sy = thispace
        return (-(pi/2-atan2(sy, sx)) // (2*pi / sectors)) % sectors

    def current_sprite(self, observer):
        orientation = self.current_orientation(observer)
        sprite = self.sprites[int(self.state.value + orientation)]
        sprite.pos = self.pos
        return sprite
