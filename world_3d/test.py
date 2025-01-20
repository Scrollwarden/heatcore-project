class PointsHeightParams:
    def __init__(self, points, scale: float = 1.0) -> None:
        self.points = points
        self.denom_list = [1 / (points[i][0] - points[i + 1][0]) for i in range(len(self.points) - 1)]
        self.scale = scale

    def height_from_noise(self, noise_value: float) -> float:
        index = 0
        while index < len(self.points) - 1 and self.points[index + 1][0] < noise_value:
            index += 1
        h = (noise_value - self.points[index + 1][0]) * self.denom_list[index]
        return h * self.points[index][1] + (1 - h) * self.points[index + 1][1]

points = ((0.0, -0.2), (0.4, 0.0), (0.45, 0.1), (0.5, 0.2), (0.6, 0.26), (1.0, 1.0))
height_params = PointsHeightParams(points)


import numpy as np
import matplotlib.pyplot as plt


# Generate x values (e.g., from -10 to 10 with 0.1 increments)
x = np.arange(0, 1, 0.001)

# Calculate corresponding y values
y = [height_params.height_from_noise(value) for value in x]

# Plot the points
plt.plot(x, y, label="height", color="blue")  # Plot as a line
plt.scatter(x, y, color="red", s=10)  # Optional: Show points

# Add labels and title
plt.xlabel("x")
plt.ylabel("y")
plt.title("Plot of height")
plt.legend()

# Show the plot
plt.grid(True)  # Optional: Add a grid
plt.show()
