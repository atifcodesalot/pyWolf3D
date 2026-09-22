

import math
from .aux_math import *
from wolf.maps import WolfMap, WolfDoor


# observer class,
# contains the unit ray directions raycaster uses to cast.
class Observer:
    def __init__(self, pos, look_dir=[1, 0], fov=120, ray_count=200):
        self.pos = list(pos)
        self.look_dir = plain_normalize(look_dir)
        self.left = get_perp(self.look_dir)
        self.fov = math.radians(fov)
        self.vp_length = math.tan(self.fov / 2)
        self.ray_count = ray_count
        self.directions = []
        self.gap = self.fov / (self.ray_count - 1)
        self.update_directions()

    def update_directions(self):
        self.directions.clear()
        self.left_dir = rotate_vector_angle(
            self.look_dir, self.fov / -2).tolist()
        da = self.gap
        for i in range(self.ray_count):
            vec = rotate_vector_angle(self.left_dir, i*da)
            self.directions.append(vec.tolist())

    def to_this_space(self, pos):
        to_pos = plain_sub(self.pos, pos)
        return (plain_dot(to_pos, self.left),
                plain_dot(to_pos, self.look_dir))

    def rotate(self, angle):
        rm = ROT_MATRIX(math.radians(angle))
        self.look_dir = rm.dot(self.look_dir).tolist()
        self.left = rm.dot(self.left).tolist()
        self.update_directions()

    def translate(self, tvec):
        self.pos[0] += tvec[0]
        self.pos[1] += tvec[1]


class Raycaster:
    atol = 0.000001

    def __init__(self, observer: Observer, map: WolfMap):
        self.observer = observer
        self.map = map

    def mags_for_step(self, trace, rx, ry, xnn, ynn, xhalf=False, yhalf=False):
        w = self.map.wall_width
        if xhalf:
            dx = w / 2 if xnn else -w / 2
        else:
            dx = w - (trace[0] % w) if xnn else -(trace[0] % w)

        if yhalf:
            dy = w / 2 if ynn else -w / 2
        else:
            dy = w - (trace[1] % w) if ynn else -(trace[1] % w)

        dx = dx if not self.atol > dx > -self.atol else (xnn - 1) * w
        dy = dy if not self.atol > dy > -self.atol else (ynn - 1) * w
        mags = [dx / rx, dy / ry]
        return mags

    def handle_door(self, trace, door: WolfDoor,
                    vert_intercept: int, *details):
        # the ray hits from the door's side
        if not (vert_intercept ^ door.horizontal):
            return vert_intercept, self.map.DOOR[0], trace, True
        #
        ww = self.map.wall_width
        trace, hstep_vertical = self.march_ray(
            trace, *details, vert_intercept, not vert_intercept)
        hstep_horizontal = ~hstep_vertical + 2
        offset = trace[vert_intercept] % ww
        door_hit = (offset / ww) < door.opening
        cell = self.map.DOOR[0]
        side_hit = (hstep_horizontal ^ door.horizontal)
        if side_hit:
            # if a side hit, return door interior sprite
            cell = 36
        return hstep_vertical, cell, trace, door_hit or side_hit

    def get_perp_dist(self, trace):
        to_trace = plain_sub(self.observer.pos, trace)
        return plain_dot(to_trace, self.observer.look_dir)
    
    @staticmethod
    def get_ray_context(ray):
        # get signs of the ray direction
        rx, ry = ray
        # guard against zero division
        if rx == 0:
            rx = 1e-10
        if ry == 0:
            ry = 1e-10
        # x is non negative
        xnn = sign(rx) + 1
        # y is non negative
        ynn = sign(ry) + 1
        return rx, ry, xnn, ynn

    def march_ray(self, ctrace, rx, ry, xnn, ynn, xhalf=False, yhalf=False):
        mags = self.mags_for_step(ctrace, rx, ry, xnn, ynn, xhalf, yhalf)
        mag = min(mags, key=abs)
        vertical_hit = ~mags.index(mag) + 2
        ctrace[0] += rx * mag
        ctrace[1] += ry * mag
        return ctrace, vertical_hit
    
    def ray_step(self, ray_dir, trace, hw):
        rx, ry, xnn, ynn = self.get_ray_context(ray_dir)
        trace, vertical = self.march_ray(trace, rx, ry, xnn, ynn)
        xb = hw if not xnn and vertical else 0
        yb = hw if not ynn and not vertical else 0
        biased_pos = self.map.to_block_pos(
            trace[0] - xb, trace[1] - yb)
        if (cell := self.map.raw[biased_pos[1]][biased_pos[0]]):
            if cell in self.map.DOOR:
                door_obj = self.map.get_door(biased_pos)
                dvertical, dcell, dtrace, dhit = self.handle_door(
                    trace,
                    door_obj,
                    vertical,
                    rx, ry, xnn, ynn)
                if dhit:
                    return self.get_perp_dist(dtrace), dtrace, dvertical, dcell
                else:
                    return
    
            return self.get_perp_dist(trace), trace, vertical, cell

    def raycast(self):
        db = []
        colls = []
        hw = self.map.wall_width // 2
        for ray_dir in self.observer.directions:
            trace = self.observer.pos.copy()
            while True:
                if (data := self.ray_step(ray_dir, trace, hw)):
                    dist, trace, vert, cell = data
                    db.append(dist)
                    colls.append((trace, vert, cell))
                    break
        return colls, db

    def get_corridor(self, rx, ry):
        visited = []
        hw = self.map.wall_width // 2
        trace = self.observer.pos.copy()
        rx, ry, xnn, ynn = self.get_ray_context((rx, ry))
        while True:
            trace, vertical = self.march_ray(trace, rx, ry, xnn, ynn)
            xb = hw if not xnn and vertical else 0
            yb = hw if not ynn and not vertical else 0
            biased_pos = self.map.to_block_pos(
                trace[0] - xb, trace[1] - yb)
            visited.append(biased_pos)
            if (cell := self.map.raw[biased_pos[1]][biased_pos[0]]):
                if cell in self.map.DOOR:
                    door_obj = self.map.get_door(biased_pos)
                    _, _, _, dhit = self.handle_door(
                        trace,
                        door_obj,
                        vertical,
                        rx, ry, xnn, ynn)
                    if dhit:
                        break
                else:
                    break
                    
        return visited

    def render_bird_view(self, colls, pygame, pgsurface):
        m = self.map
        ww = m.wall_width
        for b in range(m.size[0]):
            for a in range(m.size[1]):
                if (cell := m.raw[b][a]):
                    color = (255, 0, 0)
                    if cell in self.map.DOOR:
                        color = (0, 255, 0)
                    pygame.draw.rect(pgsurface, color,
                                     (a*ww, b*ww, ww, ww))

        for coll in colls:
            if coll is not None:
                pygame.draw.aaline(pgsurface, (255, 255, 255),
                                   self.observer.pos, coll[0])
                pygame.draw.circle(pgsurface, (0, 0, 255), coll[0], 2)

        pygame.draw.line(pgsurface, (0, 255, 0), self.observer.pos,
                         (self.observer.pos[0] + self.observer.left[0] * 20,
                          self.observer.pos[1] + self.observer.left[1] * 20))
        pygame.draw.line(pgsurface, (255, 0, 0), self.observer.pos,
                         (self.observer.pos[0] + self.observer.look_dir[0] * 20,
                          self.observer.pos[1] + self.observer.look_dir[1] * 20))
