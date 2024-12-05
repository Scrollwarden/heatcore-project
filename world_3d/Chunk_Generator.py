from pygame import Vector2
import numpy as np
import math # Just for height adjustment
import noise # Just to generate chunk
import pygame # Just for 2D display at the end
from collections.abc import Iterable # Just to know the size of the chunk
import sys # Just to know the size of the chunk
import time # Just for time taken on terminal

CHUNK_SIZE: int = 8

class HeightParams:
    def __init__(self) -> None:
        self.x1, self.y1 = 0.6, 0.044
        self.p, self.q = 2, 1
        self.a = self.y1 / math.pow(self.x1, self.p)
        self.b = (self.y1 - 1) / (math.pow(self.x1, self.q) - 1)

    def height_from_noise(self, noise_value: float) -> float:
        if noise_value < self.x1:
            return self.a * math.pow(noise_value, self.p)
        elif noise_value > self.x1:
            return self.b * (math.pow(noise_value, self.q) - 1) + 1
        else:
            return self.y1


class ColorParams:
    def __init__(self) -> None:
        self.heights_limit = [0.005, 0.02, 0.25, 0.4, 0.45, 0.525, 0.59, 0.68, 0.74, 0.79, 0.85]
        self.colors = [( 21,  47,  88), ( 25,  54, 100), ( 33,  69, 120), ( 44,  87, 147), # Water
                       (245, 222, 154), # Beach
                       (124, 162,  55), ( 89, 135,  51), # Grass
                       ( 39,  39,  39), ( 67,  57,  47), ( 74,  62,  53), ( 79,  73,  68), # Mountain
                       (255, 255, 255)] # Peak

    def get_color_from_noise(self, height: float) -> tuple[int, int, int]:
        for i, height_limit in enumerate(self.heights_limit):
            if height <= height_limit:
                return self.colors[i]
        return self.colors[-1]


class ChunkTerrain:
    def __init__(self, x_chunk: int, y_chunk: int, height_data, color_data) -> None:
        self.coord: Vector2 = Vector2(x_chunk, y_chunk)
        # The data have a (CHUNK_SIZE + 1, CHUNK_SIZE + 1) shape because it needs the points on each side
        self.height_data = height_data # type is np.array(shape=(CHUNK_SIZE + 1, CHUNK_SIZE + 1), dtype=np.float16)
        self.color_data = color_data # type is np.array(shape=(CHUNK_SIZE + 1, CHUNK_SIZE + 1, 3), dtype=np.uint8)
        self.vertices = None
        self.triangles = None
        self.colors = None

    def update_detail(self, new_level_of_detail, scale) -> None:
        """Change the level of detail of a chunk depending on the distance and adjust triangles to be isosceles
        0 for best detail and math.log2(CHUNK_SIZE) - 1 for worst detail"""
        if not (isinstance(new_level_of_detail, int) and 0 <= new_level_of_detail < math.log2(CHUNK_SIZE)):
            raise ValueError(f"The level of detail ({new_level_of_detail}) is not correct, it should be an integer between 0 and {int(math.log2(CHUNK_SIZE)) - 1}")

        simplification_increment: int = 2 ** new_level_of_detail
        vertices_per_line: int = CHUNK_SIZE // simplification_increment + 1

        self.vertices = np.zeros(shape=(vertices_per_line, vertices_per_line, 3), dtype=float)
        # The position in 3D space of each point in the chunk. For example [3.0, 0.763, 2.0] for the point (x, y)
        self.triangles = np.zeros(shape=(2* (vertices_per_line - 1) ** 2, 3, 2), dtype=np.uint8)
        # The 3 points of the chunk that build each triangle. For example: [[3, 0], [4, 0], [4, 1]] for the indexes of each vertex
        self.colors = np.zeros(shape=(2 * (vertices_per_line - 1) ** 2, 2), dtype=np.uint8)
        # The colors of each triangle. For example colors[i] is the color for triangles[i]
        triangle_index: int = 0
        for x in range(vertices_per_line):
            for y in range(vertices_per_line):
                # Vertices
                if y % 2 == 0:
                    self.vertices[x, y] = np.array((self.coord.x * CHUNK_SIZE + x, self.height_data[x, y], self.coord.y * CHUNK_SIZE + y), dtype=float) * scale
                else:
                    self.vertices[x, y] = np.array((self.coord.x * CHUNK_SIZE + x + 0.5, self.height_data[x, y], self.coord.y * CHUNK_SIZE + y), dtype=float) * scale

                if x < CHUNK_SIZE and y < CHUNK_SIZE:
                    # Triangles
                    if y % 2 == 0:
                        self.triangles[triangle_index, :] = ((x, y), (x + 1, y), (x, y + 1))
                        self.triangles[triangle_index + 1, :] = ((x + 1, y + 1), (x, y + 1), (x + 1, y))
                    else:
                        self.triangles[triangle_index, :] = ((x + 1, y + 1), (x, y), (x + 1, y))
                        self.triangles[triangle_index + 1, :] = ((x, y), (x + 1, y + 1), (x, y + 1))
                    # Colors
                    self.colors[triangle_index] = (x * simplification_increment, y * simplification_increment)
                    self.colors[triangle_index + 1] = (x * simplification_increment, (y + 1) * simplification_increment)
                    triangle_index += 2

        print(f"{triangle_index}/{6 * (vertices_per_line - 1) ** 2} triangles done")


def generate_chunk(x_chunk: int, y_chunk: int, height_arrangement: HeightParams, color_arrangement: ColorParams,
                   seed: int = None,
                   scale: float = 1.0,
                   octaves: int = 1,
                   persistence: float = 0.5,
                   lacunarity: float = 2.0) -> ChunkTerrain:
    height_data = np.zeros(shape=(CHUNK_SIZE + 1, CHUNK_SIZE + 1), dtype=np.float16)
    color_data = np.zeros(shape=(CHUNK_SIZE + 1, CHUNK_SIZE + 1, 3), dtype=np.uint8)

    if seed is None:
        raise ValueError("The seed can't be None")

    for x in range(CHUNK_SIZE + 1):
        for y in range(CHUNK_SIZE + 1):
            sample_x, sample_y = (x_chunk * CHUNK_SIZE + x) / scale, (y_chunk * CHUNK_SIZE + y) / scale
            perlin_value = noise.pnoise2(sample_x, sample_y, octaves=octaves, persistence=persistence,
                                         lacunarity=lacunarity, base=seed)
            noise_value = max(0, min(1, (perlin_value / max(0.5, (0.42 / octaves + 0.44)) + 1) / 2))

            height_data[x, y] = height_arrangement.height_from_noise(noise_value)
            color = color_arrangement.get_color_from_noise(noise_value)
            for i in range(3):
                color_data[x, y, i] = color[i]

    return ChunkTerrain(x_chunk, y_chunk, height_data, color_data)


def get_total_size(obj, seen=None):
    """Recursively find the total size of an object and its contents."""
    if seen is None:
        seen = set()

    size = sys.getsizeof(obj)
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    # If it's a numpy array, use nbytes instead of sys.getsizeof()
    if isinstance(obj, np.ndarray):
        return obj.nbytes

    # If it's a custom object, calculate the size of its attributes
    if hasattr(obj, '__dict__'):
        size += sum(get_total_size(v, seen) for v in obj.__dict__.values())

    # If it's an iterable (but not a string or bytes), calculate the size of elements
    elif isinstance(obj, Iterable) and not isinstance(obj, (str, bytes, bytearray)):
        size += sum(get_total_size(i, seen) for i in obj)
    return size

# Function to format the size
def format_size(size_bytes):
    """Formats size in bytes into a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes}o"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f}Ko"
    else:
        return f"{size_bytes / 1024 ** 2:.1f}Mo"

def display_chunk(chunk: ChunkTerrain):
    """Example of a function that could display a chunk on screen"""
    def display_triangle(a, b, c, color):
        """A function that displays a triangle. Here it doesn't display on screen, but it's just for reference"""
        print(f"Triangle ({a}, {b}, {c}) displayed with color {color}")

    if chunk.triangles is None:
        raise ValueError("The chunk needs to be loaded")

    for i in range(len(chunk.triangles)):
        triangle_positions = [chunk.vertices[x, y] for x, y in chunk.triangles[i]]
        m, n = chunk.colors[i]
        triangle_color = chunk.color_data[m, n]
        display_triangle(*triangle_positions, triangle_color)


if __name__ == "__main__":
    height_param = HeightParams()
    color_param = ColorParams()
    start_time = time.time()
    test_chunk = generate_chunk(0, 0, height_param, color_param, 1, 75, 5)
    middle_time = time.time()
    test_chunk.update_detail(0)
    end_time = time.time()
    display_chunk(test_chunk)
    print(f"The chunk has been generated in: \033[;4m{middle_time - start_time:.5f}s\033[0m")
    print(f"The details has been created in: \033[;4m{end_time - middle_time:.5f}s\033[0m")
    print(f"The chunk takes exactly \033[;4m{format_size(get_total_size(test_chunk))}\033[0m in memory space")

    scale = 20
    pygame.init()
    screen = pygame.display.set_mode(((CHUNK_SIZE + 1) * scale, (CHUNK_SIZE + 1) * scale))
    clock = pygame.time.Clock()
    surface = pygame.surfarray.make_surface(test_chunk.color_data)

    running = True
    while running:
        # Handle Pygame events to keep the window responsive
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))
        for x in range(CHUNK_SIZE + 1):
            for y in range(CHUNK_SIZE + 1):
                pygame.draw.rect(screen, test_chunk.color_data[x, y],
                                 (x * scale, y * scale, (x + 1) * scale, (y + 1) * scale))
        pygame.display.flip()

        # Update clock
        clock.tick(60)

    pygame.quit()