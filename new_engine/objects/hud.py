import pygame as pg
import math
import moderngl as mgl

from new_engine.hud_elements import UI1, UI2, UI2_1, MenuIntroUI, UI3
from new_engine.options import SCREEN_WIDTH, SCREEN_HEIGHT
from new_engine.meshes.hud_mesh import HUDMesh

class HUDObject:
    def __init__(self, app):
        self.app = app
        self.context = app.context
        self.ui_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
        self.mesh = HUDMesh(app)
        self.hud_game = UI1(app, self.ui_surface)
        self.hud_menu = UI2(app, self.ui_surface)
        self.hud_buttons = UI2_1(self.ui_surface)
        self.hud_intro = MenuIntroUI(self.ui_surface)
        self.hud_cube = None

    def handle_event(self, event):
        # If UI3 is active, handle its events exclusively.
        if self.hud_cube is not None:
            self.hud_cube.handle_event(event)
            return

        # Existing UI2_1 and UI2 event handling...
        if self.hud_buttons.active:
            self.hud_buttons.handle_event(event)
            return
        if self.hud_menu.active:
            self.hud_menu.handle_event(event)
            return

        # Press L to launch UI3.
        # if event.type == pg.KEYDOWN and event.key == pg.K_l:
        #     self.hud_cube = UI3(self.ui_surface)
        #     pg.mouse.set_visible(True)
        # Other key handling...
        if event.type == pg.KEYDOWN and event.key == pg.K_h:
            self.hud_game.active = not self.hud_game.active
        elif event.type == pg.KEYDOWN and event.key == self.app.controls["Toggle Menu"]:
            self.hud_menu.first_time = False
            self.hud_menu.active = True
            pg.mouse.set_visible(True)

    def update(self):
        if self.app.planet is not None and self.hud_game is None:
            self.hud_game = UI1(self.ui_surface)
        if self.app.planet is None and self.hud_game is not None:
            self.hud_game = None

        if self.hud_menu.controls_requested:
            self.hud_buttons.first_time = self.hud_menu.first_time
            self.hud_menu.controls_requested = False
            self.hud_buttons.active = True
            pg.mouse.set_visible(True)

        # Only hide the mouse if no UI is active.
        if not self.hud_menu.active and not self.hud_buttons.active and self.hud_cube is None:
            pg.mouse.set_visible(False)

        # No need to update the mesh it is done in the render

    def render(self):
        self.ui_surface.fill((0, 0, 0, 0))

        # Check for UI3 first.
        if self.hud_cube is not None:
            self.hud_cube.draw()
            # When UI3 signals it is done (via its exit_ui3 flag), remove it.
            if self.hud_cube.exit_ui3:
                self.hud_cube = None
                pg.mouse.set_visible(False)
        elif self.hud_buttons.active:
            self.hud_buttons.draw()
        elif self.hud_menu.active:
            self.hud_menu.draw()
        elif self.hud_game.active:
            self.hud_game.draw(self.app.planet.camera)

        ui_texture_data = pg.image.tostring(self.ui_surface, "RGBA", True)
        self.mesh.ui_texture.write(ui_texture_data)

        self.context.disable(mgl.DEPTH_TEST)
        self.context.enable(mgl.BLEND)
        self.context.blend_func = (mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA)

        self.mesh.render()

        self.context.disable(mgl.BLEND)
        self.context.enable(mgl.DEPTH_TEST)

    def destroy(self):
        self.mesh.destroy()