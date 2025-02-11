import numpy as np

def in_triangle(point, triangle):
    a, b, c = np.array([np.array([p[0], p[2]]) for p in triangle])
    p = np.array([point[0], point[2]])

    # Compute vectors
    v0 = c - a
    v1 = b - a
    v2 = p - a

    # Compute dot products
    dot00 = np.dot(v0, v0)
    dot01 = np.dot(v0, v1)
    dot02 = np.dot(v0, v2)
    dot11 = np.dot(v1, v1)
    dot12 = np.dot(v1, v2)

    # Compute barycentric coordinates
    denom = dot00 * dot11 - dot01 * dot01
    if denom == 0:  # Degenerate triangle
        return False

    u = (dot11 * dot02 - dot01 * dot12) / denom
    v = (dot00 * dot12 - dot01 * dot02) / denom

    # Check if point is inside the triangle
    return (u >= 0) and (v >= 0) and (u + v <= 1)


a = np.array([5, -3, 8])
triangle = np.array([
    [0, 0, 0],
    [0, 0, 10],
    [10, 0, 10],
])

print(in_triangle(a, triangle))
import math

x = -6.24e-8
print(math.floor(x))  # Expected: -1