import pygame as pg
import math
import moderngl as mgl
import glm
import time

from new_engine.hud_elements import UI1, UI2, UI2_1, UI3, DEFAULT_CONTROLS
from new_engine.options import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from new_engine.meshes.hud_mesh import HUDMesh



class Donjon:
    def __init__(self, app, level):
        self.app = app
        self.clock = app.clock
        self.context = app.context
        
        self.ui_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
        self.mesh = HUDMesh(app)
        
        self.controls = app.controls
        self.ai_level = min(3, level // 2)
        self.hud_game = UI3(self.ui_surface)
        self.hud_menu = UI2(app, self.ui_surface)
        self.hud_buttons = UI2_1(self.ui_surface)
        
        self.starting_time = time.time()
        self.runing = True
        pg.mouse.set_visible(True)

    def check_events(self):
        for event in pg.event.get():
            # If UI3 is active, handle its events exclusively.
            self.hud_game.handle_event(event)

            # Existing UI2_1 and UI2 event handling...
            if self.hud_buttons.active:
                self.hud_buttons.handle_event(event)
                return
            if self.hud_menu.active:
                self.hud_menu.handle_event(event)
                return

            elif event.type == pg.KEYDOWN and event.key == self.app.controls["Toggle Menu"]:
                self.hud_menu.first_time = False
                self.hud_menu.active = True

    def update(self):
        if self.hud_game.exit_ui3:
            self.runing = False
            return

        if self.hud_menu.controls_requested:
            self.hud_buttons.first_time = self.hud_menu.first_time
            self.hud_menu.controls_requested = False
            self.hud_buttons.active = True
        self.hud_game.update()


    def render(self):
        self.ui_surface.fill((0, 0, 0, 0))

        self.hud_game.draw()
        if self.hud_buttons.active:
            self.hud_buttons.draw()
        elif self.hud_menu.active:
            self.hud_menu.draw()
        elif self.hud_game.active:
            self.hud_game.draw()

        ui_texture_data = pg.image.tostring(self.ui_surface, "RGBA", True)
        self.mesh.ui_texture.write(ui_texture_data)

        self.context.disable(mgl.DEPTH_TEST)
        self.context.enable(mgl.BLEND)
        self.context.blend_func = (mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA)

        self.mesh.render()

        self.context.disable(mgl.BLEND)
        self.context.enable(mgl.DEPTH_TEST)

    def run(self):
        while self.runing:
            start_time = time.perf_counter()  # High-resolution timer

            self.check_events()
            self.update()
            if not self.runing: break
            if not self.hud_buttons.active:
                self.controls = self.hud_buttons.bindings
                self.app.controls = self.controls
            self.render()
            pg.display.flip()
            self.delta_time = self.clock.tick(FPS)

            elapsed_time = time.perf_counter() - start_time
            print(f"FPS: {format_fps(elapsed_time)}, Frame Time: {elapsed_time:.3f}s")
            print()

    def destroy(self):
        self.mesh.destroy()

def format_fps(delta_time: float) -> str:
    """Format a string for the FPS at a certain frame

    Args:
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