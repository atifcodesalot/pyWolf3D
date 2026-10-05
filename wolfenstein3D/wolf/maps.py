
from raycaster.sprites import Sprite
from raycaster.aux_math import *
from .game_objects import *
from .assets import SPRITES, SOUNDS
from .actors import TYPE_ACTOR_OBJ
from copy import deepcopy


class WolfDoor:
    SLIDE = 0.02

    def __init__(self, _map, pos, opening: float, horizontal=True):
        self.map = _map
        self.pos = pos
        self.opening = opening
        self.horiz = horizontal
        self.is_opening = False
        self.is_closing = False
        self.init_areas()
        
    def init_areas(self):
        dir_ = BASIS[self.horiz.real]
        area0pos = vec_add(self.pos, dir_)
        area1pos = vec_sub(dir_, self.pos)
        self.area0 = self.map.raw[area0pos[1]][area0pos[0]] - 107
        self.area1 = self.map.raw[area1pos[1]][area1pos[0]] - 107

    def is_open(self):
        return self.opening == 0

    def slide_open(self):
        self.opening = max(self.opening - self.SLIDE, 0)

    def slide_close(self):
        self.opening = min(self.opening + self.SLIDE, 1)
        
    def connect_areas(self):
        self.map.area_matrix[self.area1][self.area0] = 1
        self.map.area_matrix[self.area0][self.area1] = 1
        
    def disconnect_areas(self):
        self.map.area_matrix[self.area1][self.area0] = 0
        self.map.area_matrix[self.area0][self.area1] = 0

    def begin_opening(self):
        if self.is_opening:
            return
        self.connect_areas()
        SOUNDS["doors"]["OPENDOORSND.WAV"].play()
        self.is_opening = True
        self.is_closing = False

    def begin_closing(self):
        self.disconnect_areas()
        SOUNDS["doors"]["CLOSEDOORSND.WAV"].play()
        self.is_closing = True

    def reset(self):
        self.is_opening = False
        self.is_closing = False
        self.opening = 1
        
    def open_callback(self):
        pass


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
        SOUNDS["doors"]["PUSHWALLSND.WAV"].play()
        self.sliding = True
        self.sliding_dir = dir
        self.sliding_vert = (vec_dot(self.sliding_dir, (0, 1)) != 0).real
        self.sliding_sign = sum(self.sliding_dir)

    def slide_open(self, wolfmap):
        self.offset = min(self.offset + self.SLIDE, 2)
        if (self.ATOL > self.offset % 1 > -self.ATOL):
            adjpos = vec_add(self.pos, self.sliding_dir)
            adjpos = (int(adjpos[0]), int(adjpos[1]))
            # unoccupy current cell, set it an ambush tile
            wolfmap.raw[self.pos[1]][self.pos[0]] = 106
            # occupy adjacent cell
            wolfmap.raw[adjpos[1]][adjpos[0]] = self.cell
            del wolfmap.pushwalls[self.pos]

            self.pos = adjpos
            wolfmap.pushwalls[self.pos] = self
            if self.offset == 2:
                self.sliding = False
                self.slid = True
                return

    def reset(self):
        self.offset = 0
        self.sliding_vert = 0
        self.sliding = False
        self.slid = False


# map class,
# 0: empty, nonzero: wall with texture
# DOOR has door tile numbers
# contains actors, items, sprites to render etc.
class WolfMap:
    DOOR = [0x1f, 0x1f << 1, 0x22, 0x22 << 1]
    HORIZ_DOOR = [0x1f << 1, 0x22 << 1]

    def __init__(self, size=(64, 64), array=None,
                 wall_width=20, init_pos=[0, 0], init_look_dir=[1, 0]):
        self.size = size

        self.wall_width = wall_width
        self.init_pos = list(init_pos)
        self.init_look = list(init_look_dir)

        self.sprites: list[Sprite] = []
        self.sprite_lookup = {}

        self.actors: list = []

        self.item_lookup: dict[tuple: WolfItemObj] = {}
        self.pushwalls: dict[tuple: WolfPushWall] = {}
        self.doors: dict[tuple: WolfDoor] = {}
        self.raw = array
        self.init_doors()
        
        self.area_matrix = []
        for i in range(37):
            row = [0,] * 37
            row[i] = 1
            self.area_matrix.append(row)

    def snapshot(self):
        state = (deepcopy(self.raw),
                 [act.snapshot() for act in self.actors],
                 self.item_lookup.copy(),
                 self.sprite_lookup.copy(),
                 self.sprites.copy(),
                 deepcopy(self.pushwalls))

        return state

    def reload_snapshot(self, snapshot):
        raw, actsnaps, itemsnap, spdsnap, spsnap, pws = snapshot
        self.raw = deepcopy(raw)
        for snap, act in zip(actsnaps, self.actors):
            act.reload_snapshot(snap)
        self.item_lookup = itemsnap.copy()
        self.sprite_lookup = spdsnap.copy()
        self.sprites = spsnap.copy()
        self.pushwalls = deepcopy(pws)

    def reset(self):
        self.reload_snapshot(self.init_snap)
        for k in self.doors:
            self.doors[k].reset()

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
        itemobj = WolfItemObj(self, item, pos, effect)
        self.item_lookup[itemobj.pos] = itemobj
        self.sprites.append(itemobj.sprite)
        self.sprite_lookup[itemobj.pos] = itemobj.sprite

    def pop_item(self, pos):
        item = self.item_lookup.pop(pos)
        self.delete_sprite(item.pos)
        return item

    def add_actor(self, actor_type: WolfActorType, pos, look_dir):
        if actor_type not in WolfActorType:
            raise TypeError("can't add non actor type")
        actor_obj = TYPE_ACTOR_OBJ[actor_type](self, pos, look_dir)
        self.actors.append(actor_obj)

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
        self.doors[block_pos] = WolfDoor(self,
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
        if not self.in_boundary(block_pos):
            return True
        cell = self.raw[block_pos[1]][block_pos[0]]
        if cell >= 106:
            # cell is empty
            if block_pos in self.sprite_lookup:
                sprite = self.sprite_lookup[block_pos]
                return sprite.blocking
            else:
                return False
        if cell in self.DOOR:
            door = self.get_door(block_pos)
            return door.opening != 0
        return True

    def in_boundary(self, block_pos):
        return 0 <= block_pos[0] < self.size[0] and\
            0 <= block_pos[1] < self.size[1]

    def set_random(self, amount, num=1):
        import random
        w, h = self.size
        for _ in range(amount):
            self.raw[random.randint(0, h-1)][random.randint(0, w-1)] = num
