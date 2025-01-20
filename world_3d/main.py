import pygame as pg
import moderngl as mgl
import sys, time
from camera import Camera
from light import Light
from scene import Scene

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
        print("everything is setup up correctly")

    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.scene.destroy()
                pg.quit()
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
            self.render()
            self.delta_time = self.clock.tick(60)
            elapsed_time = time.time() - start_time

            print(f"FPS: {format_fps(elapsed_time, 60)}, Frame Time: {elapsed_time:.3f}ms")

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

if __name__ == '__main__':
    app = GraphicsEngine()
    app.run()
