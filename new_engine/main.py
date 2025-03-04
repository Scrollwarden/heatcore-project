from ast import Index

import pygame as pg
import moderngl as mgl
import sys, time
from camera import Camera
from light import Light
from scene import Scene
import numpy as np
import matplotlib.pyplot as plt

class Logs:
    def __init__(self, frame_count_limit: int = 10000):
        self.index = 0
        self.frame_count_limit = frame_count_limit
        self.times = np.zeros((frame_count_limit, ), dtype=np.float32)
        self.accumulated_time = np.zeros((frame_count_limit, ), dtype=np.float32)
        self.fps = np.zeros((frame_count_limit, ), dtype=np.float32)
        self.chunks_loaded = np.zeros((frame_count_limit, ), dtype=np.uint32)
        self.chunks_loading = np.zeros((frame_count_limit, ), dtype=np.uint32)

    def add_to_log(self, delta_time, chunks_loaded, chunks_loading):
        if self.index >= self.frame_count_limit:
            print("===========================================================")
            print("!!! Not enough place in logs to add in new informations !!!")
            print("===========================================================")
            return
        self.times[self.index] = delta_time
        self.fps[self.index] = 1 / delta_time
        self.chunks_loaded[self.index] = chunks_loaded
        self.chunks_loading[self.index] = chunks_loading

        if self.index == 0:
            self.accumulated_time[self.index] = delta_time
        else:
            self.accumulated_time[self.index] = (
                self.accumulated_time[self.index - 1] + delta_time
            )

        self.index += 1

    def display_windows(self):
        x = self.accumulated_time[:self.index]

        metrics = [
            ("FPS", self.fps[:self.index], "Frames Per Second", "green"),
            ("Chunks Loaded", self.chunks_loaded[:self.index], "Chunks Loaded", "orange"),
            ("Chunks Loading", self.chunks_loading[:self.index], "Chunks Loading", "red"),
        ]

        for i, (title, data, ylabel, color) in enumerate(metrics):
            plt.figure(i + 1, figsize=(8, 5))
            plt.plot(x, data, label=title, color=color)
            plt.title(title)
            plt.xlabel("Time (s)")
            plt.ylabel(ylabel)
            plt.legend()
            plt.grid()
            plt.tight_layout()

        plt.show()



class GraphicsEngine:
    def __init__(self, window_size: tuple[int, int] = (1600, 900)):
        self.time = 0
        self.delta_time = 0
        self.window_size = window_size

        pg.init()
        self.clock = pg.time.Clock()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.set_mode(self.window_size, flags=pg.OPENGL | pg.DOUBLEBUF)

        #pg.event.set_grab(True)
        pg.mouse.set_visible(False)

        self.context = mgl.create_context()
        self.context.enable(flags=mgl.DEPTH_TEST | mgl.CULL_FACE)
        self.light = Light()
        self.camera = Camera(self)
        self.scene = Scene(self)
        self.logs = Logs()
        print("Graphics engine initialized successfully")

    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.scene.destroy()
                pg.quit()
                self.logs.display_windows()
                sys.exit()

    def render(self):
        self.context.clear(color=(0.08, 0.16, 0.18))
        self.scene.render()
        pg.display.flip()

    def get_time(self):
        self.time = pg.time.get_ticks() * 0.001

    def run(self):
        while True:
            start_time = time.time()
            self.get_time()
            self.check_events()
            self.camera.update()
            for shader_program in self.scene.shader_programs.values():
                shader_program.update()
            print(f"Chunks loaded: {self.scene.chunks.values()}")
            print(f"Chunks loading: {self.scene.chunks_loading}")
            print(f"Chunks to load: {self.scene.chunks_to_load}")
            self.render()
            self.delta_time = self.clock.tick(60)
            elapsed_time = time.time() - start_time
            print(f"FPS: {format_fps(elapsed_time, 60)}, Frame Time: {elapsed_time:.3f}s")
            num_loaded = len(self.scene.chunks)
            num_loading = len(self.scene.chunks_loading)
            self.logs.add_to_log(elapsed_time, num_loaded, num_loading)
            print()

def format_fps(delta_time, fps):
    current_fps = 1 / delta_time
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

if __name__ == '__main__':
    app = GraphicsEngine()
    app.run()
