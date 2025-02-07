import glm
import numpy as np
import threading, queue
import struct
import time

from new_engine.chunk import ChunkTerrain, ColorParams, PointsHeightParams, PerlinGenerator
from new_engine.meshes.chunk_mesh import ChunkMesh, CHUNK_SIZE, LG2_CS
from new_engine.options import CHUNK_SCALE, HEIGHT_SCALE, INV_NOISE_SCALE, THREADS_LIMIT, TASKS_PER_FRAME
from new_engine.shader_program import open_shaders


class ChunkManager:
    def __init__(self, app):
        self.radius = 10
        self.radius_squared = self.radius ** 2
        self.app = app

        points = ((0.0, -0.5), (0.4, 0.0), (0.45, 0.1), (0.5, 0.2), (0.6, 0.26), (1.0, 1.0))
        self.height_params = PointsHeightParams(points, HEIGHT_SCALE)
        self.color_params = ColorParams()
        self.noise = PerlinGenerator(self.height_params, self.color_params,
                                     seed=2, scale=100 / INV_NOISE_SCALE, octaves=5)
        self.chunk_shader = open_shaders(self.app, 'chunk')
        self.init_shader()

        self.result_queue = queue.Queue()
        self.threads = []
        self.threads_limit = THREADS_LIMIT
        self.semaphore = threading.Semaphore(self.threads_limit)

        self.chunk_meshes = {}
        self.chunks_loading = set()
        self.chunks_to_load_dic = {}
        self.chunks_to_load_set = set()
        self.tasks_per_frame = TASKS_PER_FRAME
    
    def init_shader(self):
        # light
        self.chunk_shader['light.position'].write(self.app.light.position)
        self.chunk_shader['light.Ia'].write(self.app.light.Ia)
        self.chunk_shader['light.Id'].write(self.app.light.Id)
        self.chunk_shader['light.Is'].write(self.app.light.Is)
        # mvp
        colors_256 = np.zeros((256, 3), dtype=np.float32)
        colors_256[:len(self.color_params.colors)] = self.color_params.colors
        colors_256 *= 1 / 255
        self.chunk_shader['colors'].write(colors_256.tobytes())
        self.chunk_shader['m_proj'].write(self.app.camera.m_proj)
        self.chunk_shader['m_model'].write(glm.mat4())

    def generate_chunk_worker(self, coord, detail):
        """Worker function for generating chunks and rendering."""
        chunk = ChunkTerrain(self.noise, coord[0], coord[1], CHUNK_SCALE)
        chunk_mesh = ChunkMesh(self.app, chunk)
        chunk_mesh.update_detail(detail)
        self.result_queue.put((coord, chunk_mesh))
    
    def generate_chunks(self):
        """Update chunks and load new ones."""
        player_position = self.app.player.position.xz / (CHUNK_SIZE * CHUNK_SCALE)
        player_chunk_coord = glm.vec2(glm.floor(player_position.x), glm.floor(player_position.y))
        keys_to_delete = [chunk_coord for chunk_coord in self.chunk_meshes.keys()
                          if glm.length2(player_position - chunk_coord - 0.5) > self.radius_squared]
        for key in keys_to_delete:
            del self.chunk_meshes[key]

        for i in range(-self.radius, self.radius + 1):
            for j in range(-self.radius, self.radius + 1):
                chunk_position = player_chunk_coord + (i, j)
                distance_sq = glm.length2(player_position - chunk_position - 0.5)
                if distance_sq > self.radius_squared:
                    continue # Don't load chunks too far away

                chunk_coord = tuple(chunk_position)
                if chunk_coord in self.chunks_loading:
                    continue # Don't reload a chunk being loaded loaded

                detail = distance_sq / self.radius_squared
                if chunk_coord in self.chunk_meshes:
                    chunk_detail = int(LG2_CS * self.chunk_meshes[chunk_coord].detail)
                    if chunk_detail == int(LG2_CS * detail):
                        continue # Don't load a chunk with same detail
                self.chunks_to_load_dic[chunk_coord] = detail
                self.chunks_to_load_set.add(chunk_coord)

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
    
    def update_shader(self):
        self.chunk_shader['m_view'].write(self.app.camera.view_matrix)
        self.chunk_shader['camPos'].write(self.app.camera.position)
        self.chunk_shader['time'].write(struct.pack('f', self.app.time))

    def update(self):
        self.generate_chunks()
        self.update_chunks()
        self.update_shader()

    def render(self):
        """Render all chunks within the active radius."""
        self.update()
        player_position = self.app.camera.position / (CHUNK_SIZE * CHUNK_SCALE)

        for (i, j) in self.chunk_meshes.keys():
            chunk_mesh = self.chunk_meshes[(i, j)]
            if chunk_mesh.detail is None:
                continue
            distance_sq = (player_position.x - i - 0.5) ** 2 + (player_position.z - j - 0.5) ** 2
            chunk_mesh.update_model_matrix(glm.sqrt(distance_sq))
            chunk_mesh.render()

    def destroy(self):
        """Clean up resources."""
        self.semaphore.acquire()
        for t in self.threads:
            t.join()

        [obj.destroy() for obj in self.chunk_meshes.values()]
        self.chunk_shader.release()

