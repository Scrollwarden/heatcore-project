import numpy as np
import math
import noise

import pygame

import time
from tqdm import tqdm

CHUNK_SIZE: int = 16
SCALE = 30

class HeightParams:
    __slots__ = ['x1', 'y1', 'p', 'q', 'a', 'b', 'scale']

    def __init__(self, scale: float = 1.0) -> None:
        self.x1: float = 0.6
        self.y1: float = 0.044
        self.p: float = 2
        self.q: float = 1
        self.a: float = self.y1 / math.pow(self.x1, self.p)
        self.b: float = (self.y1 - 1) / (math.pow(self.x1, self.q) - 1)
        self.scale = scale

    def height_from_noise(self, noise_value: float) -> float:
        if noise_value < self.x1:
            return self.a * math.pow(noise_value, self.p) * self.scale
        elif noise_value > self.x1:
            return (self.b * (math.pow(noise_value, self.q) - 1) + 1) * self.scale
        else:
            return self.y1 * self.scale


class ColorParams:
    __slots__ = ['heights_limit', 'colors']

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
    """Class for a chunk, contains all the necessary informations to render it or update its details.
    
    | Attribute     | Shape                                 | Description                                    |
    |---------------|---------------------------------------|------------------------------------------------|
    | `coord`       | `(2, )`                               | Coordinate of the coordinate system of chunks. |
    | `height_data` | `(chunk_size + 1, chunk_size + 1)`    | Grid of height values for each point.          |
    | `color_data`  | `(chunk_size + 1, chunk_size + 1, 3)` | Grid of RGB colors for the chunk.              |
    | `vertices`    | `(num_vertices, 3)`                   | List of unique 3D vertex positions.            |
    | `triangles`   | `(num_triangles, 3)`                  | Indices of vertices forming each triangle.     |
    | `colors`      | `(num_triangles, 3)`                  | List the color of each triangle.               |
    """
    __slots__ = ['coord', 'height_data', 'color_data', 'vertices', 'triangles', 'colors']

    def __init__(self, x_chunk: int, y_chunk: int, height_data, color_data) -> None:
        self.coord = np.array([x_chunk, y_chunk], dtype=np.int32)
        self.height_data = height_data
        self.color_data = color_data
        self.vertices = None
        self.triangles = None
        self.colors = None

    def update_detail(self, new_level_of_detail: int, progress_bar: bool = True) -> None:
        """Change the level of detail of a chunk depending on the distance and adjust triangles to be isosceles
        
        Args:
            new_level_of_detail (int): the detail of the chunk, 0 for best detail and math.log2(CHUNK_SIZE) - 1 for worst detail.
            scale (float): how much you spread the coordinates of the render

        Raises:
            ValueError: Whenever the level of detail is not between 0 and math.log2(CHUNK_SIZE) - 1.
        """
        if not isinstance(new_level_of_detail, int) or new_level_of_detail < 0 or new_level_of_detail >= math.log2(CHUNK_SIZE):
            raise ValueError(f"The level of detail ({new_level_of_detail}) is not correct,"
                             f"it should be an integer between 0 and {int(math.log2(CHUNK_SIZE)) - 1}")

        simplification_increment: int = 2 ** new_level_of_detail
        vertices_per_line: int = CHUNK_SIZE // simplification_increment + 1

        self.vertices = np.zeros(shape=(vertices_per_line ** 2, 3), dtype=float)
        self.triangles = np.zeros(shape=(2 * (vertices_per_line - 1) ** 2, 3), dtype=np.uint16)
        self.colors = np.zeros(shape=(2 * (vertices_per_line - 1) ** 2, 3), dtype=np.uint8)
        
        if progress_bar:
            tqdm_progress_bar = tqdm(total=(CHUNK_SIZE + 1) ** 2, desc=f"Changing details of chunk {tuple(self.coord)}", leave=False)
        
        index: int = 0
        triangle_index: int = 0
        for x in range(vertices_per_line):
            for y in range(vertices_per_line):
                # Vertices
                if y % 2 == 0:
                    self.vertices[index, :] = (self.coord[0] * CHUNK_SIZE + x, self.height_data[x, y], self.coord[1] * CHUNK_SIZE + y)
                else:
                    self.vertices[index, :] = (self.coord[0] * CHUNK_SIZE + x + 0.5, self.height_data[x, y], self.coord[1] * CHUNK_SIZE + y)

                if x < CHUNK_SIZE and y < CHUNK_SIZE:
                    # Triangles
                    if y % 2 == 0:
                        self.triangles[triangle_index, :] = (index, index + 1, index + vertices_per_line)
                        self.triangles[triangle_index + 1, :] = (index + 1, index + vertices_per_line + 1, index + vertices_per_line)
                    else:
                        self.triangles[triangle_index, :] = (index, index + vertices_per_line + 1, index + vertices_per_line)
                        self.triangles[triangle_index + 1, :] = (index + 1, index + vertices_per_line + 1, index)
                    
                    # Colors
                    self.colors[triangle_index, :] = self.color_data[x * simplification_increment, y * simplification_increment]
                    self.colors[triangle_index + 1, :] = self.color_data[x * simplification_increment, (y + 1) * simplification_increment]
                    triangle_index += 2
                
                index += 1
                if progress_bar:
                    tqdm_progress_bar.update(1)


def generate_chunk(x_chunk: int, y_chunk: int, height_arrangement: HeightParams, color_arrangement: ColorParams,
                   seed: int = None,
                   scale: float = 1.0,
                   octaves: int = 1,
                   persistence: float = 0.5,
                   lacunarity: float = 2.0,
                   progress_bar: bool = True) -> ChunkTerrain:
    height_data = np.zeros(shape=(CHUNK_SIZE + 1, CHUNK_SIZE + 1), dtype=np.float16)
    color_data = np.zeros(shape=(CHUNK_SIZE + 1, CHUNK_SIZE + 1, 3), dtype=np.uint8)

    if seed is None:
        raise ValueError("The seed can't be None")

    if progress_bar:
        tqdm_progress_bar = tqdm(total=(CHUNK_SIZE + 1) ** 2, desc=f"Generating chunk {(x_chunk, y_chunk)}", leave=False)
    for x in range(CHUNK_SIZE + 1):
        for y in range(CHUNK_SIZE + 1):
            sample_x, sample_y = (x_chunk * CHUNK_SIZE + x) / scale, (y_chunk * CHUNK_SIZE + y) / scale
            perlin_value = noise.pnoise2(sample_x, sample_y, octaves=octaves, persistence=persistence,
                                         lacunarity=lacunarity, base=seed)
            noise_value = max(0, min(1, (perlin_value / max(0.5, (0.42 / octaves + 0.44)) + 1) / 2))

            height_data[x, y] = height_arrangement.height_from_noise(noise_value)
            color_data[x, y, :] = color_arrangement.get_color_from_noise(noise_value)
            if progress_bar:
                tqdm_progress_bar.update(1)

    return ChunkTerrain(x_chunk, y_chunk, height_data, color_data)

def get_chunk_size(chunk: ChunkTerrain):
    return sum(chunk.__getattribute__(attribute).nbytes for attribute in chunk.__slots__)

# Function to format the size
def format_size(size_bytes):
    """Formats size in bytes into a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes}o"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f}Ko"
    else:
        return f"{size_bytes / 1024 ** 2:.1f}Mo"

def display_chunk(screen, chunk: ChunkTerrain):
    """Example of a function that could display a chunk on screen"""
    def display_triangle(a, b, c, color):
        """A function that displays a triangle. Here it doesn't display on screen, but it's just for reference"""
        #print(f"Triangle ({a}, {b}, {c}) displayed with color {color}")
        pygame.draw.polygon(screen, color, ((a[0] * SCALE, a[2] * SCALE),
                                            (b[0] * SCALE, b[2] * SCALE),
                                            (c[0] * SCALE, c[2] * SCALE)))

    if chunk.triangles is None:
        raise ValueError("The chunk needs to be loaded")

    for i in range(len(chunk.triangles)):
        triangle_vertices = [chunk.vertices[vertex_index] for vertex_index in chunk.triangles[i]]
        triangle_color = chunk.colors[i]
        display_triangle(*triangle_vertices, triangle_color)


if __name__ == "__main__":
    height_param = HeightParams()
    color_param = ColorParams()
    start_time = time.time()
    test_chunk = generate_chunk(0, 0, height_param, color_param, 1, 75, 5)
    middle_time = time.time()
    test_chunk.update_detail(0, 1)
    end_time = time.time()
    print(f"The chunk has been generated in: \033[;4m{middle_time - start_time:.5f}s\033[0m")
    print(f"The details has been created in: \033[;4m{end_time - middle_time:.5f}s\033[0m")
    print(f"The chunk takes exactly \033[;4m{format_size(get_chunk_size(test_chunk))}\033[0m in memory space")

    pygame.init()
    screen = pygame.display.set_mode(((CHUNK_SIZE + 1) * SCALE, (CHUNK_SIZE + 1) * SCALE))
    clock = pygame.time.Clock()
    surface = pygame.surfarray.make_surface(test_chunk.color_data)

    detail = 0
    running = True
    while running:
        # Handle Pygame events to keep the window responsive
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    detail -= 1
                elif event.key == pygame.K_DOWN:
                    detail += 1
                detail = max(0, min(detail, int(math.log2(CHUNK_SIZE))))
                test_chunk.update_detail(detail, 1)


        screen.fill((0, 0, 0))
        display_chunk(screen, test_chunk)
        pygame.display.flip()

        # Update clock
        clock.tick(60)

    pygame.quit()