
from raycaster.sprites import Sprite
from raycaster.textures import Texture
from PIL import Image
import os


SPRITE_PATH = os.path.join('.', 'sprites')
TEXTURE_PATH = os.path.join('.', 'textures')

OBJECTS_PATH = os.path.join(SPRITE_PATH, 'objects.png')

# code used for creating transparency
# def convert_sheet_trans(sheet: Image.Image, target: tuple, savename: str):
#     sheet = sheet.convert("RGBA")
#     datas = sheet.getdata()

#     new = []
#     for item in datas:
#         if item[0] == target[0] and item[1] == target[1] and item[2] == target[2]:
#             new.append((255, 255, 255, 0))
#         else:
#             new.append(item)

#     sheet.putdata(new)
#     sheet.save(savename, "PNG")


def texmap_parse(bmarg, tmarg, vsep, hsep, tw, th,
                 texmap: Image.Image, init, lmarg=0, rmarg=0):
    textures = []
    init = init if callable(init) else lambda im:im
    w, h = texmap.width, texmap.height
    for j in range(tmarg, h-bmarg, vsep + th):
        for i in range(lmarg, w-rmarg, hsep + tw):
            cursor = (i, j)
            subimage = texmap.crop((
                cursor[0], cursor[1], cursor[0] + tw, cursor[1] + th))
            textures.append(init(subimage))
    return textures


def init_wall_textures():
    global WALL_TEXTURES
    walls = Image.open(os.path.join(TEXTURE_PATH, 'wallmap.png'))
    WALL_TEXTURES = texmap_parse(0, 0, 0, 0, 128, 128, walls, init=Texture)

    # extend to 100 slot texture table
    WALL_TEXTURES.extend([0]*100)
    WALL_TEXTURES[31 << 1] = WALL_TEXTURES[31]


def init_textures():
    init_wall_textures()
    # init more textures in the future?


def init_object_sprites():
    objects_sheet = Image.open(OBJECTS_PATH)
    objects_ = texmap_parse(0, 0, 0, 0, 64, 64, objects_sheet, init=Sprite)
    SPRITES["objects"] = dict(enumerate(objects_))
    print(SPRITES)
    
def init_object_sprites():
    objects_sheet = Image.open(OBJECTS_PATH)
    objects_ = texmap_parse(0, 0, 0, 0, 64, 64, objects_sheet, init=Sprite)
    SPRITES["objects"] = dict(enumerate(objects_))
    print(SPRITES)


def init_sprites():
    global SPRITES
    SPRITES = {}
    init_object_sprites()
    def clean_remaining():
        for entry in os.scandir(SPRITE_PATH):
            if entry.is_file():
                SPRITES[entry.name] = Sprite(Image.open(entry.path), None, None)
            if entry.is_dir():
                for entry2 in os.scandir(entry.path):
                    if entry2.is_file():
                        SPRITES[entry.name + "/" + entry2.name] = Sprite(
                            Image.open(entry2.path), None, None)
    clean_remaining()
    
        


init_sprites()
init_textures()


