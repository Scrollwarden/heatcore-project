import pygame as pg
import moderngl as mgl
import sys, time
from new_engine.meshes.obj_base_mesh import DefaultObjMesh, GameObjMesh
from new_engine.scene import Scene
from new_engine.camera import CameraAlt, CameraFollow
from new_engine.light import Light
from new_engine.planet import Planet
from new_engine.logs import Logs
from new_engine.player import Player, PlayerFollow, PlayerNoChangeInHeight, SatisfyingPlayer, FollowTerrainPlayer

from new_engine.options import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BACKGROUND_COLOR, CHUNK_SIZE, CHUNK_SCALE


class GraphicsEngine:
    def __init__(self):
        self.mouse_clicks = [0, 0]
        self.time = 0
        self.delta_time = 0

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
        
        self.light = Light()
        self.camera = CameraFollow(self)
        
        self.player = FollowTerrainPlayer(self)
        
        self.meshes = {}
        self.load_meshes()
        self.chunk_manager = Planet(self)
        # self.scene = Scene(self)
        
        self.logs = Logs()
        print("Graphics engine initialized successfully")
    
    def load_meshes(self):
        self.meshes["heatcore"] = GameObjMesh(self, "heat_core", "obj",
                                              scale=0.01)
        self.meshes["starting_base"] = GameObjMesh(self, "starting_base", "obj",
                                                   scale=0.005)

    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key in (pg.K_p, pg.K_ESCAPE)):
                self.chunk_manager.destroy()
                pg.quit()
                self.logs.save("new_engine/log_data")
                #self.logs.display_single_window()
                sys.exit()
            if event.type == pg.MOUSEWHEEL:
                self.player.camera_zoom *= 0.97 ** event.y

    def render(self):
        self.context.clear(color=BACKGROUND_COLOR)
        self.chunk_manager.render()
        # self.scene.render()
        self.player.mesh.render()
        pg.display.flip()

    def get_time(self):
        self.time = pg.time.get_ticks() * 0.001

    def run(self):
        debug = False
        while True:
            start_time = time.perf_counter()  # High-resolution timer

            self.get_time()
            self.check_events()
            for mesh in self.meshes.values():
                mesh.update()
            
            self.player.update()
            self.camera.update()

            self.render()
            self.delta_time = self.clock.tick(FPS)

            elapsed_time = time.perf_counter() - start_time
            num_loaded = len(self.chunk_manager.chunk_meshes)
            num_loading = len(self.chunk_manager.chunks_loading)
            self.logs.add_to_log(elapsed_time, num_loaded, num_loading)
            
            print(f"FPS: {format_fps(elapsed_time)}, Frame Time: {elapsed_time:.3f}s")
            if debug:
                print(f"Real player position: {self.player.position}")
                print(f"Camera real position: {self.camera.position}")
                print(f"Camera forward: {self.camera.forward}")
                print(f"Relative position of player: {self.player.position / (CHUNK_SIZE * CHUNK_SCALE)}")
                print(f"Camera relative position   : {self.camera.position / (CHUNK_SIZE * CHUNK_SCALE)}")
            print()

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

if __name__ == '__main__':
    app = GraphicsEngine()
    app.run()
