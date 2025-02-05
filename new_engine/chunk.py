import numpy as np
import math
import noise
import pygame
import time
from new_engine.options import CHUNK_SIZE, LG2_CS

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
        self.heights_limit = [0.005, 0.25, 0.3, 0.35, 0.45, 0.525, 0.59, 0.68, 0.74, 0.79, 0.85]
        self.colors = [( 21,  47,  88), ( 25,  54, 100), ( 33,  69, 120), ( 44,  87, 147), # Water
                       #( 50,  45,  47), ( 80,  60,  57), (120,  83,  65), (174, 146,  87),  # Underwater
                       (245, 222, 154),  # Beach
                       (124, 162,  55), ( 89, 135,  51),  # Grass
                       ( 39,  39,  39), ( 67,  57,  47), ( 74,  62,  53), ( 79,  73,  68),  # Mountain
                       (255, 255, 255)]  # Peak

    def get_id_from_noise(self, height: float) -> int:
        for i, height_limit in enumerate(self.heights_limit):
            if height <= height_limit:
                return i
        return len(self.colors) - 1

    def get_color_from_id(self, id: int) -> tuple[int, int, int]:
        return self.colors[id]

class PerlinGenerator:
    def __init__(self, height_params: HeightParams | PointsHeightParams, color_params: ColorParams,
                 seed: int = 0, scale: float = 1.0, octaves: int = 1,
                 persistence: float = 0.5, lacunarity: float = 2.0):
        self.height_params = height_params
        self.color_params = color_params
        self.seed = seed
        self.scale = scale
        self.octaves = octaves
        self.persistence = persistence
        self.lacunarity = lacunarity

    def noise_value(self, x: float, y: float) -> float:
        perlin_value = noise.pnoise2(x / self.scale, y / self.scale, octaves=self.octaves, persistence=self.persistence,
                                     lacunarity=self.lacunarity, base=self.seed)

        # normalized value (not perfect but experimentally correct)
        noise_value = (perlin_value / max(0.5, (0.42 / self.octaves + 0.44)) + 1) / 2
        return np.clip(noise_value, 0, 1) # just to be sure

class ChunkTerrain:
    """Represents a terrain chunk, containing information about its vertices and associated data.

    This class generates vertex positions and assigns IDs based on the requested level of detail.
    It does not handle rendering or maintain a mesh representation.

    | Attribute      | Description                                    | Shape/Data type                    |
    | -------------- | ---------------------------------------------- | ---------------------------------- |
    | `scale`        | By how much do we scale the vertices.          | float                              |
    | `noise`        | Used for perlin generation of noise.           | PerlinGenerator                    |
    | `coord`        | Coordinate of the coordinate system of chunks. | `(2, )`                            |
    | `vertices`     | List of all vertices of the chunk.             | `(chunk_size + 1, chunk_size + 1)` |
    | `id_data`      | Id of each point in the chunk.                 | `(chunk_size + 1, chunk_size + 1)` |
    | `detail`       | The maximum detail generated.                  | float                              |
    """
    __slots__ = ['noise', 'scale', 'coord', 'id_data', 'vertices', 'detail', ]

    def __init__(self, perlin_generator: PerlinGenerator, x_chunk: int, y_chunk: int, scale: float = 1.0) -> None:
        """Initializes a new ChunkTerrain instance, generating placeholders for vertex and ID data.

        Args:
            perlin_generator (PerlinGenerator): The Perlin noise generator for terrain generation.
            x_chunk (int): The X-coordinate of the chunk in the grid.
            y_chunk (int): The Y-coordinate of the chunk in the grid.
        """
        self.noise = perlin_generator
        self.scale = scale
        self.coord = np.array([x_chunk, y_chunk], dtype=np.int32)
        self.vertices = np.zeros(shape=(CHUNK_SIZE + 1, CHUNK_SIZE + 1, 3), dtype=np.float32)
        self.id_data = np.zeros(shape=(CHUNK_SIZE + 1, CHUNK_SIZE + 1), dtype=np.uint8)
        self.detail: float | None = None

    def generate_detail(self, new_level_of_detail: float | int):
        """Generates vertex positions and IDs for the specified level of detail.

        This method populates vertex data and IDs based on Perlin noise values at the requested resolution.
        Higher levels of detail result in fewer vertices being processed.

        Args:
            new_level_of_detail (float | int): The target level of detail, where a higher value reduces resolution.
        """
        if new_level_of_detail > (self.detail or float('inf')):
            return

        step = 2 ** int(new_level_of_detail * LG2_CS)
        for x in range(0, CHUNK_SIZE + 1, step):
            for y in range(0, CHUNK_SIZE + 1, step):
                if self.id_data[x, y] != 0:
                    continue
                sample_x, sample_y = (self.coord * CHUNK_SIZE) + [x, y]
                noise_value = self.noise.noise_value(sample_x, sample_y)
                height_value = self.noise.height_params.height_from_noise(noise_value)
                self.vertices[x, y] = [sample_x, height_value, sample_y]
                self.vertices[x, y] *= self.scale
                self.id_data[x, y] = self.noise.color_params.get_id_from_noise(noise_value)

        self.detail = new_level_of_detail

    def get_chunk_size(self):
        """Computes the memory size of the chunk's data.

        Returns:
            int: Total memory size of the chunk's attributes in bytes.
        """
        return sum(self.__getattribute__(attribute).nbytes for attribute in self.__slots__
                   if type(self.__getattribute__(attribute)) is np.ndarray)

    def __repr__(self) -> str:
        """Provides a string representation of the ChunkTerrain instance.

        Returns:
            str: A string containing the chunk's coordinates and detail level.
        """
        return f"ChunkTerrain<coord={self.coord}, detail={self.detail}>"

class ChunkMesh:
    """Chunk mesh that can update its details

    """
    DTYPE = np.dtype([
        ('position', np.float32, (3,)),  # 3 floats for vertex position (x, y, z)
        ('normal', np.float32, (3,)),  # 3 floats for face normal (nx, ny, nz)
        ('id', np.uint8)  # 1 unsigned int for triangle ID
    ])

    def __init__(self, chunk):
        self.chunk = chunk

        self.vertex_data = None
        self.detail = None

    def update_detail(self, new_level_of_detail):
        if not (type(new_level_of_detail) in (float, int) and 0 <= new_level_of_detail <= 1):
            raise ValueError(f"The level of detail ({new_level_of_detail}) is not correct,"
                             "it should be an float between 0 and 1")

        if new_level_of_detail > self.chunk.detail:
            self.chunk.update_detail(new_level_of_detail)

        step = 1 << int(LG2_CS * new_level_of_detail)
        self.vertex_data = np.zeros(6 * (CHUNK_SIZE // step) ** 2, dtype=self.DTYPE)

        index = 0
        for x in range(0, CHUNK_SIZE + 1, step):
            for y in range(0, CHUNK_SIZE + 1, step):
                if x == CHUNK_SIZE or y == CHUNK_SIZE:
                    continue

                # Triangles
                if (x // step * y // step) % 2 == 0:
                    triangles = (((x, y), (x + step, y), (x, y + step)),
                                 ((x + step, y + step), (x, y + step), (x + step, y)))
                else:
                    triangles = (((x, y + step), (x, y), (x + step, y + step)),
                                 ((x + step, y), (x + step, y + step), (x, y)))

                # ID taken from the highest point in the triangle
                for k, triangle in enumerate(triangles):
                    vertices = [self.chunk.vertices[i, j] for i, j in triangle]
                    normal = np.cross(vertices[2] - vertices[1], vertices[2] - vertices[0])
                    normal *= 1 / np.linalg.norm(normal)
                    face_id = max([self.chunk.id_data[i, j] for i, j in triangle])
                    for l in range(3):
                        self.vertex_data[index + 3 * k + l] = (vertices[l], normal, face_id)
                index += 6

        self.detail = new_level_of_detail

    def get_byte_size(self):
        return self.vertex_data.nbytes + self.chunk.get_chunk_size()

    def __repr__(self):
        return f"ChunkMesh<{self.chunk}{", NotLoaded" if self.vertex_data is None else ""}>"

# Function to format the size
def format_size(size_bytes):
    """Formats size in bytes into a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes}o"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f}Ko"
    else:
        return f"{size_bytes / 1024 ** 2:.1f}Mo"


def display_chunk(screen, chunk_mesh: ChunkMesh, scale: float | int):
    """Display a chunk on the screen with optional offsets for positioning."""
    if chunk_mesh.chunk.detail is None:
        raise ValueError("The chunk needs to be loaded")

    length = len(chunk_mesh.vertex_data) // 3
    for i in range(length):
        data = chunk_mesh.vertex_data[i * 3: i * 3 + 3]
        normal = data[0][1]
        face_id = data[0][2]
        color = chunk_mesh.chunk.noise.color_params.get_color_from_id(face_id)

        a, b, c = [tuple(int(axis * scale) for axis in ele[0]) for ele in data]
        pygame.draw.polygon(screen, color, [
            (a[0], a[2]),
            (b[0], b[2]),
            (c[0], c[2])
        ])

if __name__ == "__main__":
    height_param = HeightParams()
    color_param = ColorParams()
    perlin_noise = PerlinGenerator(height_param, color_param, seed=2, scale=30.0, octaves=5, persistence=0.5, lacunarity=2.0)

    chunk = ChunkTerrain(perlin_noise, 0, 0)

    sst = time.time()
    chunk.generate_detail(0.3)
    mmt = time.time()
    chunk_mesh = ChunkMesh(chunk)
    chunk_mesh.update_detail(0.3)
    eet = time.time()

    st = time.time()
    chunk.generate_detail(0)
    mt = time.time()
    chunk_mesh = ChunkMesh(chunk)
    chunk_mesh.update_detail(0)
    et = time.time()
    print(f"Time taken generating: {mmt - sst:.5f}s")
    print(f"Time taken meshing: {eet - mmt:.5f}s")
    print(f"Size of chunk: {format_size(chunk_mesh.get_byte_size())}")
    print()
    print(f"Time taken generating all data: {mt - st:.5f}s")
    print(f"Time taken meshing to max detail: {et - mt:.5f}s")
    print(f"Size of chunk: {format_size(chunk_mesh.get_byte_size())}")
    print()
    print(f"Total time: {et - sst:.5f}s")

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

        screen.fill((0, 0, 0))

        # Display all chunks
        display_chunk(screen, chunk_mesh, SCALE)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
