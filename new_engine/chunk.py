import numpy as np
import math
import noise

import pygame

import time
from tqdm import tqdm

CHUNK_SIZE: int = 16
SCALE = 900 / CHUNK_SIZE

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

class PointsHeightParams:
    __slots__ = ['points', 'denom_list']

    def __init__(self, points, scale: float) -> None:
        self.points = [(point[0], point[1] * scale) for point in points]
        self.denom_list = [1 / (points[i][0] - points[i + 1][0]) for i in range(len(self.points) - 1)]

    def height_from_noise(self, noise_value: float) -> float:
        index = 0
        while index < len(self.points) - 1 and self.points[index + 1][0] < noise_value:
            index += 1
        h = (noise_value - self.points[index + 1][0]) * self.denom_list[index]
        return h * self.points[index][1] + (1 - h) * self.points[index + 1][1]

class ColorParams:
    __slots__ = ['heights_limit', 'colors']

    def __init__(self) -> None:
        """self.heights_limit = [0.005, 0.02, 0.25, 0.4, 0.45, 0.525, 0.59, 0.68, 0.74, 0.79, 0.85]
        self.colors = [( 21,  47,  88), ( 25,  54, 100), ( 33,  69, 120), ( 44,  87, 147), # Water
                       (245, 222, 154), # Beach
                       (124, 162,  55), ( 89, 135,  51), # Grass
                       ( 39,  39,  39), ( 67,  57,  47), ( 74,  62,  53), ( 79,  73,  68), # Mountain
                       (255, 255, 255)] # Peak"""
        self.heights_limit = [0.005, 0.2, 0.25, 0.3, 0.45, 0.525, 0.59, 0.68, 0.74, 0.79, 0.85]
        self.colors = [(50, 45, 47), (80, 60, 57), (120, 83, 65), (174, 146, 87),  # Underwater
                       (245, 222, 154),  # Beach
                       (124, 162, 55), (89, 135, 51),  # Grass
                       (39, 39, 39), (67, 57, 47), (74, 62, 53), (79, 73, 68),  # Mountain
                       (255, 255, 255)]  # Peak

    def get_id_from_noise(self, height: float) -> int:
        for i, height_limit in enumerate(self.heights_limit):
            if height <= height_limit:
                return i
        return len(self.colors) - 1

    def get_color_from_id(self, id: int) -> tuple[int, int, int]:
        return self.colors[id]

class ChunkTerrain:
    """Class for a chunk, contains all the necessary information to render it or update its details.
    
    | Attribute      | Shape                               | Description                                    |
    |----------------|-------------------------------------|------------------------------------------------|
    | `coord`        | `(2, )`                             | Coordinate of the coordinate system of chunks. |
    | `height_data`  | `(chunk_size + 1, chunk_size + 1)`  | Grid of height values for each point.          |
    | `id_data`      | `(chunk_size + 1, chunk_size + 1)`  | Grid of id value for each point.               |
    | `vertices`     | `(num_vertices, 3)`                 | List of unique 3D vertex positions.            |
    | `triangles`    | `(num_triangles, 3)`                | Indices of vertices forming each triangle.     |
    | `triangle_ids` | `(num_triangles, )`                 | List the id of each triangle.                  |
    | `detail`       | No shape, it's just an integer/None | Current detail of the chunk.                   |
    """
    __slots__ = ['coord', 'height_data', 'id_data', 'vertices', 'triangles', 'triangle_ids', 'detail', ]

    def __init__(self, x_chunk: int, y_chunk: int, height_data, id_data) -> None:
        self.coord = np.array([x_chunk, y_chunk], dtype=np.int32)
        self.height_data = height_data
        self.id_data = id_data
        self.vertices = None
        self.triangles = None
        self.triangle_ids = None
        self.detail: None | int = None

    def update_detail(self, new_level_of_detail: int, progress_bar: bool = False) -> None:
        """Change the level of detail of a chunk depending on the distance and adjust triangles to be isosceles
        
        Args:
            new_level_of_detail (int): the detail of the chunk, 0 for best detail and math.log2(CHUNK_SIZE) - 1 for worst detail.
            progress_bar (bool): add in a progress bar or not to display progress. Defaults to False

        Raises:
            ValueError: Whenever the level of detail is not between 0 and math.log2(CHUNK_SIZE) - 1.
        """

        if not (type(new_level_of_detail) is int and 0 <= new_level_of_detail <= math.log2(CHUNK_SIZE)):
            raise ValueError(f"The level of detail ({new_level_of_detail}) is not correct,"
                             f"it should be an integer between 0 and {int(math.log2(CHUNK_SIZE))}")

        simplification_increment: int = 2 ** new_level_of_detail
        vertices_per_line: int = CHUNK_SIZE // simplification_increment + 1

        types = [type for i, type in enumerate((np.uint8, np.uint16, np.uint32, np.uint64))
                 if 4 << i >= np.log2(vertices_per_line)]
        triangles_dtype = types[0]

        self.vertices = np.zeros(shape=(vertices_per_line ** 2, 3), dtype=float)
        self.triangles = np.zeros(shape=(2 * (vertices_per_line - 1) ** 2, 3), dtype=triangles_dtype)
        self.triangle_ids = np.zeros(shape=(2 * (vertices_per_line - 1) ** 2,), dtype=np.uint8)
        
        if progress_bar:
            tqdm_progress_bar = tqdm(total=(CHUNK_SIZE + 1) ** 2, desc=f"Changing details of chunk {tuple(self.coord)}", leave=False)
        
        index: int = 0
        triangle_index: int = 0
        for x in range(vertices_per_line):
            for y in range(vertices_per_line):
                # Vertices
                offset = 0.0
                self.vertices[index, :] = (self.coord[0] * CHUNK_SIZE + (x + offset) * simplification_increment,
                                           self.height_data[x, y],
                                           self.coord[1] * CHUNK_SIZE + y)

                if x < vertices_per_line - 1 and y < vertices_per_line - 1:
                    # Triangles
                    if y % 2 == 0:
                        self.triangles[triangle_index, :] = (index, index + 1, index + vertices_per_line)
                        self.triangles[triangle_index + 1, :] = (index + vertices_per_line + 1, index + vertices_per_line, index + 1)
                    else:
                        self.triangles[triangle_index, :] = (index + vertices_per_line, index, index + vertices_per_line + 1)
                        self.triangles[triangle_index + 1, :] = (index + 1, index + vertices_per_line + 1, index)

                    # Colors taken from the highest point in the triangle
                    for k in range(2):
                        triangle = self.triangles[triangle_index + k]
                        points = [tuple(k * simplification_increment for k in divmod(ind, vertices_per_line)) for ind in triangle]
                        self.triangle_ids[triangle_index + k] = max(self.id_data[j, i] for j, i in points)
                    triangle_index += 2
                
                index += 1
                if progress_bar:
                    tqdm_progress_bar.update(1)

        self.detail = new_level_of_detail

    def __repr__(self) -> str:
        return f"ChunkTerrain<coord={self.coord}, detail={self.detail}>"

def generate_chunk(x_chunk: int, y_chunk: int,
                   height_arrangement: HeightParams | PointsHeightParams,
                   color_arrangement: ColorParams,
                   seed: int = 0,
                   scale: float = 1.0,
                   octaves: int = 1,
                   persistence: float = 0.5,
                   lacunarity: float = 2.0,
                   progress_bar: bool = False) -> ChunkTerrain:
    height_data = np.zeros(shape=(CHUNK_SIZE + 1, CHUNK_SIZE + 1), dtype=np.float16)
    id_data = np.zeros(shape=(CHUNK_SIZE + 1, CHUNK_SIZE + 1), dtype=np.uint8)

    if progress_bar:
        tqdm_progress_bar = tqdm(total=(CHUNK_SIZE + 1) ** 2, desc=f"Generating chunk {(x_chunk, y_chunk)}", leave=False)
    for x in range(CHUNK_SIZE + 1):
        for y in range(CHUNK_SIZE + 1):
            sample_x, sample_y = (x_chunk * CHUNK_SIZE + x) / scale, (y_chunk * CHUNK_SIZE + y) / scale
            perlin_value = noise.pnoise2(sample_x, sample_y, octaves=octaves, persistence=persistence,
                                         lacunarity=lacunarity, base=seed)

            # normalized value (not perfect but experimentally correct)
            noise_value = max(0, min(1, (perlin_value / max(0.5, (0.42 / octaves + 0.44)) + 1) / 2))

            height_data[x, y] = height_arrangement.height_from_noise(noise_value)
            id_data[x, y] = color_arrangement.get_id_from_noise(noise_value)
            if progress_bar:
                tqdm_progress_bar.update(1)

    return ChunkTerrain(x_chunk, y_chunk, height_data, id_data)

def get_chunk_size(chunk: ChunkTerrain):
    return sum(chunk.__getattribute__(attribute).nbytes for attribute in chunk.__slots__
               if type(chunk.__getattribute__(attribute)) not in (str, bool, int, float))

# Function to format the size
def format_size(size_bytes):
    """Formats size in bytes into a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes}o"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f}Ko"
    else:
        return f"{size_bytes / 1024 ** 2:.1f}Mo"

def display_chunk(screen, chunk: ChunkTerrain, color_params: ColorParams, scale, offset_x=0, offset_y=0):
    """Display a chunk on the screen with optional offsets for positioning."""
    def display_triangle(a, b, c, color):
        """Display a single triangle on the screen."""
        pygame.draw.polygon(screen, color, [
            ((a[0] + offset_x) * scale, (a[2] + offset_y) * scale),
            ((b[0] + offset_x) * scale, (b[2] + offset_y) * scale),
            ((c[0] + offset_x) * scale, (c[2] + offset_y) * scale)
        ])

    if chunk.detail is None:
        raise ValueError("The chunk needs to be loaded")

    for i in range(len(chunk.triangles)):
        triangle_vertices = [chunk.vertices[vertex_index] for vertex_index in chunk.triangles[i]]
        triangle_color = color_params.get_color_from_id(chunk.triangle_ids[i])
        display_triangle(*triangle_vertices, triangle_color)

def generate_chunks(radius):
    chunks = {}
    start_time = time.time()
    for x in range(-radius, radius + 1):
        for y in range(-radius, radius + 1):
            chunk = generate_chunk(x, y, height_param, color_param, 2, 75, 5, progress_bar=False)
            chunk.update_detail(0)
            chunks[(x, y)] = chunk

    render_time = time.time() - start_time
    print(f"All chunks generated in: \033[;4m{render_time:.5f}s\033[0m")
    print(f"Space taken by chunks: {format_size(sum(get_chunk_size(chunk) for chunk in chunks.values()))}")
    return chunks

if __name__ == "__main__":
    height_param = HeightParams()
    color_param = ColorParams()
    radius = 3
    scale = SCALE / radius

    chunks = generate_chunks(radius)

    pygame.init()
    screen = pygame.display.set_mode((CHUNK_SIZE * SCALE, CHUNK_SIZE * SCALE))
    clock = pygame.time.Clock()

    detail = 0
    running = True
    while running:
        # Handle Pygame events to keep the window responsive
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                last_params = (detail, scale)
                if event.key == pygame.K_UP:
                    detail = max(0, detail - 1)
                elif event.key == pygame.K_DOWN:
                    detail = min(int(math.log2(CHUNK_SIZE)), detail + 1)
                elif event.key == pygame.K_z:  # Increase grid radius
                    radius += 1
                    chunks = generate_chunks(radius)
                elif event.key == pygame.K_s:  # Decrease grid radius
                    radius = max(1, radius - 1)
                    chunks = generate_chunks(radius)

                scale = SCALE / radius
                if last_params != (detail, scale):
                    for chunk in chunks.values():
                        chunk.update_detail(detail)

        screen.fill((0, 0, 0))

        # Display all chunks
        for (cx, cy), chunk in chunks.items():
            display_chunk(screen, chunk, color_param, scale)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()