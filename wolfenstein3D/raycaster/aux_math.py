

import math
import numpy as np

BASIS = (np.array((1, 0)), np.array((0, 1)))

def ROT_MATRIX(a): return np.array(
    [[math.cos(a), -math.sin(a)],
     [math.sin(a), math.cos(a)]])

def normalize(vec):
    return np.divide(vec, np.linalg.norm(vec))

def plain_normalize(vec):
    mag = math.sqrt(vec[0]**2 + vec[1]**2)
    return (vec[0] / mag, vec[1] / mag)

def rotate_vector_angle(vec, angle):
    rm = ROT_MATRIX(angle)
    return rm.dot(vec)

def euclidean_distance(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def plain_dot(a, b):
    return a[0] * b[0] + a[1] * b[1]
 
def sign(x):
    if x > 0: return 1
    if x < 0: return -1
    return 0