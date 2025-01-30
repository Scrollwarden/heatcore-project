import time

from new_engine.chunk import ChunkTerrain, ColorParams, PointsHeightParams, PerlinGenerator, CHUNK_SIZE, LG2_CS
from meshes.chunk_mesh import ChunkMesh
import queue
import threading

from new_engine.shader_program import ShaderProgram
from collections import deque


class Scene:
    CHUNK_SCALE = 8.0 # By how much we scale every axis
    HEIGHT_SCALE = 5.0 # By how much we scale the height
    INV_NOISE_SCALE = 0.06 # How much info we put in a chunk

    def __init__(self, app):
        self.radius = 9
        self.radius_squared = self.radius ** 2
        self.app = app

        points = ((0.0, -0.2), (0.4, 0.0), (0.45, 0.1), (0.5, 0.2), (0.6, 0.26), (1.0, 1.0))
        self.height_params = PointsHeightParams(points, self.HEIGHT_SCALE)
        self.color_params = ColorParams()
        self.noise = PerlinGenerator(self.height_params, self.color_params,
                                     seed=2, scale=1 / self.INV_NOISE_SCALE, octaves=5)
        self.shader_programs = {string: ShaderProgram(self.app, self.color_params, string) for string in ("chunk",)}

        self.result_queue = queue.Queue()
        self.threads = []
        self.threads_limit = 5
        self.semaphore = threading.Semaphore(self.threads_limit)

        self.chunk_meshes = {}
        self.chunks_loading = set()
        self.chunks_to_load_queue = deque()
        self.chunks_to_load_dic = {}
        self.chunks_to_load_set = set()
        self.tasks_per_frame = 1

    def generate_chunk_worker(self, coord, detail):
        """Worker function for generating chunks and rendering."""
        chunk = ChunkTerrain(self.noise, coord[0], coord[1], self.CHUNK_SCALE)
        chunk_mesh = ChunkMesh(self.app, chunk)
        chunk_mesh.update_detail(detail)
        self.result_queue.put((coord, chunk_mesh))

    def update_chunks(self):
        """Distribute chunk generation tasks across multiple frames."""
        st = time.time()
        #print(f"Chunks to load: {self.chunks_to_load_dic}")
        tasks_this_frame = 0
        keys_used = []

        if tasks_this_frame < self.tasks_per_frame and len(self.threads) < self.threads_limit:
            for coord in self.chunks_to_load_dic.keys():
                self.chunks_to_load_set.remove(coord)
                t = threading.Thread(
                    target=self.generate_chunk_worker,
                    args=(coord, self.chunks_to_load_dic[coord])
                )
                t.start()
                self.threads.append(t)
                self.chunks_loading.add(coord)
                keys_used.append(coord)
                tasks_this_frame += 1

                if tasks_this_frame >= self.tasks_per_frame or len(self.threads) >= self.threads_limit:
                    break
        for key in keys_used:
            del self.chunks_to_load_dic[key]

        self.threads = [t for t in self.threads if t.is_alive()]

        temp = set()
        while not self.result_queue.empty():
            coord, chunk_mesh = self.result_queue.get()
            if chunk_mesh.detail is not None:
                chunk_mesh.init_context()
            self.chunk_meshes[coord] = chunk_mesh
            #print(f"Attempting to remove {coord} from {self.chunks_loading}")
            self.chunks_loading.remove(coord)
            temp.add(coord)

        #print(f"Chunks loading: {self.chunks_loading}")
        #print(f"Chunks that finished loading: {temp}")

    def update(self):
        """Update chunks and load new ones."""
        player_position = self.app.camera.position / (CHUNK_SIZE * self.CHUNK_SCALE)
        keys_to_delete = [(i, j) for i, j in self.chunk_meshes.keys()
                          if (player_position.x - i - 0.5) ** 2 + (player_position.z - j - 0.5) ** 2 > self.radius_squared]
        for key in keys_to_delete:
            del self.chunk_meshes[key]

        for i in range(-self.radius, self.radius + 1):
            for j in range(-self.radius, self.radius + 1):
                int_pos = (int(player_position.x) + i, int(player_position.z) + j)
                distance_sq = (player_position.x - i - 0.5) ** 2 + (player_position.z - j - 0.5) ** 2
                if distance_sq > self.radius_squared:
                    continue # Don't load chunks too far away

                if int_pos in self.chunks_loading:
                    continue # Don't reload a chunk being loaded loaded

                detail = distance_sq / self.radius_squared
                if int_pos in self.chunk_meshes:
                    chunk_detail = int(LG2_CS * self.chunk_meshes[int_pos].detail)
                    if chunk_detail == int(LG2_CS * detail):
                        continue # Don't load a chunk with same detail
                self.chunks_to_load_dic[int_pos] = detail
                self.chunks_to_load_set.add(int_pos)

        # Handle chunk generation and update details
        self.update_chunks()

    def render(self):
        """Render all chunks within the active radius."""
        self.update()
        player_position = self.app.camera.position / (CHUNK_SIZE * self.CHUNK_SCALE)

        for (i, j) in self.chunk_meshes.keys():
            chunk_mesh = self.chunk_meshes[(i, j)]
            if chunk_mesh.detail is None:
                continue
            distance_sq = (player_position.x - i - 0.5) ** 2 + (player_position.z - j - 0.5) ** 2
            chunk_mesh.update_model_matrix(distance_sq / self.radius_squared)
            chunk_mesh.render()

    def destroy(self):
        """Clean up resources."""
        self.semaphore.acquire()
        for t in self.threads:
            t.join()

        [obj.destroy() for obj in self.chunk_meshes.values()]
        [shader.destroy() for shader in self.shader_programs.values()]

