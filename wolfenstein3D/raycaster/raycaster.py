

import math
from .aux_math import *
from wolf.maps import WolfMap, WolfDoor, WolfPushWall


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
        self.pos = plain_add(self.pos, tvec)


class Raycaster:
    atol = 0.000001

    def __init__(self, observer: Observer, map: WolfMap):
        self.observer = observer
        self.map = map

    def mags_for_step(self, trace, rx, ry, xnn, ynn):
        w = self.map.wall_width
        dx = w - (trace[0] % w) if xnn else -(trace[0] % w)
        dy = w - (trace[1] % w) if ynn else -(trace[1] % w)

        dx = dx if not self.atol > dx > -self.atol else (xnn - 1) * w
        dy = dy if not self.atol > dy > -self.atol else (ynn - 1) * w
        mags = [dx / rx, dy / ry]
        return mags

    def mags_for_half_step(self, trace, rx, ry, xnn, ynn, xhalf, yhalf):
        w = self.map.wall_width
        dx = w - (trace[0] % w) if xnn else -(trace[0] % w)
        if xhalf:
            dx = w / 2 if xnn else -w / 2

        dy = w - (trace[1] % w) if ynn else -(trace[1] % w)
        if yhalf:
            dy = w / 2 if ynn else -w / 2

        dx = dx if not self.atol > dx > -self.atol else (xnn - 1) * w
        dy = dy if not self.atol > dy > -self.atol else (ynn - 1) * w
        mags = [dx / rx, dy / ry]
        return mags

    def handle_door(self, cell, trace, door: WolfDoor,
                    vert_intercept: int, ray_context):
        # the ray hits from the door block's other side
        if not (vert_intercept ^ door.horiz):
            return vert_intercept, cell, True
        #
        ww = self.map.wall_width
        half_vert = self.march_ray_half(
            trace, *ray_context, vert_intercept, not vert_intercept)
        half_horiz = ~half_vert + 2
        # for a near side hit; the half step must hit,
        # in the opposite direction of the door orientation
        nearside_hit = (half_horiz ^ door.horiz)
        if nearside_hit:
            # return door interior cell
            return half_vert, 36, True

        offset = trace[vert_intercept] % ww
        door_hit = (offset / ww) < door.opening
        if door_hit:
            # the door was hit
            return half_vert, cell, True
        else:
            # if the ray passes the door opening
            hh_vert = self.march_ray_half(
                trace, *ray_context, half_vert, half_horiz)
            hh_horiz = ~hh_vert + 2
            farside_hit = (hh_horiz ^ door.horiz)
            hh_horiz = ~hh_vert + 2
            if farside_hit:
                return hh_vert, 36, True
            # the ray passes through
            return vert_intercept, cell, False

    def handle_pushwall(self, cell, trace, pushwall: WolfPushWall,
                        vert_intercept: int, *rayctx):
        if pushwall.offset == 1:
            return self.get_perp_dist(trace), vert_intercept, cell, True
        # the wall has slided

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

    def march_ray(self, trace, rx, ry, xnn, ynn) -> int:
        mags = self.mags_for_step(trace, rx, ry, xnn, ynn)
        mag = min(mags, key=abs)
        vert_hit = ~mags.index(mag) + 2
        trace[0] += rx * mag
        trace[1] += ry * mag
        return vert_hit

    def march_ray_half(self, trace, rx, ry, xnn, ynn, xhalf, yhalf) -> int:
        # if xhalf and yhalf:
        #     raise RuntimeError(
        #         "march_ray: cannot march half step in both directions")
        mags = self.mags_for_half_step(trace, rx, ry, xnn, ynn, xhalf, yhalf)
        mag = min(mags, key=abs)
        vert_hit = ~mags.index(mag) + 2
        trace[0] += rx * mag
        trace[1] += ry * mag
        return vert_hit

    def march_ray_offset(self, trace, rx, ry, xnn, ynn, xoffset, yoffset) -> int:
        # if xoffset and yoffset:
        #     raise RuntimeError(
        #         "march_ray: cannot march step in both offseted directions")
        mags = self.mags_offset(trace, rx, ry, xnn, ynn, xoffset, yoffset)
        mag = min(mags, key=abs)
        vert_hit = ~mags.index(mag) + 2
        trace[0] += rx * mag
        trace[1] += ry * mag
        return vert_hit

    def ray_step(self, trace, hw, rayctx) -> tuple:
        rx, ry, xnn, ynn = rayctx
        vert = self.march_ray(trace, rx, ry, xnn, ynn)
        xb = hw if not xnn and vert else 0
        yb = hw if not ynn and not vert else 0
        biased_pos = self.map.to_block_pos(
            trace[0] - xb, trace[1] - yb)
        if (cell := self.map.raw[biased_pos[1]][biased_pos[0]]):
            if cell in self.map.DOOR:
                door_obj = self.map.get_door(biased_pos)
                dvert, dcell, door_hit = self.handle_door(
                    cell,
                    trace,
                    door_obj,
                    vert,
                    rayctx)
                if door_hit:
                    return self.get_perp_dist(trace), dvert, dcell
                # the ray passes through the opening
                return None

            elif biased_pos in self.map.pushwalls:
                pushwall = self.map.get_pushwall(biased_pos)
                pdist, pvert, pcell, pwhit = self.handle_pushwall(
                    cell, trace, pushwall, vert)
                if pwhit:
                    return pdist, pvert, pcell
                return None

            return self.get_perp_dist(trace), vert, cell
        # no hit on an occupied cell
        # returns None

    def raycast(self):
        distbuff = []
        colls = []
        hw = self.map.wall_width // 2
        for ray_dir in self.observer.directions:
            rayctx = self.get_ray_context(ray_dir)
            trace = self.observer.pos.copy()
            while True:
                if (hitinfo := self.ray_step(trace, hw, rayctx)):
                    dist, vert, cell = hitinfo
                    distbuff.append(dist)
                    colls.append((trace, vert, cell))
                    break
                # hitinfo is none
        return colls, distbuff

    def get_corridor(self, rx, ry, start_pos):
        visited = []
        hw = self.map.wall_width // 2
        trace = start_pos.copy()
        rayctx = self.get_ray_context((rx, ry))
        rx, ry, xnn, ynn = rayctx
        while True:
            vert = self.march_ray(trace, rx, ry, xnn, ynn)
            xb = hw if not xnn and vert else 0
            yb = hw if not ynn and not vert else 0
            biased_pos = self.map.to_block_pos(
                trace[0] - xb, trace[1] - yb)
            visited.append(biased_pos)
            if (cell := self.map.raw[biased_pos[1]][biased_pos[0]]):
                if cell in self.map.DOOR:
                    door_obj = self.map.get_door(biased_pos)
                    _, _, door_hit = self.handle_door(
                        cell,
                        trace,
                        door_obj,
                        vert,
                        rayctx)
                    if door_hit:
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
