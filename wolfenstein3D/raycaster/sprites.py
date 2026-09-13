

from .textures import Texture, os, Image
from .raycaster import Observer
from .aux_math import plain_dot, plain_sub, plain_add


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
        # guard against 0
        w = 0.0001 if view[1] == 0 else view[1]
        return (view[0] / w, 1)

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


def init_sprites():
    global SPRITES
    SPRITES = {}
    for entry in os.scandir(SPRITE_PATH):
        if entry.is_file():
            if entry.name == "objects.png":
                objects_ = Image.open(entry.path)
                for i in range(0, 40):
                    SPRITES[f"object{i}"] = Sprite(objects_.crop((
                        i*64, 0, (i+1) * 64, 64)), None)
            print(Image.open(entry.path))
            SPRITES[entry.name] = Sprite(Image.open(entry.path), None)


init_sprites()
