

from wolfenstein3D.raycaster.textures import Texture, pygame, Image
from wolfenstein3D.raycaster.aux_math import vec_add


class Sprite(Texture):
    def __init__(self, image: Image.Image, pos=None, blocking=None):
        super().__init__(image)
        self.pos = pos
        self.blocking = blocking

    def to_observer_space(self, observer):
        self.obs_space = observer.to_this_space(self.pos)
        return self.obs_space[1]

    def project(self):
        # guard against 0
        w = 1e-10 if self.obs_space[1] == 0 else self.obs_space[1]
        return (self.obs_space[0] / w, 1)

    # takes RayRenderer object
    def screen_pos(self, renderer, projected):
        observer = renderer.raycaster.observer
        vpl = observer.vp_length
        # transform to screen position
        return ((projected[0] + vpl) / (2*vpl)) * renderer.width

    def translate(self, tvec):
        self.pos = vec_add(self.pos, tvec)

    def get_column(self, i, repeat, height, screen_height):
        scaled = self.scale_column(
            self.columns[i], repeat, height, screen_height)
        return scaled

    def get_scaled(self, width, height, screen_height):
        width = int(width)
        height = int(height)
        if (width, height) in self.scale_cache:
            return self.scale_cache[(width, height)]
        scaled = self.scale_column(
            self.surface, width, height, screen_height)
        self.scale_cache[(width, height)] = scaled
        return scaled

    def copy(self, pos):
        copied = self.__new__(self.__class__)
        copied.__init__(self.image, pos=pos, blocking=self.blocking)
        return copied
