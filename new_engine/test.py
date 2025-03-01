import numpy as np
import matplotlib.pyplot as plt
from chunk_jittery_test import SplineHeightParams

# Define points and create the SplineHeightParams instance
points = ((0.0, -0.3), (0.4, 0.0), (0.45, 0.1), (0.5, 0.2), (0.6, 0.26), (1.0, 1.0))
shp = SplineHeightParams(points, 1.0)

# Generate values between 0 and 1
x = np.linspace(0, 1, 500)
y = [shp.height_from_noise(k) for k in x]

# Plot the spline
plt.figure(figsize=(8, 5))
plt.plot(x, y, label='Original Curve', color='blue')
plt.scatter(*zip(*points), color='red', label='Control Points', zorder=3)
plt.xlabel('Input Value (Noise)')
plt.ylabel('Height')
plt.title('Original Height Function')
plt.legend()
plt.grid()
plt.show()