import pygame as pg
import moderngl as mgl
import glm
import sys, time
import random
from new_engine.meshes.obj_base_mesh import GameObjMesh
from new_engine.meshes.advanced_skybox import AdvancedSkyBoxMesh
from new_engine.objects.hud import HUDObject
from new_engine.objects.popup import PopUp
from new_engine.planet import Planet
from new_engine.logs import Logs
from new_engine.hud_elements import DEFAULT_CONTROLS

from new_engine.options import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BACKGROUND_COLOR, CHUNK_SIZE, CHUNK_SCALE


class GraphicsEngine:
    def __init__(self):
        self.mouse_clicks = [0, 0]
        self.controls = DEFAULT_CONTROLS.copy()
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
        
        self.meshes = {}
        self.load_meshes()
        self.textures = {}
        self.load_textures()
        self.planet = None
        self.hud = HUDObject(self)
        self.popup = None
        
        self.logs = Logs()
        print("Graphics engine initialized successfully")
    
    def load_meshes(self):
        self.meshes["spaceship"] = GameObjMesh(self, "spaceship_player", "obj",
                                               scale=0.002,
                                               obj_transformation=glm.rotate(glm.radians(90), glm.vec3(0, 1, 0)))
        self.meshes["starting_base"] = GameObjMesh(self, "starting_base", "obj",
                                                   scale=0.005)
        self.meshes["ancient_structure"] = GameObjMesh(self, "door_dungeon", "obj", 
                                                       scale=0.015)
        self.meshes["heatcore"] = GameObjMesh(self, "heat_core", "obj",
                                              scale=0.01)
        self.meshes["advanced_skybox"] = AdvancedSkyBoxMesh(self)

    def load_textures(self):
        image = pg.image.load("new_engine/textures/img.png")
        image = pg.transform.flip(image, False, True)
        image_data = pg.image.tobytes(image, "RGB")
        self.textures["test"] = self.context.texture(image.get_size(), 3, image_data)
        
        # self.textures["depth_texture"] = self.context.depth_texture(SCREEN_WIDTH / SCREEN_HEIGHT)


    def load_new_planet(self, seed = None):
        if self.planet is not None:
            self.planet.destroy()
        if seed is None:
            seed = random.randrange(1500)
            print(f"Current seed: {seed}")
        self.planet = Planet(self, seed, "plateau")
        self.planet.load_attributes()
        
        self.hud.hud_game.heatcore_markers = {}
        self.hud.hud_game.heatcore_bar.sections = self.planet.num_heatcores
        # self.planet.cinematique_entree()
        
        if pg.mixer.music.get_busy():
            pg.mixer.music.stop()
        # pg.mixer.music.load("musics/The Road Ahead_LoudnessComp.wav")
        # pg.mixer.music.set_volume(0.5)
        # pg.mixer.music.play(-1)
    
    def quit_game(self):
        self.planet.destroy()
        self.hud.destroy()
        pg.quit()
        self.logs.save("new_engine/log_data")
        self.logs.display_single_window()
        sys.exit()

    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_p):
                self.quit_game()
            if event.type == pg.KEYDOWN and event.key == self.controls["Reset Planet"]:
                if not (self.hud.hud_menu.active or self.hud.hud_buttons.active):
                    self.load_new_planet()
            if event.type == pg.KEYDOWN and event.key == pg.K_l:
                self.planet.light.time = 0
            if event.type == pg.KEYDOWN and event.key == pg.K_m:
                self.popup = PopUp(self, "Vous avez récoltez tous les coeurs d'énergies. Retournez à la base pour décoller vers la prochaine planète.",
                                   500, 20, 200, 0.5, 5, 0.5, True, 20, 50)
            if event.type == pg.MOUSEWHEEL:
                self.planet.player.camera_zoom *= 0.97 ** event.y
            self.hud.handle_event(event)

    def render(self):
        self.context.clear(color=BACKGROUND_COLOR)
        self.planet.render()
        self.hud.render()
        if self.popup is not None:
            self.popup.render()

    def get_time(self):
        self.time = pg.time.get_ticks() * 0.001

    def run(self):
        self.get_time()
        # manual activation on first time app is launched
        self.hud.hud_menu.first_time = True
        self.hud.hud_menu.active = True
        pg.mouse.set_visible(True)
        self.load_new_planet()
        while True:
            start_time = time.perf_counter()  # High-resolution timer

            self.get_time()
            self.check_events()
            self.hud.update()
            for mesh in self.meshes.values():
                mesh.update()

            if not self.hud.hud_buttons.active:
                self.controls = self.hud.hud_buttons.bindings
            self.render()
            pg.display.flip()
            self.delta_time = self.clock.tick(FPS)

            elapsed_time = time.perf_counter() - start_time
            num_loaded = len(self.planet.chunk_meshes)
            num_loading = len(self.planet.chunks_loading)
            self.logs.add_to_log(elapsed_time, num_loaded, num_loading)
            
            print(f"FPS: {format_fps(elapsed_time)}, Frame Time: {elapsed_time:.3f}s")
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
