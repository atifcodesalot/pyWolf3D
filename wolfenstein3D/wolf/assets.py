
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

    # the sprite sheet (a list of sprites) must be in the form of the matrix:
    # Standing sprites (orientation variants)
    # n columns of moving sprites (orientation variants)
    # :
    # :
    # :
    # Death sprites and hurt sprite
    # Attack sprites

    @staticmethod
    def adapt_character_sprites(move_frames, move_frame_amount, death_frames,
                                attack_frames, layout, stand_frames=None,
                                no_orientation=True, move_transpose=True):

        adapted = {}
        w, h = layout
        for i in range(w*h):
            adapted[i] = None

        ori = 1 if no_orientation else w

        if stand_frames is not None:
            # adapt standing sprites
            for i in range(ori):
                adapted[i] = stand_frames[i]
        else:
            for i in range(ori):
                adapted[i] = move_frames[i]

        # adapt moving sprites
        for j in range(move_frame_amount):
            for i in range(ori):
                move_frame = move_frames[i*w +
                                         j] if move_transpose else move_frames[j*w + i]
                adapted[i+(j+1)*w] = move_frame

        # adapt death sprites
        for i in range(len(death_frames)):
            adapted[i + (1 + move_frame_amount)*w] = death_frames[i]

        # adapt attack sprites
        for i in range(len(attack_frames)):
            adapted[i + (2 + move_frame_amount)*w] = attack_frames[i]

        return adapted

    def adapt_bosses(self, *sprites):
        hans, gretel, schabbs, \
            giftmacher, fettgesicht, hitler, mechahitler = sprites
        hans_adapted = self.adapt_character_sprites(
            move_frames=hans[:4], move_frame_amount=4,
            death_frames=hans[8:12],
            attack_frames=hans[4: 7], layout=[4, 7])
        self.sprites["characters"]["boss"]["hans"] = hans_adapted
        gretel_adapted = self.adapt_character_sprites(
            move_frames=gretel[:4], move_frame_amount=4,
            death_frames=gretel[8:12],
            attack_frames=gretel[4: 7], layout=[4, 7])
        self.sprites["characters"]["boss"]["gretel"] = gretel_adapted
        schabbs_adapted = self.adapt_character_sprites(
            move_frames=schabbs[:4], move_frame_amount=4,
            death_frames=schabbs[8:12],
            attack_frames=schabbs[4: 7], layout=[4, 7])
        self.sprites["characters"]["boss"]["schabbs"] = schabbs_adapted

        self.sprites["projectiles"]["syringes"] = schabbs[12:]

        giftmacher_adapted = self.adapt_character_sprites(
            move_frames=giftmacher[:4], move_frame_amount=4,
            death_frames=giftmacher[8:12],
            attack_frames=giftmacher[4: 6], layout=[4, 7])
        self.sprites["characters"]["boss"]["giftmacher"] = giftmacher_adapted

        self.sprites["projectiles"]["rockets"] = giftmacher[12: 20]
        self.sprites["projectiles"]["explosion"] = giftmacher[24: 27]

        fettgesicht_adapted = self.adapt_character_sprites(
            move_frames=fettgesicht[:4], move_frame_amount=4,
            death_frames=fettgesicht[8:12],
            attack_frames=fettgesicht[4: 8], layout=[4, 7])
        self.sprites["characters"]["boss"]["fettgesicht"] = fettgesicht_adapted
        
        hitler_adapted = self.adapt_character_sprites(
                    move_frames=hitler[:4], move_frame_amount=4,
                    death_frames=hitler[8:] + [hitler[7],],
                    attack_frames=hitler[4:7], layout=[8, 7]) # has 8 death frames
        self.sprites["characters"]["boss"]["hitler"] = hitler_adapted
        
        mechahitler_adapted = self.adapt_character_sprites(
                            move_frames=mechahitler[:4], move_frame_amount=4,
                            death_frames=mechahitler[8:11] + [mechahitler[7],],
                            attack_frames=mechahitler[4: 7], layout=[4, 7])
        self.sprites["characters"]["boss"]["mechahitler"] = mechahitler_adapted

    def init_boss_sprites(self):
        self.sprites["characters"]["boss"] = {}
        # init hans grösse
        hans_sheet = Image.open(os.path.join(
            self.sprite_path, 'characters', 'boss', 'hansgrösse.png'))
        hans = self.texmap_parse(hans_sheet,
                                         1, 1, 1, 1, 64, 64, Sprite, 1, 1)
        gretel_sheet = Image.open(os.path.join(
            self.sprite_path, 'characters', 'boss', 'gretelgrösse.png'))
        gretel = self.texmap_parse(gretel_sheet,
                                           1, 1, 1, 1, 64, 64, Sprite, 1, 1)
        schabbs_sheet = Image.open(os.path.join(
            self.sprite_path, 'characters', 'boss', 'drschabbs.png'))
        schabbs = self.texmap_parse(schabbs_sheet,
                                            1, 1, 1, 1, 64, 64, Sprite, 1, 1)
        giftmacher_sheet = Image.open(os.path.join(
            self.sprite_path, 'characters', 'boss', 'giftmacher.png'))
        giftmacher = self.texmap_parse(giftmacher_sheet,
                                               1, 1, 1, 1, 64, 64, Sprite, 1, 1)
        fettgesicht_sheet = Image.open(os.path.join(
            self.sprite_path, 'characters', 'boss', 'fettgesicht.png'))
        fettgesicht = self.texmap_parse(fettgesicht_sheet,
                                                1, 1, 1, 1, 64, 64, Sprite, 1, 1)
        
        hitler_sheet = Image.open(os.path.join(
                    self.sprite_path, 'characters', 'boss', 'hitler.png'))
        hitler = self.texmap_parse(hitler_sheet,
                                           0, 0, 0, 0, 64, 64, Sprite)
        
        mechahitler_sheet = Image.open(os.path.join(
                    self.sprite_path, 'characters', 'boss', 'mechahitler.png'))
        mechahitler = self.texmap_parse(mechahitler_sheet,
                                                0, 0, 0, 0, 64, 64, Sprite)

        # adapt below
        self.adapt_bosses(hans, gretel,
                          schabbs, giftmacher, 
                          fettgesicht, hitler, mechahitler)

    def init_character_sprites(self):
        self.sprites["characters"] = {}
        self.init_character_sprite(
            'guard.png', 'guard', 0, 0, 1, 1, 64, 64, Sprite)
        self.init_character_sprite(
            'shepherd.png', 'shepherd', 0, 0, 1, 1, 64, 64, Sprite)
        self.init_character_sprite(
            'SS.png', 'SS', 1, 1, 1, 1, 64, 64, Sprite, 1, 1)
        self.init_character_sprite(
            'officer.png', 'officer', 1, 1, 1, 1, 64, 64, Sprite, 1, 1)
        self.init_character_sprite(
            'mutant.png', 'mutant', 1, 1, 1, 1, 64, 64, Sprite, 1, 1)
        self.init_character_sprite(
            'pacman.png', 'pacman-ghosts', 64, 0, 0, 0, 64, 64, Sprite, 0, 0)
        self.init_character_sprite(
            'fakehitler.png', 'fakehitler', 1, 0, 1, 0, 64, 64, Sprite, 0, 0)

        hs = list(self.sprites["characters"]["fakehitler"].values())
        self.sprites["characters"]["fakehitler"] = self.adapt_character_sprites(
            move_frames=hs[:3], move_frame_amount=3,
            death_frames=hs[7:13],
            attack_frames=hs[3:5], layout=[6, 6])
        self.sprites["projectiles"] = {}
        self.sprites["projectiles"]["fireballs"] = hs[5:7]

        ps = list(self.sprites["characters"]["pacman-ghosts"].values())

        ghosts = ["blinky", "pinky", "clyde", "inky"]
        for i, gn in enumerate(ghosts):
            self.sprites["characters"][gn] = self.adapt_character_sprites(
                move_frames=ps[i*2:(i+1)*2], move_frame_amount=2,
                death_frames=ps[i*2:(i+1)*2],
                attack_frames=ps[i*2:(i+1)*2], layout=[2, 5])

        # init bosses here
        self.init_boss_sprites()

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
