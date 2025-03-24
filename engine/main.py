import pygame as pg
import moderngl as mgl
import glm
import sys, time
import random
import pickle
import os

from engine.meshes.obj_base_mesh import GameObjMesh
from engine.meshes.advanced_skybox import AdvancedSkyBoxMesh
from engine.objects.hud import HUDObject
from engine.objects.popup import PopUp
from engine.donjon import Donjon
from engine.planet import Planet
from engine.logs import Logs
from engine.hud_elements import DEFAULT_CONTROLS

from engine.options import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BACKGROUND_COLOR, CHUNK_SIZE, CHUNK_SCALE


class GraphicsEngine:
    """Class for the 3d graphic engine"""
    
    def __init__(self):
        """Class constructor"""
        self.mouse_clicks = [0, 0]
        self.controls = DEFAULT_CONTROLS.copy()
        self.time = 0
        self.delta_time = 0
        self.current_level = 0

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
        self.current_song = None

        print("Graphics engine initialized successfully")
    
    def load_meshes(self):
        """Load all meshes for 3d objects"""
        self.meshes["spaceship"] = GameObjMesh(self, "spaceship_player", "obj",
                                               scale=0.002,
                                               obj_transformation=glm.rotate(glm.radians(90), glm.vec3(0, 1, 0)))
        self.meshes["starting_base"] = GameObjMesh(self, "starting_base", "obj",
                                                   scale=0.005)
        self.meshes["ancient_structure"] = GameObjMesh(self, "door_dungeon", "obj", 
                                                       scale=0.04)
        self.meshes["heatcore"] = GameObjMesh(self, "heat_core", "obj",
                                              scale=0.02)
        self.meshes["advanced_skybox"] = AdvancedSkyBoxMesh(self)

    def load_textures(self):
        """Load textures for the rendering"""
        image = pg.image.load("engine/textures/img.png")
        image = pg.transform.flip(image, False, True)
        image_data = pg.image.tobytes(image, "RGB")
        self.textures["test"] = self.context.texture(image.get_size(), 3, image_data)
        
        # self.textures["depth_texture"] = self.context.depth_texture(SCREEN_WIDTH / SCREEN_HEIGHT)


    def load_new_planet(self, saved_data = None, heatcore_count = 0):
        """Load a whole new planet

        Args:
            seed (int | None, optional): World seed (positive integer). Defaults to None -> aléatoire.
        """
        if self.planet is not None:
            self.planet.destroy()
        if saved_data is None:
            saved_data = [self.current_level, heatcore_count]
        if pg.mixer.music.get_busy():
            pg.mixer.music.stop()

        self.planet = Planet(self, saved_data)
        self.planet.load_attributes()
        self.planet.cinematique_entree()

        self.hud.update()
        self.hud.hud_game.heatcore_markers = {}

        self.current_level = saved_data[0] + 1
    
    def save_data(self, file_path: str):
        """Save data to a file"""
        if self.planet is not None:
            objects = [self.current_level - int(self.planet is not None),
                       self.planet.seed,
                       self.planet.player.position,
                       self.planet.player.forward,
                       tuple(self.planet.heatcores.keys()),
                       self.planet.heatcore_count,
                       self.planet.ancient_structure.won]
        else:
            objects = [self.current_level, 0]
        with open(file_path, 'wb') as f:
            pickle.dump(objects, f)
        print(f"Data successfully saved in {file_path}")

    def save_buttons(self, file_path: str):
        with open(file_path, 'wb') as f:
            pickle.dump(self.controls, f)
        print(f"Button data saved successfully in {file_path}")
    
    def load_data(self, file_path: str) -> list:
        """Load data from a file"""
        try:
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return [0, 0]

    def load_buttons(self, file_path: str):
        try:
            with open(file_path, 'rb') as f:
                self.hud.hud_buttons.bindings = pickle.load(f)
        except FileNotFoundError:
            print(f"Button data not found, gave normal ones.")
    
    def remove_data(self, data_file_path: str, buttons_file_path: str):
        """Remove data from files"""
        for file_path in (data_file_path, buttons_file_path):
            try:
                os.remove(file_path)
            except FileNotFoundError:
                print(f"No file in {file_path}, cancelling the removal of saves")
    
    def quit_game(self):
        """Quit the game and it's garbage collection"""
        self.save_data("saves/data.pkl")
        self.save_buttons("saves/buttons.pkl")
        self.hud.destroy()
        if self.planet is not None:
            self.planet.destroy()
        pg.quit()
        sys.exit()

    def check_events(self):
        """Pygame events loop"""
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_p):
                self.quit_game()
            if event.type == pg.KEYDOWN and event.key == pg.K_r:
                if not (self.hud.hud_menu.active or self.hud.hud_buttons.active):
                    self.load_new_planet()
            if self.planet is not None:
                self.planet.handle_event(event)
            self.hud.handle_event(event)

    def render(self):
        """World rendering"""
        self.context.clear(color=BACKGROUND_COLOR)
        if self.planet is not None:
            self.planet.render()
        self.hud.render()

    def get_time(self):
        """Update the time"""
        self.time = pg.time.get_ticks() * 0.001

    def play_song(self, song=None, fade=3000, replace=True, restart=False):
        """Joue une musique en fonction des paramètres donnés

        Args:
            song (None | str): le nom de la musique à jouer. Defaults to None (pas de musique).
            replace (bool): Remplace ou pas si il y a déjà une musique différent qui joue. Defaults to True.
            restart (bool): Recommence ou pas si la musique est déjà joué. Defaults to False.
        """
        if song is None:
            pg.mixer.stop()
            self.current_song = None
            return

        if self.current_song == song:
            if restart or not pg.mixer.music.get_busy():
                pg.mixer.music.stop()
                pg.mixer.music.load(f"musics/{song}")
                pg.mixer.music.set_volume(0.4)
                pg.mixer.music.play(-1, fade_ms=fade)
            return

        if replace or not pg.mixer.music.get_busy():
            pg.mixer.music.stop()

        pg.mixer.music.load(f"musics/{song}")
        pg.mixer.music.set_volume(0.4)
        pg.mixer.music.play(-1, fade_ms=fade)
        self.current_song = song

    def playsound(self):
        """Actualise les sons"""
        # select sound
        if self.hud.hud_menu.active or self.hud.hud_buttons.active:
            self.play_song("an_empty_planet_v1.mp3", int(3e3))
        elif self.hud.hud_intro.active:
            self.play_song()
        else:
            self.play_song("The-Road-Ahead_LoudnessComp_mp3_compressed.mp3", int(1e4))

    def run(self):
        """Main while loop"""
        self.get_time()
        # Manual activation on first time app is launched
        self.hud.hud_menu.first_time = True
        self.hud.hud_menu.active = True
        pg.mouse.set_visible(True)
        
        # Load data on launch
        self.load_buttons("saves/buttons.pkl")
        
        while True:
            start_time = time.perf_counter()  # High-resolution timer

            self.get_time()
            self.hud.hud_intro.check_end_condition()
            self.hud.hud_credits.check_end_condition()
            self.check_events()
            self.hud.update()
            if self.planet is not None:
                for mesh in self.meshes.values():
                    mesh.update()

            self.playsound()

            if not self.hud.hud_buttons.active:
                self.controls = self.hud.hud_buttons.bindings
            self.render()
            pg.display.flip()
            self.delta_time = self.clock.tick(FPS)

            elapsed_time = time.perf_counter() - start_time
            
            # print(f"FPS: {format_fps(elapsed_time)}, Frame Time: {elapsed_time:.3f}s")
            # print()

            if self.planet is not None and self.planet.exit:
                if self.planet.heatcore_count >= 9:
                    pg.mouse.set_visible(False)
                    self.hud.hud_menu.active = False
                    self.hud.hud_menu.credits_requested = True
                else:
                    self.load_new_planet(heatcore_count=max(0, self.planet.heatcore_count))

def format_fps(delta_time):
    """Format a string for the FPS at a certain frame

    Args:x
        delta_time (float): difference of time between two frames

    Returns:
        str: string of the fps with a given color for how close it is to the goal amount
    """
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
