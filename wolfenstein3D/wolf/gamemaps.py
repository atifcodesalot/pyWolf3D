
from .maps import WolfMap, WolfDifficulty
from .actors import *
from .assets import SPRITES, ASSETS_PATH
from os import path
from .game_objects import *
from . import wolflogger
from .actors import WolfActorType

ID_TO_ATLAS = {
    1:  0,
    2:  2,
    3:  4,
    4:  6,
    5:  8,
    6: 10,
    7: 12,
    8: 14,
    9: 16,
    10: 18,
    11: 20,
    12: 22,
    13: 24,
    14: 26,
    15: 28,
    16: 30,
    17: 32,
    18: 34,
    19: 36,
    20: 38,
    21: 40,
    22: 42,
    23: 44,
    24: 46,
    25: 48,
    26: 50,
    27: 52,
    28: 54,
    29: 64,
    30: 66,
    31: 68,
    32: 70,
    33: 72,
    34: 74,
    35: 76,
    36: 78,
    37: 80,
    38: 82,
    39: 84,
    40: 86,
    41: 88,
    42: 90,
    43: 92,
    44: 94,
    45: 96,
    46: 98,
    47: 100,
    48: 102,
    49: 104,

    # Vertical doors
    90: 56,  # Regular
    92: 62,  # Gold
    94: 620,  # Silver
    100: 60,  # Elevator

    # Horizontal doors:
    91: 57,
    93: 63,
    95: 630,  # Silver
    97: 63,
    99: 63,
    101: 61,
}


def init_actor_entries():
    # entry: type, difficulty, patrolling (bool)
    global ACTOR_ENTRIES
    ACTOR_ENTRIES = {}
    starts = {108: WolfActorType.GUARD,
              126: WolfActorType.SCHUTZSTAFFEL, 134: WolfActorType.DOG}

    for start in starts:
        for i in range(3):
            for j in range(8):
                entry = start + i * 36 + j
                patrolling = j >= 4
                ACTOR_ENTRIES[start + i * 36 + j] = \
                    (starts[start],
                     WolfDifficulty(i),
                     patrolling, 
                     (entry-start) % 4)
    # mutants use 18 offset per difficulty level
    mutant_start = 216
    for i in range(3):
        for j in range(8):
            entry = start + i * 18 + j
            patrolling = j >= 4
            ACTOR_ENTRIES[mutant_start + i * 18 + j] = \
                (WolfActorType.MUTANT,
                 WolfDifficulty(i),
                 patrolling,
                 (entry - mutant_start) % 4)


init_actor_entries()

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
    actor_orientation = [[1, 0], [0, -1], [-1, 0], [0, 1]]
    PUSHWALL = 0x62
    PATROL = range(90, 98)

    def __init__(self, parser):
        self.parser = parser
        self.planes = self.parser.planes

    def add_actor(self, wolfmap, obj, pos):
        if obj not in ACTOR_ENTRIES:
            return
        _type, diff, patrol, look_i = ACTOR_ENTRIES[obj]

        wolfmap.add_actor(_type, pos,
                          self.actor_orientation[look_i],
                          difficulty=diff, patrol=patrol)

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
            walls[i] = [ID_TO_ATLAS.get(wall, wall) for wall in row]

        wolfmap = WolfMap(array=walls, wall_width=8,
                          difficulty=WolfDifficulty.DEATHINCARNATE,
                          nextmap=None, map_id=level_i)
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
            elif entry in WolfItem:
                self.add_item(wolfmap, entry, pos)
            elif entry in WolfDecoration:
                self.add_decoration(wolfmap, entry, pos)
            else:
                if entry == self.PUSHWALL:
                    wolfmap.add_pushwall(block_pos)
                elif entry in self.PATROL:
                    wolfmap.add_patrol(block_pos, entry)
                else:
                    if entry != 124:
                        self.add_actor(wolfmap, entry, pos)
                    else:
                        # add dead guard
                        wolfmap.add_sprite(SPRITES["characters"]["guard"][44], pos)

        wolfmap.init_snap = wolfmap.snapshot()
        return wolfmap


def get_shareware_maps():
    global SHAREWARE_MAPS
    maphead = open(path.join(ASSETS_PATH, "maps", "MAPHEAD.WL1"), "rb")
    maptemp = open(path.join(ASSETS_PATH, "maps", "MAPTEMP.WL1"), "rb")
    parser = GameMapsParser(maphead.read(), maptemp.read(), level_count=10)
    adaptor = GameMapsAdaptor(parser)
    SHAREWARE_MAPS = [adaptor.to_wolfmap(level_i) for level_i in range(10)]
    for i, map_ in enumerate(SHAREWARE_MAPS):
        if i == len(SHAREWARE_MAPS)-1:
            break
        map_.nextmap = SHAREWARE_MAPS[i+1]
    maphead.close()
    maptemp.close()


get_shareware_maps()
