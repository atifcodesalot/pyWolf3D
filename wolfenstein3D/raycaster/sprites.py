

from .textures import Texture, os, Image
from .raycaster import Observer
from .aux_math import plain_dot, plain_sub


SPRITE_PATH = os.path.join('.', 'sprites')


class Sprite(Texture):
    def __init__(self, image, pos):
        super().__init__(image)
        self.pos = pos

    def to_observer_space(self, observer: Observer):
        to_self = plain_sub(self.pos, observer.pos)
        return (plain_dot(to_self, observer.left),
                plain_dot(to_self, observer.look_dir))

    def project(self, observer: Observer):
        view = self.to_observer_space(observer)
        return (view[0] / view[1], 1)

    # takes RayRenderer object
    def screen_pos(self, renderer, projected):
        observer = renderer.raycaster.observer
        vpl = observer.vp_length
        # transform to screen position
        return ((projected[0] + vpl) / (2*vpl)) * renderer.width


def init_sprites():
    global SPRITES
    SPRITES = {}
    for entry in os.scandir(SPRITE_PATH):
        if entry.is_file():
            print(Image.open(entry.path))
            SPRITES[entry.name] = Sprite(Image.open(entry.path), None)
            
init_sprites()
