from chunk import generate_chunk, HeightParams, ColorParams, PointsHeightParams, CHUNK_SIZE
from model import ChunkModel, Cube
from tqdm import tqdm
import queue
import threading
import moderngl as mgl
import time

class Scene:
    def __init__(self, app):
        self.seed = 1
        self.radius = 3
        self.scale = 35.0
        self.app = app

        points = ((0.0, -0.2), (0.4, 0.0), (0.45, 0.1), (0.5, 0.2), (0.6, 0.26), (1.0, 1.0))
        self.height_params = PointsHeightParams(points, self.scale / 4)
        self.color_params = ColorParams()

        self.result_queue = queue.Queue()
        self.threads = []
        self.threads_limit = 2
        self.semaphore = threading.Semaphore(self.threads_limit)

        self.chunks = {}
        self.objects = {}
        self.chunks_to_load = []
        self.tasks_per_frame = 5

    def update_worker(self, coord):
        """Worker function for generating chunks and rendering."""
        #try:
        s = time.time()
        chunk = generate_chunk(
            coord[0], coord[1], self.height_params, self.color_params,
            seed=self.seed, scale=self.scale, octaves=5, progress_bar=False
        )
        m = time.time()
        chunk.update_detail(0, progress_bar=False)
        m2 = time.time()
        chunk_model = ChunkModel(self.app, chunk)
        e = time.time()
        self.result_queue.put((coord, chunk, chunk_model))
        #except Exception as e:
        #    print(f"Error in worker for chunk {coord}: {e}")

        #print(f"Time taken generating: {m - s:.3f}s")
        #print(f"Time taken detailing: {m2 - m:.3f}s")
        #print(f"Time taken rendering + modeling: {e - m2:.3f}s")

    def update_chunks(self):
        """Distribute chunk generation tasks across multiple frames."""
        tasks_this_frame = 0
        while self.chunks_to_load and tasks_this_frame < self.tasks_per_frame:
            coord = self.chunks_to_load.pop(0)
            if len(self.threads) < self.threads_limit:
                t = threading.Thread(
                    target=self.update_worker,
                    args=(coord,)
                )
                t.start()
                self.threads.append(t)
                tasks_this_frame += 1

        # Clean up finished threads
        self.threads = [t for t in self.threads if t.is_alive()]

        # Collect results
        while not self.result_queue.empty():
            coord, chunk, chunk_model = self.result_queue.get()
            self.chunks[coord] = chunk
            chunk_model.init_context()
            self.objects[coord] = chunk_model

    def update(self):
        """Update chunks and load new ones."""
        # Remove far chunks
        player_position = self.app.camera.position / CHUNK_SIZE
        keys_to_remove = [(i, j) for (i, j) in self.chunks.keys()
                          if (player_position.x - i - 0.5) ** 2 +
                             (player_position.z - j - 0.5) ** 2 > (2 * self.radius) ** 2]
        for key in keys_to_remove:
            del self.chunks[key]
            del self.objects[key]

        # Add new chunks to the queue
        for i in range(-self.radius, self.radius + 1):
            for j in range(-self.radius, self.radius + 1):
                int_pos = (int(self.app.camera.position.x) + i, int(self.app.camera.position.z) + j)
                if int_pos in self.chunks or int_pos in self.chunks_to_load:
                    continue
                if (player_position.x - i - 0.5) ** 2 + (player_position.z - j - 0.5) ** 2 > (2 * self.radius) ** 2:
                    continue
                self.chunks_to_load.append(int_pos)

        # Handle chunk generation
        self.update_chunks()

    def render(self):
        """Render all objects."""
        self.update()
        for obj in self.objects.values():
            print(obj, end=' ')
            obj.render()
        print()

    def destroy(self):
        """Clean up resources."""
        [obj.destroy() for obj in self.objects.values()]

