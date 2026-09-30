
from enum import Enum
from .assets import SPRITES

class WolfWeapon(Enum):
    KNIFE = 0
    PISTOL = 1
    MP4 = 2
    MINIGUN = 3

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
    WolfItem.FIRSTAIDKIT: lambda p: p.regain_health(75),
    WolfItem.CHAINGUN: lambda p: p.switch_weapon(WolfWeapon.MINIGUN),
    WolfItem.MACHINEGUN: lambda p: p.switch_weapon(WolfWeapon.MP4),
    WolfItem.AMMUNITION: lambda p: p.get_ammo(),
    WolfItem.GOLDKEY: None, # will add key functionality later
    WolfItem.SILVERKEY: None, #
    WolfItem.CROSS: lambda p: p.get_money(),
    WolfItem.CHALICE: lambda p: p.get_money(),
    WolfItem.TREASURECHEST: lambda p: p.get_money(),
    WolfItem.CROWN: lambda p: p.get_money(),
    
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
            
class WolfActorType(Enum):
    GUARD = 0
    DOG = 1
    SCHUTZSTAFFEL = 2
    MUTANT = 3


WEAPON_MULTIPLIER = 1.2
