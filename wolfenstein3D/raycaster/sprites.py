

from .textures import Texture, pygame, Image
from .aux_math import vec_add


class Sprite(Texture):
    def __init__(self, image: Image.Image, pos=None, blocking=None):
        super().__init__(image)
        self.pos = pos
        self.blocking = blocking

        # sprites dont get shaded so it is easy to cache?
        self.column_cache = {}

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
        if (i, repeat, height) in self.column_cache:
            # cache hit
            return self.column_cache[(i, repeat, height)]

        # cache miss
        column = self.columns[i]

        if height > screen_height:
            # clip before scaling
            off = screen_height / height * self.half_height
            column = column.subsurface(
                (0, self.half_height - off, 1, off*2))
            height = screen_height

        height = max(height, 0)
        scaled = pygame.transform.scale(
            column, (repeat, height))
        # save to cache
        self.column_cache[(i, repeat, height)] = scaled
        return scaled

    def get_scaled_portion(self, xoff1, xoff2, width, height, screen_height):
        height = int(height)
        scaled = self.scale_column(
            self.surface, width, height, screen_height)
        return scaled.subsurface(
            (xoff1, 0, xoff2-xoff1, height))

    def copy(self, pos):
        copied = self.__new__(self.__class__)
        copied.__init__(self.image, pos=pos, blocking=self.blocking)
        copied.column_cache = self.column_cache
        return copied
