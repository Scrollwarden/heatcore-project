import threading
import time
import queue
from world_3d.chunk import PointsHeightParams, ColorParams, generate_chunk
import pygame as pg





class Game:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

        self.seed = 1
        self.radius = 5

        self.color_params = ColorParams()
        points = ((0.0, -0.2), (0.4, 0.0), (0.45, 0.1), (0.5, 0.2), (0.6, 0.26), (1.0, 1.0))
        self.height_params = PointsHeightParams(points, 10)

        self.result_queue = queue.Queue()
        self.threads = []
        self.threads_limit = 8
        self.semaphore = threading.Semaphore(self.threads_limit)  # Limit to 8 threads

        self.chunks = {}
        self.chunks_to_load = []
        self.tasks_per_frame = 5  # Process 5 tasks per frame to balance workload

    def update_worker(self, coord):
        """Worker function for generating chunks."""
        try:
            chunk = generate_chunk(
                coord[0], coord[1], self.height_params, self.color_params,
                seed=self.seed, scale=35.0, octaves=5, progress_bar=False
            )
            chunk.update_detail(0, progress_bar=False)
            time.sleep(0.08)  # Simulate processing delay
            self.result_queue.put((coord, chunk))
        except Exception as e:
            print(f"Error in worker for chunk {coord}: {e}")

    def update_chunks(self):
        """Distribute chunk generation tasks across multiple frames."""
        tasks_this_frame = 0
        while self.chunks_to_load and tasks_this_frame < self.tasks_per_frame:
            coord = self.chunks_to_load.pop(0)
            if len(self.threads) < self.threads_limit:
                t = threading.Thread(
                    target=self.update_worker,
                    args=(coord, )
                )
                t.start()
                self.threads.append(t)
                tasks_this_frame += 1

        # Clean up finished threads
        self.threads = [t for t in self.threads if t.is_alive()]

        # Collect results
        while not self.result_queue.empty():
            coord, chunk = self.result_queue.get()
            self.chunks[coord] = chunk

    def update(self):
        """Update chunks and load new ones."""
        # Remove far chunks
        keys_to_remove = [(i, j) for (i, j) in self.chunks.keys()
                          if (self.x - i) ** 2 + (self.y - j) ** 2 > (2 * self.radius) ** 2]
        for key in keys_to_remove:
            del self.chunks[key]

        # Add new chunks to the queue
        for i in range(-self.radius, self.radius + 1):
            for j in range(-self.radius, self.radius + 1):
                int_pos = (int(self.x) + i, int(self.y) + j)
                if int_pos in self.chunks or int_pos in self.chunks_to_load:
                    continue
                if i ** 2 + j ** 2 > self.radius ** 2:
                    continue
                self.chunks_to_load.append(int_pos)

        # Handle chunk generation
        self.update_chunks()

def format_fps(delta_time, fps):
    current_fps = 1000 / delta_time
    diff_percentage = (current_fps - fps) / fps
    if diff_percentage >= -0.1:
        color_code = "\033[32m"  # Green
    elif diff_percentage >= -0.2:
        color_code = "\033[94m"  # Light Blue
    elif diff_percentage >= -0.4:
        color_code = "\033[34m"  # Blue
    elif diff_percentage >= -0.6:
        color_code = "\033[33m"  # Orange (Yellow in ANSI)
    else:
        color_code = "\033[31m"  # Red

    reset_code = "\033[0m"
    formatted_fps = f"{current_fps:.3f}"
    return f"{color_code}{formatted_fps}{reset_code}"

def main():
    pg.init()
    pg.display.set_mode((500, 500))
    clock = pg.time.Clock()
    game = Game()

    print("Running")
    while True:
        start_time = pg.time.get_ticks()

        game.update()

        pg.display.get_surface().fill((0, 0, 0))
        pg.display.flip()

        delta_time = clock.tick(60)
        elapsed_time = pg.time.get_ticks() - start_time
        print(f"FPS: {format_fps(elapsed_time, 60)}, Frame Time: {elapsed_time}ms")
        print(game.chunks.keys())


if __name__ == "__main__":
    main()
