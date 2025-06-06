import pygame as pg
import math
import moderngl as mgl
import glm
import time

from engine.hud_elements import UI1, UI2, UI2_1, UI3, DEFAULT_CONTROLS
from engine.options import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from engine.meshes.hud_mesh import HUDMesh
from engine.objects.popup import PopUp



class Donjon:
    def __init__(self, app, level):
        self.app = app
        self.clock = app.clock
        self.context = app.context
        
        self.ui_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
        self.mesh = HUDMesh(app)
        self.popup = PopUp(self.app, "Le Cube", SCREEN_WIDTH // 3, 50, 100,
                           0.5, 1, 0.5, True)
        
        self.controls = app.controls
        self.ai_level = min(5, level // 2)
        self.hud_game = UI3(self.ui_surface, self.ai_level)
        self.hud_menu = UI2(app, self.ui_surface)
        self.hud_buttons = UI2_1(self.ui_surface)

        self.time_taken = 0
        self.delta_time = 0
        self.running = True
        pg.mouse.set_visible(True)

    def new_popup(self, text, wait_time, size=SCREEN_WIDTH // 2, font_size=40, y=100,
                  fade_in=0.5, fade_out=0.5, center_text=True, border_radius=10, border_width=10):
        if self.popup is not None:
            self.popup.destroy()
        self.popup = PopUp(self.app, text, size, font_size, y,
                           fade_in, wait_time, fade_out, center_text, border_radius, border_width)

    def remove_popup(self):
        if self.popup is not None:
            self.popup.destroy()
        self.popup = None

    def check_events(self):
        for event in pg.event.get():
            # Existing UI2_1 and UI2 event handling...
            if self.hud_buttons.active:
                self.hud_buttons.handle_event(event)
                return
            if self.hud_menu.active:
                self.hud_menu.handle_event(event)
                return

            if event.type == pg.KEYDOWN and event.key == self.app.controls["Activer le menu"]:
                self.hud_menu.first_time = False
                self.hud_menu.active = True
            elif event.type == pg.KEYDOWN and event.key == pg.K_p:
                self.new_popup("Le Cube", 1.5, SCREEN_WIDTH // 3, 50)

        pg.mouse.set_visible(True)

    def update(self):
        if self.hud_game.exit_ui3:
            self.running = False
            return

        if self.hud_menu.controls_requested:
            self.hud_buttons.first_time = self.hud_menu.first_time
            self.hud_menu.controls_requested = False
            self.hud_buttons.active = True
        self.hud_game.update()
        if self.hud_game.popup_flag != "":
            self.new_popup(self.hud_game.popup_flag, 2)

        fini, value = self.hud_game.cube.terminal_state()
        if not self.hud_game.fini and fini:
            if value * self.hud_game.ai_player > 0:
                text = "Parti fini, vous avez perdu !"
            else:
                text = "Parti fini, vous avez gagné !"
                self.hud_game.won = True
            self.new_popup(text, 69420, SCREEN_WIDTH // 2, 50)
            self.hud_game.fini = True
        if self.hud_game.fini == False and self.popup is not None and self.popup.wait_time == 69420:
            self.remove_popup()

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
        if self.popup is not None:
            self.popup.render()

        self.context.disable(mgl.BLEND)
        self.context.enable(mgl.DEPTH_TEST)

    def run(self):
        while self.running:
            start_time = time.perf_counter()  # High-resolution timer

            self.check_events()
            self.update()
            if not self.running: break
            if not self.hud_buttons.active:
                self.controls = self.hud_buttons.bindings
                self.app.controls = self.controls
            self.render()
            pg.display.flip()
            self.delta_time = self.clock.tick(FPS)

            elapsed_time = time.perf_counter() - start_time
            if not (self.hud_menu.active or self.hud_buttons.active):
                self.time_taken += elapsed_time

    def cinematique(self):
        with open("txt/text_cube_ia.txt", 'r', encoding='utf-8') as f:
            content = f.read().strip()  # Read file and remove leading/trailing newlines
        paragraphs = [paragraph.splitlines() for paragraph in content.split("\n\n") if paragraph.strip()]
        self.remove_popup()
        for paragraph in paragraphs:
            for line in paragraph:
                break_paragraph = False
                popup = PopUp(self.app, line, 800, 40, 300, 0.5, 3.5, 0.5, True, 20, 20)
                while not popup.finished:
                    start_time = time.perf_counter()  # High-resolution timer
                    for event in pg.event.get():
                        if event.type == pg.KEYDOWN and event.key == self.app.controls["Activer le menu"]:
                            break_paragraph = True
                    if break_paragraph:
                        break
                    self.render()
                    popup.render()
                    pg.display.flip()
                    self.delta_time = self.clock.tick(FPS)

                    elapsed_time = time.perf_counter() - start_time
                if break_paragraph:
                    break


    def destroy(self):
        self.mesh.destroy()
        if self.popup is not None:
            self.popup.destroy()

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