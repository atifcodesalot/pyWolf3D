
from wolfenstein3D.wolf.assets import SPRITES, SOUNDS
from enum import Enum


class WolfWeapon(Enum):
    KNIFE = 0
    PISTOL = 1
    MP4 = 2
    MINIGUN = 3


WEAPON_SOUND = {
    WolfWeapon.KNIFE: None,
    WolfWeapon.PISTOL: "ATKPISTOLSND.WAV",
    WolfWeapon.MP4: "ATKMACHINEGUNSND.WAV",
    WolfWeapon.MINIGUN: "ATKGATLINGSND.WAV"
}


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
    MEDKIT = 48
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
    WolfItem.DOGFOOD:  6,  
    WolfItem.GOLDKEY: 20, 
    WolfItem.SILVERKEY: 21,  
    WolfItem.FOOD: 24, 
    WolfItem.MEDKIT: 25,  
    WolfItem.AMMUNITION: 26,  
    WolfItem.MACHINEGUN: 27, 
    WolfItem.CHAINGUN: 28,  
    WolfItem.CROSS: 29,  
    WolfItem.CHALICE: 30,  
    WolfItem.TREASURECHEST: 31, 
    WolfItem.CROWN: 32,  
    WolfItem.EXTRALIFE: 33, 
    WolfItem.BLOODYREMAINS: 34,  
    WolfItem.BLOODPOOL: 38, 
}

ITEM_EFFECT = {
    WolfItem.DOGFOOD: lambda p: p.regain_health(10),
    WolfItem.FOOD: lambda p: p.regain_health(30),
    WolfItem.MEDKIT: lambda p: p.regain_health(50),
    WolfItem.CHAINGUN: lambda p: p.acquire_weapon(WolfWeapon.MINIGUN),
    WolfItem.MACHINEGUN: lambda p: p.acquire_weapon(WolfWeapon.MP4),
    WolfItem.AMMUNITION: lambda p: p.get_ammo(),
    WolfItem.GOLDKEY: lambda p: setattr(p, "has_gold_key", True),
    WolfItem.SILVERKEY: lambda p: setattr(p, "has_silver_key", True),
    WolfItem.CROSS: lambda p: p.get_money(),
    WolfItem.CHALICE: lambda p: p.get_money(),
    WolfItem.TREASURECHEST: lambda p: p.get_money(),
    WolfItem.CROWN: lambda p: p.get_money(),
    WolfItem.EXTRALIFE: lambda p: p._1up(),
    WolfItem.BLOODPOOL: lambda p: p.regain_health(5)
}

ITEM_SOUND = {
    WolfItem.DOGFOOD: SOUNDS["pickup"]["ALFOODUP.wav"],
    WolfItem.GOLDKEY: SOUNDS["pickup"]["ALGETKEY.wav"],
    WolfItem.SILVERKEY: SOUNDS["pickup"]["ALGETKEY.wav"],
    WolfItem.FOOD: SOUNDS["pickup"]["ALFOODUP.wav"],
    WolfItem.MEDKIT: SOUNDS["pickup"]["ALMEDIUP.wav"],
    WolfItem.AMMUNITION: SOUNDS["pickup"]["ALAMMOUP.wav"],
    WolfItem.MACHINEGUN: None,
    WolfItem.CHAINGUN: None,
    WolfItem.CROSS: SOUNDS["pickup"]["ALBONUS1.wav"],
    WolfItem.CHALICE: SOUNDS["pickup"]["ALBONUS2.wav"],
    WolfItem.TREASURECHEST: SOUNDS["pickup"]["ALBONUS3.wav"],
    WolfItem.CROWN: SOUNDS["pickup"]["ALBONUS4.wav"],
    WolfItem.EXTRALIFE: SOUNDS["pickup"]["ALBNS1UP.wav"],
    WolfItem.BLOODYREMAINS: None,
    WolfItem.BLOODPOOL: None
}

TREASURE_ITEMS = [
    WolfItem.CROSS,
    WolfItem.CHALICE,
    WolfItem.TREASURECHEST,
    WolfItem.CROWN,
]

HEALTH_ITEMS = [
    WolfItem.MEDKIT,
    WolfItem.FOOD,
    WolfItem.BLOODYREMAINS,
    WolfItem.BLOODPOOL
]

WEAPON_ITEMS = [
    WolfItem.MACHINEGUN,
    WolfItem.CHAINGUN
]


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


class WolfItemObj:
    def __init__(self, map_, item: WolfItem, pos, pickup_callback):
        self.map = map_
        self.item = item
        self.pyindex = ITEM_SPRITES_MAPPING[item]
        self.sprite = SPRITES["objects"][self.pyindex].copy(pos)
        self.sprite.blocking = item in BLOCKING_SPRITES
        self.pos = self.map.to_block_pos(*pos)
        self.pickup_callback = pickup_callback

        self.is_health_item = item in HEALTH_ITEMS
        self.is_weap_item = item in WEAPON_ITEMS

        self.pickupsnd = ITEM_SOUND[item]

    def pickup_condition(self, player):
        if self.is_health_item:
            if self.item is WolfItem.BLOODPOOL:
                return player.health < 20
            return player.health < 100
        elif self.item is WolfItem.AMMUNITION:
            return player.ammo < 100
        return True

    def affect(self, game_ctx):
        if callable(self.pickup_callback):
            self.pickup_callback(game_ctx.player)

    def pickup(self, game_ctx):
        if self.pickupsnd is not None:
            game_ctx.schedule_sound_effect(self.pickupsnd, None, 1, repeat=False)
        self.affect(game_ctx)
        glow = (0, 1, 2) if self.is_health_item or self.is_weap_item else (0, 1)
        game_ctx.game_renderer.begin_glow(glow, 22)


class WolfActorType(Enum):
    GUARD = 108
    OFFICER = 116
    SCHUTZSTAFFEL = 126
    DOG = 134
    HANS = 214
    MUTANT = 216
    


WEAPON_MULTIPLIER = 1.1
