

from .textures import Texture, os, Image
from .aux_math import plain_dot, plain_sub, plain_add


class Sprite(Texture):
    def __init__(self, image: Image.Image, pos=None, blocking=None):
        super().__init__(image)
        self.pos = pos
        self.image = image
        self.blocking = blocking

    def to_observer_space(self, observer):
        to_self = plain_sub(self.pos, observer.pos)
        self.ospace = (plain_dot(to_self, observer.left),
                plain_dot(to_self, observer.look_dir))
        return self.ospace[1]

    def project(self):
        # guard against 0
        w = 0.0001 if self.ospace[1] == 0 else self.ospace[1]
        return (self.ospace[0] / w, 1)

    # takes RayRenderer object
    def screen_pos(self, renderer, projected):
        observer = renderer.raycaster.observer
        vpl = observer.vp_length
        # transform to screen position
        return ((projected[0] + vpl) / (2*vpl)) * renderer.width

    def translate(self, tvec):
        self.pos = plain_add(self.pos, tvec)
        
    def shade(self, _, i):
        return self.columns[i]
    
    def copy(self, pos):
        copied = self.__new__(self.__class__)
        copied.__init__(self.image, pos=pos, blocking=self.blocking)
        return copied