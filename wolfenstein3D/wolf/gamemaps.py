
from .maps import WolfMap
from .actors import *
from .assets import SPRITES, ASSETS_PATH
from os import path
from .game_objects import *
from . import wolflogger
from .actors import WolfActorType

WALL_TEXTURE_MAPPING = {
    # DOS GAMEMAPS ID : my atlas index

    0x00: 0,   # renderer subtracts 1 from tiles, -1 is for empty.
    0x01: 1,   # grey stone
    0x02: 1,   # grey stone
    0x03: 3,   # grey stone + flag
    0x04: 4,   # grey stone + Hitler portrait
    0x05: 10,  # blue stone + cell door
    0x06: 2,   # grey stone + eagle arch
    0x07: 10,  # cell door + skeleton -> collapsed to cell texture
    0x08: 9,   # blue stone
    0x09: 9,   # blue stone

    0x0A: 6,   # wood + eagle
    0x0B: 7,   # wood + Hitler portrait
    0x0C: 5,   # plain wood
    0x0D: 35,  # elevator entrance / closest Jaguar equivalent
    0x0E: 20,  # steel + Achtung/Verboten -> Jaguar decorated steel
    0x0F: 19,  # plain steel

    0x10: 17,  # landscape -- DAY
               # atlas 17 is the NIGHT variant

    0x11: 11,  # red brick
    0x12: 14,  # wreath/emblem wall
    # 0x13     # purple/green -- no direct Jaguar equivalent
    0x14: 12,  # red brick + eagle tapestry

    0x15: 15,  # elevator interior / rail
    0x16: 16,  # elevator interior / control panel
    0x17: 8,   # wood + iron cross
    0x18: 21,  # moss/slime stone
    # 0x19     # pink/green -- no direct Jaguar equivalent
    0x1A: 22,  # second moss/slime stone
    0x1B: 1,   # grey stone
    0x1C: 20,  # grey stone + Achtung/Verboten -> closest equivalent

    0x1D: 27,  # brown cave
    0x1E: 28,  # brown cave + blood
    0x1F: 28,  # brown cave + blood (collapsed)
    0x20: 28,  # brown cave + blood (collapsed)

    # 0x21     # Hitler stained glass -- no direct Jaguar equivalent

    0x22: 24,  # blue brick + skulls
    0x23: 31,  # grey brick
    0x24: 24,  # blue brick + swastikas -- Jaguar combines the family
    0x25: 31,  # grey brick + hole -> plain grey brick fallback
    0x26: 13,  # red/grey/brown wall
    0x27: 31,  # grey brick + crack -> plain grey brick fallback
    0x28: 23,  # plain blue brick
    0x29: 20,  # blue stone + Verboten -> closest decorated steel

    0x2A: 30,  # brown tiles
    0x2B: 31,  # grey brick + map -> plain grey brick fallback
    0x2C: 29,  # orange stone
    0x2D: 29,  # orange stone
    0x2E: 30,  # brown tiles
    0x2F: 30,  # brown tiles + banner -> brown tiles fallback
    0x30: 5,   # orange panel on wood -> wood fallback
    0x31: 4,   # grey brick + Hitler -> portrait fallback

    # Doors
    0x5A: 32,  # regular door, orientation A
    0x5B: (31 << 1) + 1,  # regular door, orientation B
    0x5C: 33,  # gold-key door
    0x5D: 33,
    0x5E: 34,  # silver-key door
    0x5F: 34,

    0x64: 35,  # elevator door, orientation A
    0x65: (34 << 1) + 1, # elevator door, orientation A
}


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
    entry_lookdir = {19: [0, -1], 20: [1, 0], 21: [0, 1], 22: [-1, 0]}
    PUSHWALL = 0x62

    def __init__(self, parser):
        self.parser = parser
        self.planes = self.parser.planes

    def add_actor(self, wolfmap, obj, pos):
        # todo: implement all character sprites
        if obj in range(108, 116):
            wolfmap.add_actor(WolfActorType.GUARD, pos, [0, 1])
        elif obj in range(126, 135):
           wolfmap.add_actor(WolfActorType.SCHUTZSTAFFEL, pos, [0, 1])
        elif obj in range(134, 142):
            wolfmap.add_actor(WolfActorType.DOG, pos, [0, 1])
        elif obj == 124:
            # add dead guard
            wolfmap.add_sprite(SPRITES["characters"]["guard"][44], pos)

    def add_player(self, wolfmap, obj, pos):
        wolfmap.init_pos = list(pos)
        wolfmap.init_look = self.entry_lookdir[obj]

    def add_decoration(self, wolfmap, obj, pos):
        myindex = DECORATION_SPRITES_MAPPING[WolfDecoration(obj)]
        if myindex not in SPRITES["objects"]:
            wolflogger.warning(
                f"entry {obj} not in available sprites dict.")
            return
        sprite_src = SPRITES["objects"][myindex]
        sprite_src.blocking = WolfDecoration(obj) in BLOCKING_SPRITES
        wolfmap.add_sprite(sprite_src, pos)

    def add_item(self, wolfmap, obj, pos):
        wolfmap.add_item(WolfItem(obj), pos)
        myindex = ITEM_SPRITES_MAPPING[WolfItem(obj)]
        if myindex not in SPRITES["objects"]:
            wolflogger.warning(
                f"entry {obj} not in available sprites dict.")
            return

    def to_wolfmap(self, level_i) -> WolfMap:
        walls = self.planes[level_i][0]
        walls = [walls[i*64: (i+1)*64] for i in range(64)]
        for i, row in enumerate(walls):
            walls[i] = [WALL_TEXTURE_MAPPING.get(wall, 0) for wall in row]

        wolfmap = WolfMap(array=walls, wall_width=8)
        ww = wolfmap.wall_width

        # add sprites, items, pushwalls, doors
        sprite_plane = self.planes[level_i][1]
        for i, entry in enumerate(sprite_plane):
            if not entry:
                continue
            pos = (i % 64)*ww + ww // 2, (i // 64)*ww + ww // 2
            block_pos = (i % 64), (i // 64)
            if entry in self.entry_lookdir:
                self.add_player(wolfmap, entry, pos)
            if entry in WolfItem:
                self.add_item(wolfmap, entry, pos)
            elif entry in WolfDecoration:
                self.add_decoration(wolfmap, entry, pos)
            else:
                if entry == self.PUSHWALL:
                    wolfmap.add_pushwall(block_pos)
                    continue
                self.add_actor(wolfmap, entry, pos)
                continue

        wolfmap.init_snap = wolfmap.snapshot()
        return wolfmap



def get_shareware_maps():
    global SHAREWARE_MAPS
    maphead = open(path.join(ASSETS_PATH, "maps", "MAPHEAD.WL1"), "rb")
    maptemp = open(path.join(ASSETS_PATH, "maps", "MAPTEMP.WL1"), "rb")
    parser = GameMapsParser(maphead.read(), maptemp.read(), level_count=10)
    adaptor = GameMapsAdaptor(parser)
    SHAREWARE_MAPS = [adaptor.to_wolfmap(level_i) for level_i in range(10)]
    maphead.close()
    maptemp.close()


get_shareware_maps()
