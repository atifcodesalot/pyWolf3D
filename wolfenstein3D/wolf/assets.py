
from raycaster.sprites import Sprite
from raycaster.textures import Texture
from . import SPRITES, WALL_TEXTURES, pygame
from PIL import Image
import os


ASSETS_PATH = os.path.join('.', 'assets')

FONT_PATH = os.path.join(ASSETS_PATH, 'fonts')
SPRITE_PATH = os.path.join(ASSETS_PATH, 'sprites')
TEXTURE_PATH = os.path.join(ASSETS_PATH, 'textures')
SOUND_PATH = os.path.join(ASSETS_PATH, 'sound')

WALLS_PATH = os.path.join(TEXTURE_PATH, 'wallmap.png')
HUD_PATH = os.path.join(TEXTURE_PATH, 'hud.png')

SPRITE_OBJECTS_PATH = os.path.join(SPRITE_PATH, 'objects.png')
SPRITE_WEAPONS_PATH = os.path.join(SPRITE_PATH, 'weapons.png')


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
    init = init if callable(init) else lambda im: im
    w, h = texmap.width, texmap.height
    for j in range(tmarg, h-bmarg, vsep + th):
        for i in range(lmarg, w-rmarg, hsep + tw):
            cursor = (i, j)
            subimage = texmap.crop((
                cursor[0], cursor[1], cursor[0] + tw, cursor[1] + th))
            if callable(init):
                textures.append(init(subimage))
            else:
                textures.append(subimage)
    return textures


def init_wall_textures():
    global WALL_TEXTURES, SIDEDOOR
    SIDEDOOR = 58
    walls = Image.open(WALLS_PATH)
    WALL_TEXTURES = texmap_parse(486, 16, 1, 1, 64, 64, walls, init=Texture, lmarg=1, rmarg=1)

    # extend to 120 slot texture table
    WALL_TEXTURES.extend([None]*120)


def init_hud_textures():
    def to_surf(im):
        return pygame.image.frombytes(
            im.tobytes(),
            im.size,
            "RGBA",
        )
    global HUD_FACES, STATUSBAR, HUD_NUMBERS, HUD_WEAPONS
    hudim = Image.open(HUD_PATH)
    HUD_FACES = texmap_parse(
        52, 42, 1, 1, 24, 32, hudim, init=to_surf, lmarg=1, rmarg=91)
    hudsurf = to_surf(hudim)
    STATUSBAR = hudsurf.subsurface((1, 1, 320, 40))
    HUD_NUMBERS = texmap_parse(
        68, 75, 0, 1, 8, 16, hudim, init=to_surf, lmarg=301, rmarg=1)
    HUD_WEAPONS = texmap_parse(
        1, 109, 1, 1, 48, 24, hudim, init=to_surf, lmarg=226, rmarg=68)


def init_textures():
    init_wall_textures()
    init_hud_textures()
    # init more textures in the future?


def init_object_sprites():
    objects_sheet = Image.open(SPRITE_OBJECTS_PATH)
    objects_ = texmap_parse(0, 0, 0, 0, 64, 64, objects_sheet, init=Sprite)
    SPRITES["objects"] = dict(enumerate(objects_))


def init_weapon_srites():
    weapons_sheet = Image.open(SPRITE_WEAPONS_PATH)
    weapons = texmap_parse(34, 16, 16, 1, 64, 64, weapons_sheet, Sprite, 1, 1)
    SPRITES["weapons"] = dict(enumerate(weapons))


def init_character_sprites():
    SPRITES["characters"] = {}
    guard_sheet = Image.open(os.path.join(
        SPRITE_PATH, 'characters', 'guard.png'))
    guard_sprites = texmap_parse(0, 0, 1, 1, 64, 64, guard_sheet, Sprite)
    SPRITES["characters"]["guard"] = dict(enumerate(guard_sprites))

    dog_sheet = Image.open(os.path.join(
        SPRITE_PATH, 'characters', 'shepherd.png'))
    dog_sprites = texmap_parse(0, 0, 1, 1, 64, 64, dog_sheet, Sprite)
    SPRITES["characters"]["shepherd"] = dict(enumerate(dog_sprites))

    SS_sheet = Image.open(os.path.join(SPRITE_PATH, 'characters', 'SS.png'))
    SS_sprites = texmap_parse(1, 1, 1, 1, 64, 64, SS_sheet, Sprite, 1, 1)
    SPRITES["characters"]["SS"] = dict(enumerate(SS_sprites))
    
    # init bosses here
    SPRITES["characters"]["boss"] = {}
    # init hans grösse
    hans_sheet =  Image.open(os.path.join(SPRITE_PATH, 'characters', 'boss', 'hansgrösse.png'))
    hans_sprites = texmap_parse(1, 1, 1, 1, 64, 64, hans_sheet, Sprite, 1, 1)
    ogsrc = dict(enumerate(hans_sprites))
    hans_sprites = {}
    for i in range(4):
        hans_sprites[i*4] = ogsrc[i]
    death_off = 16
    for i in range(4):
        hans_sprites[death_off + i] = ogsrc[8 + i]
    attack_off = 20
    for i in range(3):
        hans_sprites[attack_off + i] = ogsrc[4 + i]
    SPRITES["characters"]["boss"]["hans"] = hans_sprites
    


def init_sprites():
    init_object_sprites()
    init_weapon_srites()
    init_character_sprites()

    def clean_remaining():
        for entry in os.scandir(SPRITE_PATH):
            if entry.is_file():
                SPRITES[entry.name] = Sprite(
                    Image.open(entry.path), None, None)
            if entry.is_dir():
                for entry2 in os.scandir(entry.path):
                    if entry2.is_file():
                        SPRITES[entry.name + "/" + entry2.name] = Sprite(
                            Image.open(entry2.path), None, None)
    clean_remaining()


def init_font():
    font_size = 30
    global FONT
    FONT = pygame.font.Font(os.path.join(FONT_PATH, "ITCHonda.ttf"), font_size)


def init_sounds(root=SOUND_PATH, depth=0):
    if depth == 0:
        global SOUNDS
        SOUNDS = {}
    base = os.path.basename(root)
    SOUNDS[base] = {}
    for entry in os.scandir(root):
        if entry.is_dir():
            init_sounds(root=entry.path, depth=depth+1)
        elif entry.is_file():
            if base == "music":
                SOUNDS[base][entry.name] = entry.path
            else:
                SOUNDS[base][entry.name] = pygame.mixer.Sound(entry.path)


init_textures()
init_sprites()
init_font()
init_sounds()
