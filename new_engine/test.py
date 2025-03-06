import math
import numpy as np
import matplotlib.pyplot as plt
import mpmath

mpmath.mp.dps = 100

N = mpmath.mpf("12242945609572961744356466185880148497170699959845184127931125935360")
x_vals = np.arange(0, 16)


def binary_expression(x, y):
    term1 = mpmath.floor(y / 15)
    y_modulo15 = y % 15
    power_term = mpmath.power(2, -15 * x - y_modulo15)
    mod_term = (term1 * power_term) % 2
    floor_mod_term = math.floor(mod_term)
    return floor_mod_term > 1/2

result = []

for i in range(16):
    y = N + i
    row = []
    for x in x_vals:
        row.append(binary_expression(x, y))
    result.append(row)

result = np.array(result)
result = np.flipud(result)
result = result[1:]

plt.figure(figsize=(20, 20))
plt.imshow(result, cmap = 'gray_r', origin = 'upper')