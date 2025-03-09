import time
import numpy as np
from noise import pnoise2
from opensimplex import OpenSimplex

# Parameters
num_samples = 100_000
seed = 1234
scale = 100.0
octaves = 4
persistence = 0.5
lacunarity = 2.0

# Generate random coordinates
x_vals = np.random.uniform(0, 1000, num_samples)
y_vals = np.random.uniform(0, 1000, num_samples)

# --- Benchmark noise.pnoise2 ---
start_time = time.time()
for x, y in zip(x_vals, y_vals):
    _ = pnoise2(x / scale, y / scale, octaves=octaves, persistence=persistence, lacunarity=lacunarity, base=seed)
pnoise2_time = time.time() - start_time

# --- Benchmark OpenSimplex ---
open_simplex = OpenSimplex(seed=seed)
start_time = time.time()
for x, y in zip(x_vals, y_vals):
    _ = open_simplex.noise2(x / scale, y / scale)
opensimplex_time = time.time() - start_time

print(f"pnoise2 time: {pnoise2_time:.4f} sec")
print(f"OpenSimplex time: {opensimplex_time:.4f} sec")
