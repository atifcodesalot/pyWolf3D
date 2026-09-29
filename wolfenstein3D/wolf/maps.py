
from raycaster.sprites import Sprite
from raycaster.aux_math import plain_dot, plain_add
from .game_objects import *
from .assets import SPRITES


class WolfDoor:
    SLIDE = 0.02

    def __init__(self, pos, opening: float, horizontal=True):
        self.pos = pos
        self.opening = opening
        self.open = opening == 1
        self.horiz = horizontal
        self.is_opening = False
        self.is_closing = False

    def is_open(self):
        return self.openning == 1

    def slide_open(self):
        self.opening = max(self.opening - self.SLIDE, 0)

    def slide_close(self):
        self.opening = min(self.opening + self.SLIDE, 1)

    def begin_opening(self):
        self.is_opening = True
        self.is_closing = False

    def begin_closing(self):
        self.is_closing = True


class WolfPushWall:
    SLIDE = 0.01
    ATOL = 1e-10

    def __init__(self, cell, pos, offset=0):
        self.cell = cell
        self.pos = pos
        self.offset = offset
        self.sliding_vert = 0
        self.sliding = False
        self.slid = False

    def begin_sliding(self, dir):
        if self.slid:
            return
        self.sliding = True
        self.sliding_dir = dir
        self.sliding_vert = (plain_dot(self.sliding_dir, (0, 1)) != 0).real
        self.sliding_sign = sum(self.sliding_dir)

    def slide_open(self, wolfmap):
        self.offset = min(self.offset + self.SLIDE, 2)
        if (self.ATOL > self.offset % 1 > -self.ATOL):
            adjpos = plain_add(self.pos, self.sliding_dir)
            adjpos = (int(adjpos[0]), int(adjpos[1]))
            # unoccupy current cell
            wolfmap.raw[self.pos[1]][self.pos[0]] = 0
            # occupy adjacent cell
            wolfmap.raw[adjpos[1]][adjpos[0]] = self.cell
            del wolfmap.pushwalls[self.pos]
            
            self.pos = adjpos
            wolfmap.pushwalls[self.pos] = self
            if self.offset == 2:
                self.sliding = False
                self.slid = True
                return


# map class,
# 0: empty, nonzero: wall with texture
# DOOR has door tile numbers
# contains actors, items, sprites to render etc.
class WolfMap:
    DOOR = [0x1f + 1, (0x1f << 1) + 1, 0x22 + 1, (0x22 << 1) + 1]
    HORIZ_DOOR = [(0x1f << 1) + 1, (0x22 << 1) + 1]

    def __init__(self, size=(64, 64), array=None,
                 wall_width=20, init_pos=(0, 0), init_look_dir=[1, 0]):
        self.size = size
        self.doors = {}
        if array is None:
            self.construct_map()
        else:
            self.raw = array
            self.init_doors()

        self.wall_width = wall_width
        self.init_pos = init_pos
        self.init_look = init_look_dir

        self.abs_size = self.size[0] * \
            self.wall_width, self.size[1] * self.wall_width

        self.sprites: list[Sprite] = []
        self.sprite_lookup = {}

        self.items = {}
        self.actors: list = []

        self.pushwalls: list[WolfPushWall] = {}

    def add_sprite(self, sprite_src: Sprite, coor):
        if type(sprite_src) is not Sprite:
            raise TypeError("Expected Sprite object")
        # copy and add a sprite from sprite_src
        copy = sprite_src.copy(pos=coor)
        self.sprites.append(copy)
        # save to lookup for deletion
        self.sprite_lookup[self.to_block_pos(*coor)] = copy

    def delete_sprite(self, pos):
        sprite = self.sprite_lookup[pos]
        self.sprites.remove(sprite)
        del self.sprite_lookup[pos]

    def add_item(self, item: WolfItem, pos):
        effect = ITEM_AFFECT.get(item, None)
        mapitem = MapItem(self, item, pos, effect)
        self.items[mapitem.pos] = mapitem
        self.sprites.append(mapitem.sprite)
        self.sprite_lookup[mapitem.pos] = mapitem.sprite

    def pop_item(self, pos):
        item = self.items.pop(pos)
        self.delete_sprite(item.pos)
        return item

    def add_actor(self, actor):
        self.actors.append(actor)

    def add_decoration(self, decor: WolfDecoration, coor):
        if decor not in WolfDecoration:
            raise TypeError("can't add non decoration")
        spidx = DECORATION_SPRITES_MAPPING[decor]
        self.add_sprite(SPRITES["objects"][spidx], coor)

    def add_pushwall(self, block_pos):
        cell = self.raw[block_pos[1]][block_pos[0]]
        self.pushwalls[block_pos] = WolfPushWall(cell, block_pos)

    def to_block_pos(self, x, y):
        return int(x // self.wall_width), int(y // self.wall_width)

    def get_door(self, block_pos) -> WolfDoor:
        return self.doors.get(block_pos, None)

    def get_pushwall(self, block_pos) -> WolfPushWall:
        return self.pushwalls.get(block_pos, None)

    def add_door(self, block_pos, horizontal):
        self.doors[block_pos] = WolfDoor(
            block_pos, 1, horizontal=horizontal)

    def init_doors(self):
        self.doors.clear()
        for j, row in enumerate(self.raw):
            for i, entry in enumerate(row):
                if entry in self.DOOR:
                    self.add_door((i, j),
                                  horizontal=entry in self.HORIZ_DOOR)

    def get_cell(self, coor):
        block_pos = self.to_block_pos(*coor)
        return self.raw[block_pos[1]][block_pos[0]]

    def cell_occupied(self, block_pos):
        cell = self.raw[block_pos[1]][block_pos[0]]
        if not cell:
            if block_pos in self.sprite_lookup:
                sprite = self.sprite_lookup[block_pos]
                return sprite.blocking
            else:
                return False
        if cell in self.DOOR:
            door = self.get_door(block_pos)
            return door.opening != 0
        return True

    def in_boundary(self, coor):
        return 0 <= coor[0] < self.abs_size[0] and\
            0 <= coor[1] < self.abs_size[1]

    def set_random(self, amount, num=1):
        import random
        w, h = self.size
        for _ in range(amount):
            self.raw[random.randint(0, h-1)][random.randint(0, w-1)] = num
