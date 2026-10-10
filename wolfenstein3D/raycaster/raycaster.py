

import math
from .aux_math import *
from wolf.maps import WolfMap, WolfDoor, WolfPushWall


# observer class,
# contains the unit ray directions raycaster uses to cast.
class Observer:
    def __init__(self, pos, look_dir=[1, 0], fov=120, ray_count=200):
        self.pos = list(pos)
        self.look_dir = vec_norm(look_dir)
        self.left = vec_get_perp(self.look_dir)
        self.fov = math.radians(fov)
        self.vp_length = math.tan(self.fov / 2)
        self.ray_count = ray_count
        self.directions = []
        self.gap = self.fov / (self.ray_count - 1)
        self.update_directions()

    def update_directions(self):
        self.directions.clear()
        left_ray = rotate_vector_angle(
            self.look_dir, self.fov / -2).tolist()
        da = self.gap
        for i in range(self.ray_count):
            vec = rotate_vector_angle(left_ray, i*da)
            self.directions.append(vec.tolist())

    def to_this_space(self, pos):
        to_pos = vec_sub(self.pos, pos)
        return (vec_dot(to_pos, self.left),
                vec_dot(to_pos, self.look_dir))

    def rotate(self, angle):
        rm = ROT_MATRIX(math.radians(angle))
        self.look_dir = rm.dot(self.look_dir).tolist()
        self.left = rm.dot(self.left).tolist()
        self.update_directions()

    def translate(self, tvec):
        self.pos = vec_add(self.pos, tvec)


class Raycaster:
    atol = 1e-10

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

    def mags_offset(self, trace, rx, ry, xnn, ynn, xoff, yoff):
        w = self.map.wall_width
        if xoff:
            dx = xoff * w if xnn else -xoff * w
        else:
            dx = w - (trace[0] % w) if xnn else -(trace[0] % w)
        if yoff:
            dy = yoff * w if ynn else -yoff * w
        else:
            dy = w - (trace[1] % w) if ynn else -(trace[1] % w)

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
            return half_vert, 35, True

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
                return hh_vert, 35, True
            # the ray passes through
            return vert_intercept, None, False

    def handle_pushwall(self, cell, trace, pushwall: WolfPushWall,
                        vert_intercept: int, *rayctx):
        perpd = self.get_perp_dist
        w = self.map.wall_width
        absoff = pushwall.offset % 1
        if absoff == 0:
            return self.get_perp_dist(trace), vert_intercept, cell, True
        # the wall has offset
        rx, ry, *_ = rayctx
        slv = pushwall.sliding_vert
        if slv ^ vert_intercept:
            # the ray hits in the sliding orientation
            if vec_dot((rx, ry), pushwall.sliding_dir) < 0:
                # the wall is sliding in the opposite direction
                # relative to the ray
                return perpd(trace), vert_intercept, cell, True
            # the ray hits on the sliding face
            ttrace, offvert = self.test_march_ray_offset(
                trace, *rayctx, absoff * (~slv+2),
                absoff * slv)
            if offvert ^ slv:
                # the ray hits the sliding side
                # update trace
                trace[0] = ttrace[0]
                trace[1] = ttrace[1]
                return perpd(trace), offvert, cell, True
            else:
                # the ray passes through the slide gap
                return perpd(trace), offvert, None, False

        # the ray hits perp to the sliding orientation
        offset = trace[vert_intercept] % w
        if pushwall.sliding_sign != 1:
            offset = w - offset
        if offset > w * offset:
            # the ray passes through the opening
            raise NotImplementedError()
        else:
            return perpd(trace), vert_intercept, cell, True

    def get_perp_dist(self, trace):
        to_trace = vec_sub(self.observer.pos, trace)
        return vec_dot(to_trace, self.observer.look_dir)

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

    def test_march_ray_offset(self, trace, rx, ry, xnn, ynn, xoff, yoff) -> int:
        # if xoffset and yoffset:
        #     raise RuntimeError(
        #         "march_ray: cannot march step in both offseted directions")
        ttrace = trace.copy()
        mags = self.mags_offset(ttrace, rx, ry, xnn, ynn, xoff, yoff)
        mag = min(mags, key=abs)
        vert_hit = ~mags.index(mag) + 2
        ttrace[0] += rx * mag
        ttrace[1] += ry * mag
        return ttrace, vert_hit

    def ray_step(self, trace, hw, rayctx) -> tuple:
        rx, ry, xnn, ynn = rayctx
        vert = self.march_ray(trace, rx, ry, xnn, ynn)
        xb = hw if not xnn and vert else 0
        yb = hw if not ynn and not vert else 0
        biased_pos = self.map.to_block_pos(
            trace[0] - xb, trace[1] - yb)
        cell = self.map.raw[biased_pos[1]][biased_pos[0]]
        if cell < 106:
            if cell in self.map.DOOR_INDICES:
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
                return None, biased_pos

            elif biased_pos in self.map.pushwalls:
                pushwall = self.map.get_pushwall(biased_pos)
                pdist, pvert, pcell, pwhit = self.handle_pushwall(
                    cell, trace, pushwall, vert, *rayctx)
                if pwhit:
                    return pdist, pvert, pcell
                return None, biased_pos

            # hit non special cell
            return self.get_perp_dist(trace), vert, cell
        # no hit on an occupied cell
        return None, biased_pos

    def raycast(self, ray_dir, camera_pos):
        hw = self.map.wall_width // 2
        rayctx = self.get_ray_context(ray_dir)
        trace = camera_pos.copy()
        visited = []
        while True:
            hitinfo = self.ray_step(trace, hw, rayctx)
            if (hitinfo[0]):
                dist, vert, cell = hitinfo
                return (dist, trace, vert, cell, visited)
            else:
                # hitinfo doesnt contain ray hit info
                # append cell to visited
                visited.append(hitinfo[1])

    def get_corridor(self, rx, ry, start_pos):
        visited = [self.map.to_block_pos(*start_pos),]
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
            cell = self.map.raw[biased_pos[1]][biased_pos[0]]
            if cell < 106:
                if cell in self.map.DOOR_INDICES:
                    door_obj = self.map.get_door(biased_pos)
                    _, _, door_hit = self.handle_door(
                        cell,
                        trace,
                        door_obj,
                        vert,
                        rayctx)
                    visited.append(
                        tuple(vec_add(door_obj.pos, BASIS[door_obj.horiz])))
                    visited.append(tuple(vec_add(door_obj.pos, vec_mul(
                        BASIS[door_obj.horiz], -1))))
                    if door_hit:
                        break
                else:
                    break

        return visited

    def render_bird_view(self, colls, pygame, pgsurface):
        m = self.map
        ww = m.wall_width
        for x in range(m.size[0]):
            for y in range(m.size[1]):
                if (cell := m.raw[y][x]):
                    color = (255, 0, 0)
                    if cell in self.map.DOOR_INDICES:
                        color = (0, 255, 0)
                    elif (x, y) in m.pushwalls:
                        color = (23, 42, 255)
                    pygame.draw.rect(pgsurface, color,
                                     (x*ww, y*ww, ww, ww))

        for coll in colls:
            if coll is not None:
                pygame.draw.aaline(pgsurface, (255, 255, 255),
                                   self.observer.pos, coll[0])
                pygame.draw.circle(pgsurface, (0, 0, 255), coll[0], 2)
