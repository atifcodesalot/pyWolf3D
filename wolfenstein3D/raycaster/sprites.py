

from wolfenstein3D.raycaster.textures import Texture, Image
from wolfenstein3D.raycaster.aux_math import vec_add, vec_dot, vec_sub


class Sprite(Texture):
    def __init__(self, image: Image.Image, pos=None, blocking=None):
        super().__init__(image)
        self.pos = pos
        self.blocking = blocking
        self.screen_pos = None
        self.projected = None
        self.screen_width = None

    def to_observer_space(self, observer):
        self.obs_space = observer.to_this_space(self.pos)
        return self.obs_space[1]

    def project(self):
        # guard against 0
        w = 1e-10 if self.obs_space[1] == 0 else self.obs_space[1]
        self.projected = (self.obs_space[0] / w, 1)

    # takes RayRenderer object
    def to_screen_pos(self, renderer):
        observer = renderer.raycaster.observer
        vpl = observer.vp_length
        # transform to screen position
        self.screen_pos = (
            (self.projected[0] + vpl) / (2*vpl)) * renderer.width

    def get_perp_dist(self, observer):
        to_self = vec_sub(observer.pos, self.pos)
        self.perp_dist = vec_dot(to_self, observer.look_dir)

    def translate(self, tvec):
        self.pos = vec_add(self.pos, tvec)

    def get_column(self, i, repeat, height, screen_height):
        scaled = self.scale_column(
            self.columns[i], repeat, height, screen_height)
        return scaled

    def copy(self, pos):
        copied = self.__new__(self.__class__)
        copied.__init__(self.image, pos=pos, blocking=self.blocking)
        return copied
