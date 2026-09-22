
from .maps import WolfMap, WolfItem
from .actors import Actor
from .assets import SPRITES, ASSETS_PATH
from os import path
from .game_objects import *
from . import wolflogger


# return n bytes little endian from data
def get_n_bytes_LI(start, n, data: bytearray):
    result = 0
    for i in range(n):
        result <<= 8
        result |= data[start + (n - 1 - i)]
    return result


class GameMapsParser:
    def __init__(self, mapheader: bytearray, maptemp: bytearray, level_count=10):
        self.mapheader = mapheader
        self.maptemp = maptemp
        self.get_magic_marker()
        self.levels = level_count
        self.parse()

    def parse(self):
        dcmp = self.decompress
        self.level_offsets = [get_n_bytes_LI(
            2 + 4*i, 4, self.mapheader) for i in range(self.levels)]
        self.planes = [(dcmp(self.get_level_plane(i, 0)), dcmp(self.get_level_plane(i, 1)))
                       for i in range(self.levels)]

    def decompress(self, plane):
        decompressed = []
        # skip the uncompressed size header
        i = 2
        #
        while i < len(plane):
            entry = get_n_bytes_LI(i, 2, plane)
            if entry == self.magic_marker:
                repeat = get_n_bytes_LI(i + 2, 2, plane)
                value = get_n_bytes_LI(i + 4, 2, plane)
                decompressed += [value,] * repeat
                i += 6
                continue
            decompressed.append(entry)
            i += 2
        return decompressed

    def get_level_header(self, level_i):
        pos = self.level_offsets[level_i]
        return self.maptemp[pos: pos + 38]

    def get_level_plane(self, level_i, plane_i):
        header = self.get_level_header(level_i)
        plane_size = get_n_bytes_LI(12+2*plane_i, 2, header)
        offset = get_n_bytes_LI(plane_i * 4, 4, header)
        return self.maptemp[offset: offset + plane_size]

    def get_magic_marker(self):
        self.magic_marker = get_n_bytes_LI(0, 2, self.mapheader)

    
class GameMapsAdaptor:
    obj_lookdir = {19: [0, -1], 20: [1, 0], 21: [0, 1], 22: [-1, 0]}
    def __init__(self, parser):
        self.parser = parser
        self.planes = self.parser.planes
        
    def add_item_object(self, wolfmap, item, sprite_src, pos):
        witem = WolfItem(wolfmap, sprite_src,
                            pos, pickcallback=None)
        if item in HEALTH_ITEMS:
            witem.pickcallback = lambda p: p.regain_health(20)
        elif item in TREASURE_ITEMS:
            witem.pickcallback = lambda p: p.get_money()
        elif item in WEAPON_ITEMS:
            witem.pickcallback = lambda p: p.get_money()
        elif item == 49:
            witem.pickcallback = lambda p: p.get_ammo()
        wolfmap.add_item(witem)
        
    def add_actor(self, wolfmap, obj, pos):
        # todo: implement all character sprites
        # add guard sprites
        if obj in range(108, 116):
            wolfmap.add_actor(
                Actor(pos, [0, 1], "guard", sprites=SPRITES["characters"]["guard"]))
        elif obj == 124:
            # add dead guard
            wolfmap.add_sprite(SPRITES["characters"]["guard"][44], pos)
            
    def add_player(self, wolfmap, obj, pos):
        wolfmap.init_pos = pos
        wolfmap.init_look = self.obj_lookdir[obj]
    
    def to_wolfmap(self, level_i) -> WolfMap:
        walls = self.planes[level_i][0]
        sprites = self.planes[level_i][1]
        walls = [walls[i*64: (i+1)*64] for i in range(64)]
        for i, row in enumerate(walls):
            walls[i] = [WALL_TEXTURE_MAPPING.get(wall, -1) + 1 for wall in row]

        wolfmap = WolfMap(array=walls, wall_width=12)
        ww = wolfmap.wall_width

        for i, obj in enumerate(sprites):
            if not obj:
                continue
            pos = (i % 64)*ww + ww // 2, (i // 64)*ww + ww // 2
            if obj in [19, 20, 21, 22]:
                self.add_player(wolfmap, obj, pos)
            is_item = False
            if obj in ITEM_SPRITES_MAPPING:
                myindex = ITEM_SPRITES_MAPPING[obj]
                is_item = True
            elif obj in DECORATION_SPRITES_MAPPING:
                myindex = DECORATION_SPRITES_MAPPING[obj]
            else:
                self.add_actor(wolfmap, obj, pos)
                continue

            if myindex not in SPRITES["objects"]:
                wolflogger.warning(f"entry {obj} not in known sprites dict.")
                continue

            sprite_src = SPRITES["objects"][myindex]
            sprite_src.blocking = myindex in BLOCKING_SPRITES
            if is_item:
                self.add_item_object(wolfmap, obj, sprite_src, pos)
            else:
                # it is a decoration object
                wolfmap.add_sprite(sprite_src, pos)

        return wolfmap


def get_shareware_maps():
    global SHAREWARE_MAPS
    maphead = open(path.join(ASSETS_PATH, "maps", "MAPHEAD.WL1"), "rb")
    maptemp = open(path.join(ASSETS_PATH, "maps", "MAPTEMP.WL1"), "rb")
    parser = GameMapsParser(maphead.read(), maptemp.read(), level_count=10)
    adaptor = GameMapsAdaptor(parser)
    SHAREWARE_MAPS = [adaptor.to_wolfmap(i) for i in range(10)]
    maphead.close()
    maptemp.close()


get_shareware_maps()
