
from enum import Enum
from .assets import SPRITES

class WolfDecoration(Enum):
    WATERPUDDLE = 23
    GREENBARREL = 24
    TABLEWITHCHAIRS = 25
    FLOORLAMP = 26
    CHANDELIER = 27
    HANGINGSKELETON = 28
    PILLAR = 30
    POTTEDTREE = 31
    SINK = 32
    POTTEDPLANT = 34
    URN = 35
    EMPTYTABLE = 36
    CEILINGLIGHT = 37
    HANGINGKITCHENUTENSILS = 38
    ARMOUR = 39
    EMPTYHANGINGCAGE = 40
    HANGINGCAGEWITHSKELETON = 41
    SKELETONREMAINS = 42
    BED = 45
    BASKET = 46
    WOODENBARREL = 58
    WELLWITHWATER = 59
    EMPTYWELL = 60
    FLAG = 62
    CALLAPOGEE = 63
    DEBRIS1 = 64
    DEBRIS2 = 65
    DEBRIS3 = 66
    HANGINGPOTS = 67
    STOVE = 68
    SPEARRACK = 69
    VINES = 70

class WolfItem(Enum):
    DOGFOOD = 29
    GOLDKEY = 43
    SILVERKEY = 44
    FOOD = 47
    FIRSTAIDKIT = 48
    AMMUNITION = 49
    MACHINEGUN = 50
    CHAINGUN = 51
    CROSS = 52
    CHALICE = 53
    TREASURECHEST = 54
    CROWN = 55
    EXTRALIFE = 56
    BLOODYREMAINS = 57
    BLOODPOOL = 61

ITEM_SPRITES_MAPPING = {
    WolfItem.DOGFOOD:  6,  # Dog food
    WolfItem.GOLDKEY: 20,  # Gold key
    WolfItem.SILVERKEY: 21,  # Silver key
    WolfItem.FOOD: 24,  # Food
    WolfItem.FIRSTAIDKIT: 25,  # First-aid kit
    WolfItem.AMMUNITION: 26,  # Ammunition
    WolfItem.MACHINEGUN: 27,  # Machine gun
    WolfItem.CHAINGUN: 28,  # Chaingun
    WolfItem.CROSS: 29,  # Cross
    WolfItem.CHALICE: 30,  # Chalice
    WolfItem.TREASURECHEST: 31,  # Treasure chest
    WolfItem.CROWN: 32,  # Crown
    WolfItem.EXTRALIFE: 33,  # Extra life
    WolfItem.BLOODYREMAINS: 34,  # Bloody remains
    WolfItem.BLOODPOOL: 38,  # Blood pool
}

ITEM_AFFECT = {
    WolfItem.DOGFOOD: lambda p: p.regain_health(20),
    WolfItem.FOOD: lambda p: p.regain_health(50),
    WolfItem.FIRSTAIDKIT: lambda p: p.regain_health(75)
    
}

TREASURE_ITEMS = [
    WolfItem.CROSS,
    WolfItem.CHALICE,
    WolfItem.TREASURECHEST,
    WolfItem.CROWN,
]

HEALTH_ITEMS = [
    WolfItem.FIRSTAIDKIT,
    WolfItem.FOOD,
    WolfItem.BLOODYREMAINS,
    WolfItem.BLOODPOOL
]

WEAPON_ITEMS = [50, 51]

DECORATION_SPRITES_MAPPING = dict((i, i.value - 23) for i in WolfDecoration)

BLOCKING_SPRITES = [
    WolfDecoration.GREENBARREL,   
    WolfDecoration.TABLEWITHCHAIRS,   
    WolfDecoration.FLOORLAMP,  
    WolfDecoration.HANGINGSKELETON,   
    WolfDecoration.PILLAR,  
    WolfDecoration.POTTEDTREE,
    WolfDecoration.SINK,  
    WolfDecoration.POTTEDPLANT,  
    WolfDecoration.URN,  
    WolfDecoration.EMPTYTABLE,  
    WolfDecoration.ARMOUR,  
    WolfDecoration.EMPTYHANGINGCAGE,  
    WolfDecoration.HANGINGCAGEWITHSKELETON,  
    WolfDecoration.BED,  
    WolfDecoration.WOODENBARREL,  
    WolfDecoration.WELLWITHWATER,  
    WolfDecoration.EMPTYWELL,  
    WolfDecoration.FLAG, 
    WolfDecoration.CALLAPOGEE,
    WolfDecoration.STOVE, 
    WolfDecoration.SPEARRACK,  
]

OBJECT_SPRITES = set(list(ITEM_SPRITES_MAPPING.values()) +
                     list(DECORATION_SPRITES_MAPPING.values()))

WALL_TEXTURE_MAPPING = {
    # DOS GAMEMAPS ID : my atlas index

    0x00: -1,   # renderer subtracts 1 from tiles, -1 is for empty.
    0x01: 0,   # grey stone
    0x02: 0,   # grey stone
    0x03: 2,   # grey stone + flag
    0x04: 3,   # grey stone + Hitler portrait
    0x05: 9,   # blue stone + cell door
    0x06: 1,   # grey stone + eagle arch
    0x07: 9,   # cell door + skeleton -> collapsed to cell texture
    0x08: 8,   # blue stone
    0x09: 8,   # blue stone

    0x0A: 5,   # wood + eagle
    0x0B: 6,   # wood + Hitler portrait
    0x0C: 4,   # plain wood
    0x0D: 34,  # elevator entrance / closest Jaguar equivalent
    0x0E: 19,  # steel + Achtung/Verboten -> Jaguar decorated steel
    0x0F: 18,  # plain steel

    0x10: 16,  # landscape -- DAY
               # atlas 17 is the NIGHT variant

    0x11: 10,  # red brick
    0x12: 13,  # wreath/emblem wall
    # 0x13      # purple/green -- no direct Jaguar equivalent
    0x14: 11,  # red brick + eagle tapestry

    0x15: 14,  # elevator interior / rail
    0x16: 15,  # elevator interior / control panel
    0x17: 7,   # wood + iron cross
    0x18: 20,  # moss/slime stone
    # 0x19      # pink/green -- no direct Jaguar equivalent
    0x1A: 21,  # second moss/slime stone
    0x1B: 0,   # grey stone
    0x1C: 19,  # grey stone + Achtung/Verboten -> closest equivalent

    0x1D: 26,  # brown cave
    0x1E: 27,  # brown cave + blood
    0x1F: 27,  # brown cave + blood (collapsed)
    0x20: 27,  # brown cave + blood (collapsed)

    # 0x21      # Hitler stained glass -- no direct Jaguar equivalent

    0x22: 23,  # blue brick + skulls
    0x23: 30,  # grey brick
    0x24: 23,  # blue brick + swastikas -- Jaguar combines the family
    0x25: 30,  # grey brick + hole -> plain grey brick fallback
    0x26: 12,  # red/grey/brown wall
    0x27: 30,  # grey brick + crack -> plain grey brick fallback
    0x28: 22,  # plain blue brick
    0x29: 19,  # blue stone + Verboten -> closest decorated steel

    0x2A: 29,  # brown tiles
    0x2B: 30,  # grey brick + map -> plain grey brick fallback
    0x2C: 28,  # orange stone
    0x2D: 28,  # orange stone
    0x2E: 29,  # brown tiles
    0x2F: 29,  # brown tiles + banner -> brown tiles fallback
    0x30: 4,   # orange panel on wood -> wood fallback
    0x31: 3,   # grey brick + Hitler -> portrait fallback

    # Doors
    0x5A: 31,  # regular door, orientation A
    0x5B: 31 << 1,  # regular door, orientation B
    0x5C: 32,  # gold-key door
    0x5D: 32,
    0x5E: 33,  # silver-key door
    0x5F: 33,

    0x64: 34,  # elevator door
    0x65: 34,
}


class WolfWeapon(Enum):
    KNIFE = 0
    PISTOL = 1
    MP4 = 2
    MINIGUN = 3
    
class MapItem:
    def __init__(self, map_, item: WolfItem, pos, pickcallback):
        self.map = map_
        self.pyindex = ITEM_SPRITES_MAPPING[item]
        self.sprite = SPRITES["objects"][self.pyindex].copy(pos)
        self.sprite.blocking = item in BLOCKING_SPRITES
        self.pos = self.map.to_block_pos(*pos)
        self.pickcallback = pickcallback

    def affect(self, player):
        if callable(self.pickcallback):
            self.pickcallback(player)


WEAPON_MULTIPLIER = 1.2
