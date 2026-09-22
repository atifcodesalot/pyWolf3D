
from raycaster.sprites import Sprite
from .actors import Actor
from .game_objects import *
from .assets import SPRITES


class WolfDoor:
    def __init__(self, pos, opening: float, horizontal=True):
        self.pos = pos
        self.opening = opening
        self.open = opening == 1
        self.horizontal = horizontal
        self.is_opening = False
        self.is_closing = False

    def is_open(self):
        return self.openning == 1

    def slide_open(self):
        self.opening = max(self.opening - 0.01, 0)

    def slide_close(self):
        self.opening = min(self.opening + 0.01, 1)

    def begin_opening(self):
        self.is_opening = True
        self.is_closing = False

    def begin_closing(self):
        self.is_closing = True


# map class, creates a simple 2D array for map layout
# 0: empty, nonzero: wall with texture
class WolfMap:
    DOOR = [0x1f + 1, (0x1f << 1) + 1]

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

        self.sprites = []
        self.sprite_lookup = {}

        self.items = {}
        self.actors = []

    def add_sprite(self, sprite_src: Sprite, pos):
        if type(sprite_src) is not Sprite:
            raise TypeError("Expected Sprite object")
        # copy and add a sprite from sprite_src
        copy = sprite_src.copy(pos=pos)
        self.sprites.append(copy)
        # save to lookup for deletion
        self.sprite_lookup[self.to_block_pos(*pos)] = copy

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

    def add_actor(self, actor: Actor):
        self.actors.append(actor)
        
    def add_decoration(self, decor: WolfDecoration, pos): 
        if decor not in WolfDecoration:
            raise TypeError("can't add non decoration")
        spidx = DECORATION_SPRITES_MAPPING[decor]
        self.add_sprite(SPRITES["objects"][spidx], pos)

    def construct_map(self):
        self.raw = list()
        w, h = self.size
        for _ in range(h):
            self.raw.append([0]*w)
        self.construct_outer_walls()

    def construct_outer_walls(self):
        w, h = self.size
        self.raw[0] = [1] * w
        self.raw[-1] = [1] * w
        for i in range(h):
            self.raw[i][0] = 1
            self.raw[i][-1] = 1

    def to_block_pos(self, x, y):
        return int(x // self.wall_width), int(y // self.wall_width)

    def get_door(self, block_pos) -> WolfDoor:
        return self.doors.get(block_pos, None)

    def add_door(self, block_pos, horizontal):
        self.doors[block_pos] = WolfDoor(
            block_pos, 1, horizontal=horizontal)

    def init_doors(self):
        self.doors.clear()
        for j, row in enumerate(self.raw):
            for i, entry in enumerate(row):
                if entry in self.DOOR:
                    self.add_door((i, j),
                                  horizontal=entry >> 1 == 0x1f)

    def get_cell(self, coor):
        pos = self.to_block_pos(*coor)
        return self.raw[pos[1]][pos[0]]

    def cell_occupied(self, coor):
        pos = self.to_block_pos(*coor)
        cell = self.raw[pos[1]][pos[0]]
        if not cell:
            if pos in self.sprite_lookup:
                sprite = self.sprite_lookup[pos]
                return sprite.blocking
            else:
                return False
        if cell in self.DOOR:
            door = self.get_door(pos)
            return door.opening != 0
        return True

    def neighbor_cells(self, center):
        return

    def in_boundary(self, coor):
        return 0 <= coor[0] < self.abs_size[0] and\
            0 <= coor[1] < self.abs_size[1]

    def set_random(self, amount, num=1):
        import random
        w, h = self.size
        for _ in range(amount):
            self.raw[random.randint(0, h-1)][random.randint(0, w-1)] = num
