import numpy as np
from scipy.spatial import Delaunay
import math
import noise
import pygame
import time
import bisect
from scipy.interpolate import CubicSpline
CHUNK_SIZE = 16
LG2_CS = math.floor(math.log2(CHUNK_SIZE))
# from new_engine.options import CHUNK_SIZE, LG2_CS

SIDE_LENGTH = 5
SCALE = 900 / CHUNK_SIZE / SIDE_LENGTH
JITTER_STRENGTH = 1 / 3

class HeightParams:
    """Classe de calcul de la hauteur d'un point par calcul mathématique"""
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
    __slots__ = ['num_points', 'x_values', 'y_values', 'denom_list']

    def __init__(self, points, scale: float = 1.0) -> None:
        self.num_points = len(points)
        
        # Precompute values for fast lookup
        self.x_values = tuple(p[0] for p in points)  # For binary search
        self.y_values = tuple(p[1] * scale for p in points)  # Y-values for interpolation
        self.denom_list = tuple(1 / (self.x_values[i] - self.x_values[i + 1])
                           for i in range(self.num_points - 1))

    def height_from_noise(self, noise_value: float) -> float:
        # Binary search (Dichotomy) to find the correct segment
        index = bisect.bisect_right(self.x_values, noise_value) - 1

        # Clamp to valid range
        if index < 0:
            return self.y_values[0]
        if index >= self.num_points - 1:
            return self.y_values[-1]

        # LERP using NumPy
        x0, x1 = self.x_values[index], self.x_values[index + 1]
        y0, y1 = self.y_values[index], self.y_values[index + 1]
        return np.interp(noise_value, [x0, x1], [y0, y1])


BIOME_POINTS = {
    # à chaque fois on met tous les points avec valeur x entre 0 et 1 triés avec leur valeur de hauteur respective,
    # Pour les valeurs entre les points on fait un mélange
    "plain": ((0.0, -0.3), (0.43, 0.0), (0.45, 0.05), (0.67, 0.1), (0.76, 0.2), (0.84, 0.67), (0.94, 0.82), (1.0, 1.0)), # plat
    "plateau": ((0.0, -0.3), (0.4, 0.0), (0.45, 0.18), (0.51, 0.19), (0.6, 0.26), (0.9, 0.88), (1.0, 1.0)), # plat avec falaise aux côtes
    "desert_dune": ((0.0, -0.2), (0.083, 0.0), (0.084, 0.065), (0.088, 0.085), (0.11, 0.11), (0.16, 0.09), (0.17, 0.07), (0.25, 0.11), (0.3, 0.1), # Wiggle around 0.1
                    (0.36, 0.125), (0.39, 0.165), (0.41, 0.13), (0.43, 0.145), (0.46, 0.17), (0.49, 0.18), (0.53, 0.17), # Wiggle around 0.15
                    (0.55, 0.225), (0.58, 0.18), (0.61, 0.185), (0.65, 0.22), (0.67, 0.24), # Wiggle around 0.2
                    (0.8, 0.3), (0.85, 0.6), (1.0, 1.0)), # désert de dunes
    "desert_rock": ((0.0, -0.3), (0.4, 0.0), (0.53, 0.11), (0.66, 0.22), (0.8, 0.98), (1.0, 1.0)), # plats avec grands rochers rouges
    "snowy": ((0.0, -0.3), (0.43, 0.0), (0.45, 0.05), (0.67, 0.1), (0.76, 0.2), (0.84, 0.47), (0.9, 0.62), (0.98, 0.9), (1.0, 1.0)), # plat enneigé
    "tundra": ((0.0, -0.3), (0.4, 0.0), (0.45, 0.18), (0.51, 0.19), (0.6, 0.26), (0.9, 0.88), (1.0, 1.0)), # plat avec falaise aux côtes enneigé
    "archipel": ((0.0, -0.4), (0.55, 0.0), (0.58, 0.05), (0.7, 0.14), (0.75, 0.25), (0.84, 0.4), (0.89, 0.68), (0.92, 0.83), (1.0, 1.0)), # îles
    "glaciers": ((0.0, -0.4), (0.5, 0.0), (0.53, 0.14), (0.57, 0.14), (0.6, 0.0), (0.64, -0.1), # first row glaciers
                 (0.68, 0.0), (0.69, 0.15), (0.74, 0.16), (0.75, 0.25), (0.84, 0.4), (0.89, 0.68), (0.92, 0.83), (1.0, 1.0)), # océan gelé
    "volcanos": ((0.0, -0.3), (0.38, 0.0), (0.4, 0.09), (0.45, 0.19), (0.46, 0.15), (0.62, 0.18), (0.66, 0.22), (0.75, 0.8), (0.82, 1.0), (0.86, 0.65), (1.0, 0.62)), # terre volcanique
}

BIOME_COLORS = {
    "plain": [(224, 199, 161),  # Beach
        (124, 162,  55), ( 89, 135,  51),  # Grass
        ( 39,  39,  39), ( 67,  57,  47), ( 74,  62,  53), ( 79,  73,  68),  # Mountain
        (255, 255, 255)],  # Peak

    "plateau": [(224, 199, 161),  # Beach
        (124, 162,  55), ( 89, 135,  51),  # Grass
        ( 39,  39,  39), ( 67,  57,  47), ( 74,  62,  53), ( 79,  73,  68),  # Mountain
        (255, 255, 255)],  # Peak
    
    "desert_dune": [(124, 162,  55),  # grass (oasis)
        (214, 166, 125), (231, 177, 130),  # Sand
        (230, 171, 120), (230, 171, 120), (247, 189, 139), (79,  73,  68),  # Mountain
        (255, 255, 255)],  # Peak
    
    "desert_rock": [(224, 199, 161),  # Beach
        (234, 199, 161), (248, 197, 138),  # Sand
        (165, 84, 59), (197, 104, 76), (211, 115, 71), (221, 147, 105),  # Mountain
        (255, 255, 255)],  # Peak (grass on top ?)

    "snowy": [(224, 199, 161),  # Beach
        (236, 247, 240), (229, 240, 241),  # Grass (under snow)
        (178, 179, 182), (207, 207, 209), (250, 250, 252), (255, 255, 255),  # Mountain
        (224, 237, 249)],  # Peak

    "tundra": [(224, 199, 161),  # Beach
        (236, 247, 240), (229, 240, 241),  # Grass (under snow)
        (178, 179, 182), (207, 207, 209), (250, 250, 252), (255, 255, 255),  # Mountain
        (224, 237, 249)],  # Peak
    
    "archipel": [(224, 199, 161),  # Beach
        (124, 162,  55),  # Grass
        ( 39,  39,  39), ( 67,  57,  47), ( 74,  62,  53), ( 79,  73,  68),  # Mountain
        (255, 255, 255)],  # Peak
    
    "glaciers": [(224, 237, 249),  # Ice
        (178, 179, 182), (207, 207, 209), (250, 250, 252), (255, 255, 255),  # Mountain
        (224, 237, 249)],  # Peak
    
    "volcanos": [(224, 199, 161),  # Beach
        ( 79,  73,  68), ( 74,  62,  53), ( 67,  57,  47), ( 39,  39,  39),  # Rocks
        (252, 90, 15), (252, 70, 15)], # lava
}

BIOME_HEIGHTS_LIMIT = {
    "plain": [0.46, 0.65, 0.71, 0.74, 0.76, 0.79, 0.85],
    "plateau": [0.4, 0.475, 0.54, 0.63, 0.69, 0.74, 0.8],
    "desert_dune": [0.16, 0.5, 0.71, 0.75, 0.8, 0.9, 0.95],
    "desert_rock": [0.43, 0.5, 0.7, 0.73, 0.75, 0.8, 0.95],
    "snowy": [0.48, 0.6, 0.76, 0.79, 0.81, 0.84, 0.93],
    "tundra": [0.45, 0.525, 0.59, 0.68, 0.74, 0.79, 0.89],
    "archipel": [0.6, 0.7, 0.76, 0.81, 0.85, 0.9],
    "glaciers": [0.76, 0.78, 0.81, 0.85, 0.9],
    "volcanos": [0.41, 0.6, 0.75, 0.83, 0.88, 0.92],
}

class SplineHeightParams:
    """Class for height parameters with spline calculation (smoothness)"""
    
    __slots__ = ['num_points', 'x_values', 'y_values', 'spline']

    def __init__(self, biome: str, scale: float = 1.0) -> None:
        """Class constructor

        Args:
            biome (str): biome name for the heights
            scale (float, optional): height scale factor. Defaults to 1.0.
        """
        points = BIOME_POINTS[biome]
        self.num_points = len(points)
        
        # Precompute values for smooth interpolation
        self.x_values = np.array([p[0] for p in points])  # For binary search
        self.y_values = np.array([p[1] * scale for p in points])  # Y-values for interpolation
        
        # Use Cubic Spline for smooth interpolation
        self.spline = CubicSpline(self.x_values, self.y_values, bc_type='natural')

    def height_from_noise(self, noise_value: float) -> float:
        """Height calculation for a given Perlin noise

        Args:
            noise_value (float): Perlin noise value

        Returns:
            float: height associated with noise value
        """
        return self.spline(noise_value)


class ColorParams:
    """Class for color parameters"""
    
    __slots__ = ['heights_limit', 'colors']

    def __init__(self, biome: str) -> None:
        """Class constructor
        
        Args:
            biome (str): biome name for color parameters"""
        """self.heights_limit = [0.005, 0.02, 0.25, 0.4, 0.45, 0.525, 0.59, 0.68, 0.74, 0.79, 0.85]
        self.colors = [( 21,  47,  88), ( 25,  54, 100), ( 33,  69, 120), ( 44,  87, 147), # Water
                       (224, 199, 161), # Beach
                       (124, 162,  55), ( 89, 135,  51), # Grass
                       ( 39,  39,  39), ( 67,  57,  47), ( 74,  62,  53), ( 79,  73,  68), # Mountain
                       (255, 255, 255)] # Peak"""
        self.heights_limit = BIOME_HEIGHTS_LIMIT[biome]
        self.colors = BIOME_COLORS[biome]

    def get_id_from_noise(self, noise_value: float) -> int:
        """Give the id of a point for a certain Perlin noise value

        Args:
            noise_value (float): Perlin noise value

        Returns:
            int: id of the point
        """
        return min(bisect.bisect_right(self.heights_limit, noise_value), 
                   len(self.colors) - 1)

    def get_color_from_id(self, id: int) -> tuple[int, int, int]:
        """Give the color for a certain id

        Args:
            id (int): input id

        Returns:
            tuple[int, int, int]: color associated with id
        """
        return self.colors[id]


class PerlinGenerator:
    """Perlin noise generation class"""
    
    __slots__ = ['height_params', 'color_params', 'seed', 'scale', 'octaves', 'persistence', 'lacunarity']
    
    def __init__(self, height_params: HeightParams | PointsHeightParams | SplineHeightParams, color_params: ColorParams,
                 seed: int = 0, scale: float = 1.0, octaves: int = 1,
                 persistence: float = 0.5, lacunarity: float = 2.0):
        """Class constructor

        Args:
            height_params (HeightParams | PointsHeightParams | SplineHeightParams):height parameters associated
            color_params (ColorParams): color parameters associated
            seed (int, optional): Perlin seed. Defaults to 0.
            scale (float, optional): inital frequence of Perlin noise. Defaults to 1.0.
            octaves (int, optional): number of fractal octaves. Defaults to 1.
            persistence (float, optional): weight of each octave. Defaults to 0.5.
            lacunarity (float, optional): weight of frequence of each octave. Defaults to 2.0.
        """
        self.height_params = height_params
        self.color_params = color_params
        self.seed = seed
        self.scale = scale
        self.octaves = octaves
        self.persistence = persistence
        self.lacunarity = lacunarity

    def noise_value(self, x: float, y: float, **overrides) -> float:
        """Return the Perlin noise value for a point in 2d

        Args:
            x (float): x-axis coordinate
            y (float): y-axis coordinate
            **overrides (Any): the kwargs to override the class attributes

        Returns:
            float: valeur du bruit de Perlin
        """
        # Use provided overrides or fall back to the object's default attributes
        params = {
            "octaves": self.octaves,
            "persistence": self.persistence,
            "lacunarity": self.lacunarity,
            "scale": self.scale,
            "seed": self.seed
        }
        params.update(overrides)  # Override defaults with any specified values

        perlin_value = noise.pnoise2(
            x / params["scale"], y / params["scale"],
            octaves=params["octaves"],
            persistence=params["persistence"],
            lacunarity=params["lacunarity"],
            base=params["seed"]
        )

        # Normalized value (experimental adjustment)
        noise_value = (perlin_value / max(0.5, (0.42 / params["octaves"] + 0.44)) + 1) / 2
        return np.clip(noise_value, 0, 1)  # Ensure within [0,1]


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
    __slots__ = ['noise', 'scale', 'coord', 'id_data', 'vertices', 'detail']

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
    
    def get_deterministic_rng(self, coord):
        """Returns a consistent jitter displacement based on coordinates and seed.
        Could take unecessary time."""
        return np.random.default_rng(abs(hash((*coord, 0x30997A84C, self.noise.seed))))

    def generate_detail(self, new_level_of_detail: float | int):
        """Generates vertex positions and IDs for the specified level of detail.

        This method populates vertex data and IDs based on Perlin noise values at the requested resolution.
        Higher levels of detail result in fewer vertices being processed.

        Args:
            new_level_of_detail (float | int): The target level of detail, where a higher value reduces resolution.
        """
        if new_level_of_detail > (self.detail or float('inf')):
            return
        
        default_rng = np.random.default_rng(abs(hash((*self.coord, 0xF1A308E2, self.noise.seed))))

        step = 2 ** int(new_level_of_detail * LG2_CS)
        for x in range(0, CHUNK_SIZE + 1, step):
            for y in range(0, CHUNK_SIZE + 1, step):
                if self.id_data[x, y] != 0:  # Already generated
                    continue
                
                # Correctly assign RNG based on position
                if y in (0, CHUNK_SIZE) or x in (0, CHUNK_SIZE):
                    rng = self.get_deterministic_rng(self.coord * CHUNK_SIZE + [x, y])
                    jitter_strength = JITTER_STRENGTH
                else:
                    rng = default_rng
                    jitter_strength = JITTER_STRENGTH * step
                jitter_x = rng.uniform(-jitter_strength, jitter_strength)
                jitter_y = rng.uniform(-jitter_strength, jitter_strength)
                
                sample_x, sample_y = (self.coord * CHUNK_SIZE) + [x + jitter_x, y + jitter_y]
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
    """Chunk mesh that can update its details"""
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
        return f"ChunkMesh<{self.chunk}{', NotLoaded' if self.vertex_data is None else ''}>"

class DelaunayChunkMesh:
    """Chunk mesh that can update its details using Delaunay triangulation"""
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
        
        # Generate grid of points
        points = []
        for x in range(0, CHUNK_SIZE + 1, step):
            for y in range(0, CHUNK_SIZE + 1, step):
                points.append((x, y))

        points = np.array(points)

        # Compute the Delaunay triangulation
        delaunay = Delaunay(points)

        # Create vertex data
        self.vertex_data = np.zeros(3 * len(delaunay.simplices), dtype=self.DTYPE)
        
        index = 0
        for simplex in delaunay.simplices:
            # Extract the triangle vertices (in 2D coordinates)
            vertices = [self.chunk.vertices[pt[0], pt[1]] for pt in points[simplex]]
            
            # Compute the normal of the triangle (in 3D space, assuming Z = 0)
            normal = np.cross(vertices[1] - vertices[0], vertices[2] - vertices[0])
            normal *= 1 / np.linalg.norm(normal)
            
            # Get the face ID
            face_id = max([self.chunk.id_data[pt[0], pt[1]] for pt in points[simplex]])
            
            # Store the vertices, normals, and face IDs for each triangle
            for i in range(3):
                self.vertex_data[index + i] = (vertices[i], normal, face_id)
            
            index += 3

        self.detail = new_level_of_detail

    def get_byte_size(self):
        return self.vertex_data.nbytes + self.chunk.get_chunk_size()

    def __repr__(self):
        return f"ChunkMesh<{self.chunk}{', NotLoaded' if self.vertex_data is None else ''}>"



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
        # color = [min(value + (sum(chunk_mesh.chunk.coord) % 2) * 30, 255) for value in color]

        a, b, c = [[int(ele[0][i] * scale) for i in (0, 2)] for ele in data]
        pygame.draw.polygon(screen, color, [a, b, c])

def generate_chunk(x_chunk, y_chunk, noise, detail: float = 1.0):
    chunk_terrain = ChunkTerrain(noise, x_chunk, y_chunk)
    chunk_terrain.generate_detail(detail)
    chunk_mesh = DelaunayChunkMesh(chunk_terrain)
    chunk_mesh.update_detail(detail)
    return chunk_mesh

if __name__ == "__main__":
    height_param = HeightParams()
    color_param = ColorParams("archipel")
    perlin_noise = PerlinGenerator(height_param, color_param, seed=2500, scale=30.0, octaves=10, persistence=0.5, lacunarity=2.0)

    # chunk = ChunkTerrain(perlin_noise, 0, 0)

    # sst = time.time()
    # chunk.generate_detail(0.3)
    # mmt = time.time()
    # chunk_mesh = ChunkMesh(chunk)
    # chunk_mesh.update_detail(0.3)
    # eet = time.time()

    # st = time.time()
    # chunk.generate_detail(0)
    # mt = time.time()
    # chunk_mesh = ChunkMesh(chunk)
    # chunk_mesh.update_detail(0)
    # et = time.time()
    # print(f"Time taken generating: {mmt - sst:.5f}s")
    # print(f"Time taken meshing: {eet - mmt:.5f}s")
    # print(f"Size of chunk: {format_size(chunk_mesh.get_byte_size())}")
    # print()
    # print(f"Time taken generating all data: {mt - st:.5f}s")
    # print(f"Time taken meshing to max detail: {et - mt:.5f}s")
    # print(f"Size of chunk: {format_size(chunk_mesh.get_byte_size())}")
    # print()
    # print(f"Total time: {et - sst:.5f}s")
    
    st = time.time()
    chunk_meshes = []
    for x in range(SIDE_LENGTH):
        for y in range(SIDE_LENGTH):
            chunk_mesh = generate_chunk(x, y, perlin_noise, 0.5)
            chunk_meshes.append(chunk_mesh)
    et = time.time()
    print(f"Size of chunks: {format_size(sum(chunk_mesh.get_byte_size() for chunk_mesh in chunk_meshes))}")
    print(f"Total time: {et-st:.5f}s")

    pygame.init()
    screen = pygame.display.set_mode((900, 900))
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
        for chunk_mesh in chunk_meshes:
            display_chunk(screen, chunk_mesh, SCALE)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
