
from enum import Enum


ITEM_SPRITES_MAPPING = {
    29:  6,  # Dog food
    43: 20,  # Gold key
    44: 21,  # Silver key
    47: 24,  # Food
    48: 25,  # First-aid kit
    49: 26,  # Ammunition
    50: 27,  # Machine gun
    51: 28,  # Chaingun
    52: 29,  # Cross
    53: 30,  # Chalice
    54: 31,  # Treasure chest
    55: 32,  # Crown
    56: 33,  # Extra life
    57: 34,  # Bloody remains
    61: 38,  # Blood pool
}

TREASURE_ITEMS = [
    52,
    53,
    54,
    55,
]

HEALTH_ITEMS = [
    29,
    47,
    48,
    57,
    61
]

WEAPON_ITEMS = [50, 51]

DECORATION_SPRITES_MAPPING = {
    23:  0,  # Water puddle
    24:  1,  # Green barrel
    25:  2,  # Table with chairs
    26:  3,  # Floor lamp
    27:  4,  # Chandelier
    28:  5,  # Hanging skeleton
    30:  7,  # Pillar
    31:  8,  # Potted tree
    32:  9,  # Skeleton on floor
    33: 10,  # Sink
    34: 11,  # Potted plant
    35: 12,  # Urn
    36: 13,  # Empty table
    37: 14,  # Ceiling light
    38: 15,  # Hanging kitchen utensils
    39: 16,  # Armour
    40: 17,  # Empty hanging cage
    41: 18,  # Hanging cage with skeleton
    42: 19,  # Skeleton remains
    45: 22,  # Bed
    46: 23,  # Basket
    58: 35,  # Wooden barrel
    59: 36,  # Well with water
    60: 37,  # Empty well
    62: 39,  # Flag
    63: 40,  # "Call Apogee" slot — blank in our sheet
    64: 41,  # Debris 1
    65: 42,  # Debris 2
    66: 43,  # Debris 3
    67: 44,  # Hanging pots
    68: 45,  # Stove
    69: 46,  # Spear rack
    70: 47,  # Vines
}

BLOCKING_SPRITES = [
    1,   # Green barrel
    2,   # Table with chairs
    3,   # Floor lamp
    5,   # Hanging skeleton
    7,   # Pillar
    8,   # Potted tree
    10,  # Sink
    11,  # Potted plant
    12,  # Urn
    13,  # Empty table
    16,  # Armour
    17,  # Empty hanging cage
    18,  # Hanging cage with skeleton
    22,  # Bed
    35,  # Wooden barrel
    36,  # Well with water
    37,  # Empty well
    39,  # Flag
    40,  # "Call Apogee" — blocks even if my sheet has it blank
    45,  # Stove
    46,  # Spear rack
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


WEAPON_MULTIPLIER = 1.2
