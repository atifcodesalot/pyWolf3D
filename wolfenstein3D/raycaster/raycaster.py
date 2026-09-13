

import math
import numpy as np
from .aux_math import *
from wolf.mapeditor import Map


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
        self.left_dir = rotate_vector_angle(self.look_dir, self.fov / -2)
        da = self.gap
        for i in range(self.ray_count):
            vec = rotate_vector_angle(self.left_dir, i*da)
            self.directions.append(vec.tolist())

    def rotate(self, angle):
        rm = ROT_MATRIX(math.radians(angle))
        self.look_dir = rm.dot(self.look_dir)
        self.left = rm.dot(self.left)
        self.update_directions()

    def translate(self, tvec):
        self.pos[0] += tvec[0]
        self.pos[1] += tvec[1]



class Raycaster:
    atol = 0.000001

    def __init__(self, observer: Observer, map: Map):
        self.observer = observer
        self.map = map
        self.collisions = []
        self.distance_buffer = []

    def get_mags_for_step(self, track, rx, ry, xnn, ynn):
        w = self.map.wall_width
        # determine offset direction
        dx = w - (track[0] % w) if xnn else -(track[0] % w)
        dy = w - (track[1] % w) if ynn else -(track[1] % w)
        #
        dx = dx if not self.atol > dx > -self.atol else (xnn - 1) * w
        dy = dy if not self.atol > dy > -self.atol else (ynn - 1) * w
        mags = [dx / rx, dy / ry]
        return mags

    def raycast(self):
        self.distance_buffer.clear()
        self.collisions.clear()
        w = self.map.wall_width
        o = self.observer
        for ray_dir in self.observer.directions:
            track = self.observer.pos.copy()
            # get signs of the ray direction
            rx, ry = ray_dir
            # guard against zero division
            if rx == 0:
                rx = 1e-10
            if ry == 0:
                ry = 1e-10
            #
            dxs = sign(rx)
            dys = sign(ry)
            # x is non negative
            xnn = dxs + 1
            # y is non negative
            ynn = dys + 1
            while True:
                if not self.map.in_boundary(track):
                    # if the track is out of the map end
                    # and it has not collided with a filled rect
                    self.collisions.append(None)
                    break
                
                mags = self.get_mags_for_step(track, rx, ry, xnn, ynn)
                mag = min(mags, key=abs)
                vertical = mags.index(mag)
                track[0] += rx * mag
                track[1] += ry * mag

                xb = w // 2 if not xnn and not vertical else 0
                yb = w // 2 if not ynn and vertical else 0

                if (cell := self.map.get_cell(
                    (track[0] - xb,
                     track[1] - yb))):
                    self.collisions.append((track, vertical, cell))
                    to_track = (track[0] - o.pos[0],
                                track[1] - o.pos[1])
                    self.distance_buffer.append(
                        plain_dot(to_track, o.look_dir))
                    break

    def render_bird_view(self, pygame, pgsurface):
        m = self.map
        ww = m.wall_width
        for b in range(m.size[0]):
            for a in range(m.size[1]):
                if m.raw[b][a]:
                    pygame.draw.rect(pgsurface, (255, 0, 0),
                                     (a*ww, b*ww, ww, ww))
        for coll in self.collisions:
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
