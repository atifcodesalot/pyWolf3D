
from wolfenstein3D.raycaster.sprites import Sprite
from wolfenstein3D.raycaster.textures import Texture
from wolfenstein3D.wolf import pygame
from PIL import Image
import os


class WolfAssetManager:
    def __init__(self):
        self.assets_path = os.path.join(
            '.', __package__.split('.')[0], 'assets')

        self.font_path = os.path.join(self.assets_path, 'fonts')
        self.sprite_path = os.path.join(self.assets_path, 'sprites')
        self.texture_path = os.path.join(self.assets_path, 'textures')
        self.sound_path = os.path.join(self.assets_path, 'sound')

        self.walls_path = os.path.join(self.texture_path, 'wallmap.png')
        self.hud_path = os.path.join(self.texture_path, 'hud.png')

        self.sprite_objects_path = os.path.join(
            self.sprite_path, 'objects.png')
        self.sprite_weapons_path = os.path.join(
            self.sprite_path, 'weapons.png')

        self.init_font()
        self.init_textures()
        self.init_sprites()
        self.init_sounds()

    @staticmethod
    def texmap_parse(texmap: Image.Image, bmarg, tmarg,
                     vsep, hsep, tw, th, init, lmarg=0, rmarg=0):
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

    def init_wall_textures(self):
        walls = Image.open(self.walls_path)
        self.wall_textures = self.texmap_parse(walls,
                                               486, 16, 1, 1, 64, 64, init=Texture, lmarg=1, rmarg=1)
        nocturnal = self.texmap_parse(walls,
                                      1, 631, 1, 1, 64, 64, init=Texture, lmarg=1, rmarg=1)
        self.wall_textures.extend(nocturnal)

        # extend to 120 slot texture table
        self.wall_textures.extend([None]*120)

    @staticmethod
    def convert_sheet_trans(sheet: Image.Image, target: tuple, savename: str):
        sheet = sheet.convert("RGBA")
        datas = sheet.getdata()

        new = []
        for item in datas:
            if item[0] == target[0] and item[1] == target[1] and item[2] == target[2]:
                new.append((255, 255, 255, 0))
            else:
                new.append(item)

        sheet.putdata(new)
        sheet.save(savename, "PNG")

    def init_hud_textures(self):
        def to_surf(im):
            return pygame.image.frombytes(
                im.tobytes(),
                im.size,
                "RGBA",
            )
        hudim = Image.open(self.hud_path)
        self.hud_faces = self.texmap_parse(hudim,
                                           52, 42, 1, 1, 24, 32, init=to_surf, lmarg=1, rmarg=91)
        hudsurf = to_surf(hudim)
        self.statusbar = hudsurf.subsurface((1, 1, 320, 40))
        self.hud_numbers = self.texmap_parse(hudim,
                                             68, 75, 0, 1, 8, 16, init=to_surf, lmarg=301, rmarg=1)
        self.hud_weapons = self.texmap_parse(hudim,
                                             1, 109, 1, 1, 48, 24, init=to_surf, lmarg=226, rmarg=68)
        self.hud_keys = self.texmap_parse(hudim,
                                          51, 92, 0, 1, 8, 16, init=to_surf, lmarg=301, rmarg=55)

    def init_textures(self):
        self.init_wall_textures()
        self.init_hud_textures()
        # init more textures in the future?

    def init_object_sprites(self):
        objects_sheet = Image.open(self.sprite_objects_path)
        objects_ = self.texmap_parse(objects_sheet,
                                     0, 0, 0, 0, 64, 64, init=Sprite)
        self.sprites["objects"] = dict(enumerate(objects_))

    def init_weapon_sprites(self):
        weapons_sheet = Image.open(self.sprite_weapons_path)
        weapons = self.texmap_parse(weapons_sheet,
                                    34, 16, 16, 1, 64, 64, init=Sprite, lmarg=1, rmarg=1)
        self.sprites["weapons"] = dict(enumerate(weapons))

    def init_character_sprite(self, filename, charname, *texmap_args):
        char_sheet = Image.open(os.path.join(
            self.sprite_path, 'characters', filename))
        char_sprites = self.texmap_parse(char_sheet, *texmap_args)
        self.sprites["characters"][charname] = dict(enumerate(char_sprites))

    def init_character_sprites(self):
        self.sprites["characters"] = {}
        self.init_character_sprite(
            'guard.png', 'guard', 0, 0, 1, 1, 64, 64, Sprite)
        self.init_character_sprite(
            'shepherd.png', 'shepherd', 0, 0, 1, 1, 64, 64, Sprite)
        self.init_character_sprite('SS.png', 'SS', 1, 1, 1, 1, 64, 64, Sprite, 1, 1)
        self.init_character_sprite(
            'officer.png', 'officer', 1, 1, 1, 1, 64, 64, Sprite, 1, 1)
        self.init_character_sprite(
            'mutant.png', 'mutant', 1, 1, 1, 1, 64, 64, Sprite, 1, 1)

        # init bosses here
        # todo: please refactor this shit in the name of jesus christ
        self.sprites["characters"]["boss"] = {}
        # init hans grösse
        hans_sheet = Image.open(os.path.join(
            self.sprite_path, 'characters', 'boss', 'hansgrösse.png'))
        hans_sprites = self.texmap_parse(hans_sheet,
                                         1, 1, 1, 1, 64, 64, Sprite, 1, 1)
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
        self.sprites["characters"]["boss"]["hans"] = hans_sprites

    def init_sprites(self):
        self.sprites = {}
        self.init_object_sprites()
        self.init_weapon_sprites()
        self.init_character_sprites()

        def clean_remaining():
            for entry in os.scandir(self.sprite_path):
                if entry.is_file():
                    self.sprites[entry.name] = Sprite(
                        Image.open(entry.path), None, None)
                if entry.is_dir():
                    for entry2 in os.scandir(entry.path):
                        if entry2.is_file():
                            self.sprites[entry.name + "/" + entry2.name] = Sprite(
                                Image.open(entry2.path), None, None)
        clean_remaining()

    def init_font(self):
        font_size = 20

        self.font = pygame.font.Font(os.path.join(
            self.font_path, "ITCHonda.ttf"), font_size)
        self.biggerfont = pygame.font.Font(os.path.join(
            self.font_path, "ITCHonda.ttf"), font_size+20)

    def init_sounds(self, root=None, depth=0):
        if root is None:
            root = self.sound_path
        if depth == 0:
            self.sounds = {}
        base = os.path.basename(root)
        self.sounds[base] = {}
        for entry in os.scandir(root):
            if entry.is_dir():
                self.init_sounds(root=entry.path, depth=depth+1)
            elif entry.is_file():
                if base == "music":
                    self.sounds[base][entry.name] = entry.path
                else:
                    self.sounds[base][entry.name] = pygame.mixer.Sound(
                        entry.path)


def init_assets():
    global ASSET_MANAGER
    ASSET_MANAGER = WolfAssetManager()


init_assets()
