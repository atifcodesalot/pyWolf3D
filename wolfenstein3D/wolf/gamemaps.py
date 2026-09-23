
from .maps import WolfMap
from .actors import *
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

    def add_actor(self, wolfmap, obj, pos):
        # todo: implement all character sprites
        # add guard sprites
        if obj in range(108, 116):
            wolfmap.add_actor(Guard(wolfmap, pos, [0, 1]))
        elif obj in range(126, 135):
            wolfmap.add_actor(SS(wolfmap, pos, [0, 1]))
        elif obj in range(134, 142):
            wolfmap.add_actor(Shepherd(wolfmap, pos, [0, 1]))
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

        for i, entry in enumerate(sprites):
            if not entry:
                continue
            pos = (i % 64)*ww + ww // 2, (i // 64)*ww + ww // 2
            if entry in [19, 20, 21, 22]:
                self.add_player(wolfmap, entry, pos)
            is_item = False
            if entry in WolfItem:
                myindex = ITEM_SPRITES_MAPPING[WolfItem(entry)]
                is_item = True
            elif entry in WolfDecoration:
                myindex = DECORATION_SPRITES_MAPPING[WolfDecoration(entry)]
            else:
                self.add_actor(wolfmap, entry, pos)
                continue

            if myindex not in SPRITES["objects"]:
                wolflogger.warning(
                    f"entry {entry} not in available sprites dict.")
                continue

            if is_item:
                wolfmap.add_item(WolfItem(entry), pos)
            else:
                # it is a decoration object
                sprite_src = SPRITES["objects"][myindex]
                sprite_src.blocking = WolfDecoration(entry) in BLOCKING_SPRITES
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
