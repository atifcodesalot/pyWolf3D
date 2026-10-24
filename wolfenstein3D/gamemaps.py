
from wolfenstein3D.wolf.maps import WolfMap, WolfDifficulty
from wolfenstein3D.wolf.actors import *
from wolfenstein3D.wolf.assets import ASSET_MANAGER
from wolfenstein3D.wolf.game_objects import *
from wolfenstein3D.wolf import wolflogger
import os

SPRITES = ASSET_MANAGER.sprites

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
    # did not want to make a dataclass for entries
    global ACTOR_ENTRIES
    ACTOR_ENTRIES = {}
    starts = {108: WolfActorType.GUARD, 116: WolfActorType.OFFICER,
              126: WolfActorType.SCHUTZSTAFFEL, 134: WolfActorType.DOG}

    for start in starts:
        for i in range(3):
            for j in range(8):
                entry = start + i * 36 + j
                patrolling = j >= 4
                ACTOR_ENTRIES[start + i * 36 + j] = \
                    (starts[start],
                     WolfDifficulty(i+1),
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
                 WolfDifficulty(i+1),
                 patrolling,
                 (entry - mutant_start) % 4)

    # an actor is "trivial" if it has no orientation,
    # and is not a boss
    trivial_actors_types = [WolfActorType.FAKEHITLER, 
                            WolfActorType.BLINKY, WolfActorType.PINKY,
                            WolfActorType.INKY, WolfActorType.CLYDE]

    for act_type in trivial_actors_types:
        ACTOR_ENTRIES[act_type.value] = (act_type,
                                         WolfDifficulty(0),
                                         False,
                                         0)


init_actor_entries()



def get_n_bytes_LI(start, n, data: bytearray):
    '''return n bytes little endian from data'''
    result = 0
    for i in range(n):
        result <<= 8
        result |= data[start + (n - 1 - i)]
    return result


def get_word_BI(start, data: bytearray):
    return data[start] << 8 | data[start+1]


class GameMapsParser:
    def __init__(self, mapheader: bytearray, maptemp: bytearray, level_count=10, carmackized=False):
        self.mapheader = mapheader
        self.maptemp = maptemp
        self.get_magic_marker()
        self.levels = level_count
        self.carmackized = carmackized
        self.parse()

    def parse(self):
        rlewdcmp = self.RLEW_decompress
        cardcmp = self.CARMACK_decompress
        dcmp = rlewdcmp if not self.carmackized else lambda d: rlewdcmp(
            cardcmp(d))
        self.level_offsets = [get_n_bytes_LI(
            2 + 4*i, 4, self.mapheader) for i in range(self.levels)]
        self.planes = [(dcmp(self.get_level_plane(i, 0)), dcmp(self.get_level_plane(i, 1)))
                       for i in range(self.levels)]

    def RLEW_decompress(self, plane):
        decompressed = []
        if self.carmackized:
            # skip the uncompressed size header
            i = 1
            #
            while i < len(plane):
                entry = plane[i]
                if entry == self.magic_marker:
                    repeat = plane[i + 1]
                    value = plane[i + 2]
                    decompressed += [value,] * repeat
                    i += 3
                    continue
                decompressed.append(entry)
                i += 1

        else:
            i = 2
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

    @staticmethod
    def CARMACK_decompress(plane):
        near, far = 0xA7, 0xA8
        special = [near, far]

        decompressed = []
        outi, ini = 0, 2  # skip the uncompressed size header for ini

        def set_word_out(start, BI=False):
            nonlocal decompressed, plane, outi
            def fetcher(s): return get_word_BI(
                s, plane) if BI else get_n_bytes_LI(s, 2, plane)
            decompressed.append(fetcher(start))
            outi += 1

        def repeat_word_out(di):
            nonlocal decompressed, outi
            decompressed.append(decompressed[di])
            outi += 1

        while ini < len(plane):
            byte = plane[ini]
            successor = plane[ini+1]
            if successor not in special:
                # ordinary data
                set_word_out(ini)
                ini += 2

            elif byte == 0:
                # escaped ordinary data
                set_word_out(ini+1, BI=True)
                ini += 3
            else:
                # near or far pointer
                nearp = successor == near
                repeat = byte
                start = outi - plane[ini +
                                     2] if nearp else get_n_bytes_LI(ini + 2, 2, plane)
                inc = 3 if nearp else 4
                for i in range(repeat):
                    pointer = start + i
                    repeat_word_out(pointer)
                ini += inc

        return decompressed

    def get_level_header(self, level_i):
        pos = self.level_offsets[level_i]
        return self.maptemp[pos: pos + 38]

    def get_level_plane(self, level_i, plane_i) -> bytearray:
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
            if obj == 0x00D6:
                # hans grösse boss
                wolfmap.add_actor(WolfActorType.HANS, pos, [0, -1],
                                  WolfDifficulty.BABY, None)
            return
        _type, diff, patrol, look_i = ACTOR_ENTRIES[obj]

        wolfmap.add_actor(_type, pos,
                          self.actor_orientation[look_i],
                          act_diff=diff, patrol=patrol)

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
                        wolfmap.add_sprite(
                            SPRITES["characters"]["guard"][44], pos)

        return wolfmap


MAPS_PATH = os.path.join(ASSET_MANAGER.assets_path, "maps")


class GameMapsLoader:
    VALID_EXT = [".wl1", ".wl6"]

    def __init__(self, maps_path=MAPS_PATH):
        self.maps_path = maps_path
        self.init_map_filenames()

    def init_map_filenames(self):
        self.map_files = []
        for entry in os.scandir(self.maps_path):
            for ext in self.VALID_EXT:
                if entry.name.lower().endswith(ext):
                    self.map_files.append(entry.path)

    def get_shareware_maps(self):
        shareware_maphead = [
            fn for fn in self.map_files if fn.lower().endswith("maphead.wl1")][0]
        shareware_maptemp = [
            fn for fn in self.map_files if fn.lower().endswith("maptemp.wl1")][0]
        maphead = open(shareware_maphead, "rb")
        maptemp = open(shareware_maptemp, "rb")
        parser = GameMapsParser(maphead.read(), maptemp.read(), level_count=10)
        adaptor = GameMapsAdaptor(parser)

        for level_i in range(10):
            map_ = adaptor.to_wolfmap(level_i)
            yield map_

        maphead.close()
        maptemp.close()

    def wl6_maps_present(self):
        low_files = [os.path.basename(fn.lower()) for fn in self.map_files]
        gamemaps6_present = "gamemaps.wl6" in low_files
        maphead6_present = "maphead.wl6" in low_files
        return gamemaps6_present and maphead6_present

    # requires wl6 files
    def get_wl6_maps(self):
        gamemaps6 = [
            fn for fn in self.map_files if fn.lower().endswith("gamemaps.wl6")][0]
        maphead6 = [
            fn for fn in self.map_files if fn.lower().endswith("maphead.wl6")][0]
        gamemaps6 = open(gamemaps6, "rb")
        maphead6 = open(maphead6, "rb")
        parser = GameMapsParser(
            maphead6.read(), gamemaps6.read(), level_count=60, carmackized=True)
        adaptor = GameMapsAdaptor(parser)

        for level_i in range(60):
            map_ = adaptor.to_wolfmap(level_i)
            yield map_

        maphead6.close()
        gamemaps6.close()
