

# map class, creates a simple 2D array for map layout
# 0: empty, nonzero: wall with texture
class Map:
    def __init__(self, size, array=None, wall_width=20):
        self.size = size
        if array is None:
            self.construct_map()
        else:
            self.raw = array

        self.wall_width = wall_width

        self.abs_size = self.size[0] * \
            self.wall_width, self.size[1] * self.wall_width

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

    def get_cell(self, coor):
        return self.raw[int(coor[1] // self.wall_width)]\
            [int(coor[0] // self.wall_width)]

    def in_boundary(self, coor):
        return 0 <= coor[0] < self.abs_size[0] and\
            0 <= coor[1] < self.abs_size[1]

    def set_random(self, amount, num=1):
        import random
        w, h = self.size
        for _ in range(amount):
            self.raw[random.randint(0, h-1)][random.randint(0, w-1)] = num
