

import math
import numpy as np

BASIS = (np.array((1, 0)), np.array((0, 1)))

def ROT_MATRIX(a): return np.array(
    [[math.cos(a), -math.sin(a)],
     [math.sin(a), math.cos(a)]])

def np_norm(vec):
    return np.divide(vec, np.linalg.norm(vec))

def vec_norm(vec):
    mag = math.sqrt(vec[0]**2 + vec[1]**2)
    return [vec[0] / mag, vec[1] / mag]

def vec_sub(v1, v2):
    return [v2[0] - v1[0], v2[1] - v1[1]]

def vec_mul(v1, s):
    return [v1[0] * s, v1[1] * s]

def vec_add(v1, v2):
    return [v2[0] + v1[0], v2[1] + v1[1]]

def rotate_vector_angle(vec, angle):
    rm = ROT_MATRIX(angle)
    return rm.dot(vec)

def euclidean_distance(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def vec_dot(a, b):
    return a[0] * b[0] + a[1] * b[1]
 
def sign(x):
    if x > 0: return 1
    if x < 0: return -1
    return 0

def vec_get_perp(vec):
    return [-vec[1], vec[0]]