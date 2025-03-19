import pygame as pg
import moderngl as mgl
import sys, time
from camera import Camera, Light
from shader_program import ShaderProgram
from obj_base_mesh import DefaultObjMesh

SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900
BACKGROUND_COLOR = (0.05, 0.05, 0.1)
FPS = 60

class GraphicsEngine:
    def __init__(self):
        self.time = 0
        self.delta_time = 0
        self.window_size = (SCREEN_WIDTH, SCREEN_HEIGHT)

        pg.init()
        self.clock = pg.time.Clock()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags=pg.OPENGL | pg.DOUBLEBUF)

        pg.event.set_grab(True)
        pg.mouse.set_visible(False)

        self.context = mgl.create_context()
        self.context.enable(flags=mgl.DEPTH_TEST | mgl.CULL_FACE)
        self.camera = Camera(self)
        self.light = Light()
        self.scene = Scene(self)
        print("Graphics engine initialized successfully")

    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key in (pg.K_p, pg.K_ESCAPE)):
                self.scene.destroy()
                pg.quit()
                self.logs.save("new_engine/log_data")
                #self.logs.display_single_window()
                sys.exit()
            if event.type == pg.MOUSEWHEEL:
                self.player.camera_zoom *= 0.97 ** event.y

    def render(self):
        self.context.clear(color=BACKGROUND_COLOR)
        self.scene.render()
        pg.display.flip()

    def get_time(self):
        self.time = pg.time.get_ticks() * 0.001

    def run(self):
        while True:
            start_time = time.perf_counter()  # High-resolution timer

            self.get_time()
            self.check_events()
            self.camera.update()

            self.render()
            self.delta_time = self.clock.tick(FPS)

            elapsed_time = time.perf_counter() - start_time
            
            print(f"FPS: {format_fps(elapsed_time)}, Frame Time: {elapsed_time:.3f}s")

def format_fps(delta_time):
    current_fps = 1 / delta_time
    diff_percentage = (current_fps - FPS) / FPS
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


class Scene:
    def __init__(self, app):
        self.app = app
        self.objects = []
        self.load()
    
    def load(self):
        self.objects.append(DefaultObjMesh(self.app, 'spaceship_player'))
    
    def update(self):
        for obj in self.objects:
            obj.render()
    
    def render(self):
        """Render all chunks within the active radius."""
        self.update()
        for obj in self.objects:
            obj.render()
    
    def destroy(self):
        [obj.destroy() for obj in self.objects]

if __name__ == '__main__':
    app = GraphicsEngine()
    app.run()


