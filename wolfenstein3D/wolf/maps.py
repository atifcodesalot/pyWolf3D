
from raycaster.sprites import Sprite

class WolfDoor:
    def __init__(self, pos, opening: float, horizontal=True):
        self.pos = pos
        self.opening = opening
        self.open = opening == 1
        self.horizontal = horizontal

    def is_open(self):
        return self.openning == 1

    def slide(self):
        self.opening += 0.01


# map class, creates a simple 2D array for map layout
# 0: empty, nonzero: wall with texture
class WolfMap:
    DOOR = 0xd00f

    def __init__(self, size=(64, 64), array=None, wall_width=20):
        self.size = size
        if array is None:
            self.construct_map()
        else:
            self.raw = array

        self.wall_width = wall_width

        self.abs_size = self.size[0] * \
            self.wall_width, self.size[1] * self.wall_width

        self.doors = {}
        self.sprites = []
        
    def add_sprite(self, sprite_src: Sprite, pos):
        if type(sprite_src) is not Sprite:
            raise TypeError("Expected Sprite object")
        copy = sprite_src.copy(pos=pos)
        self.sprites.append(copy)

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

    def get_door(self, coor):
        pos = self.to_block_pos(*coor)
        return self.doors[pos]

    def add_door(self, pos, horizontal):
        self.raw[pos[1]][pos[0]] = self.DOOR
        self.doors[pos] = WolfDoor(pos, 1, horizontal=horizontal)

    def get_cell(self, coor):
        pos = self.to_block_pos(*coor)
        return self.raw[pos[1]][pos[0]]

    def in_boundary(self, coor):
        return 0 <= coor[0] < self.abs_size[0] and\
            0 <= coor[1] < self.abs_size[1]

    def set_random(self, amount, num=1):
        import random
        w, h = self.size
        for _ in range(amount):
            self.raw[random.randint(0, h-1)][random.randint(0, w-1)] = num
