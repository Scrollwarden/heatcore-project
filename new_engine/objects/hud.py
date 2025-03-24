import pygame as pg
import math
import moderngl as mgl

from new_engine.hud_elements import UI1, UI2, UI2_1, MenuIntroUI, CreditsUI, UI3
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
        self.hud_intro = MenuIntroUI(app, self.ui_surface)
        self.hud_credits = CreditsUI(self.ui_surface)

    def handle_event(self, event):
        # Existing UI2_1, UI2_2 and UI2 event handling...
        if self.hud_buttons.active:
            self.hud_buttons.handle_event(event)
            return
        if self.hud_intro.active:
            self.hud_intro.handle_event(event)
        if self.hud_credits.active:
            self.hud_credits.handle_event(event)
        if self.hud_menu.active:
            self.hud_menu.handle_event(event)
            return

        if event.type == pg.KEYDOWN and event.key == self.app.controls["Activer le menu"]:
            if not self.hud_menu.active:
                if self.hud_intro.active:
                    self.hud_intro.active = False
                    self.hud_game.active = True
                else:
                    self.hud_menu.first_time = False
                    self.hud_menu.active = True
                    pg.mouse.set_visible(True)

    def update(self):
        """met à jour les interfaces pour savoir qui est affiché"""
        if self.app.planet is None and self.hud_game.active:
            self.hud_game.active = False
        if not (self.app.planet is None or self.hud_game.active):
            self.hud_game.active = True

        if self.hud_menu.controls_requested: # menu to options
            self.hud_buttons.first_time = self.hud_menu.first_time
            self.hud_menu.controls_requested = False
            self.hud_buttons.active = True
            pg.mouse.set_visible(True)
        if self.hud_menu.intro_requested: # menu to intro
            self.hud_menu.intro_requested = False
            self.hud_menu.active = False
            self.hud_intro.active = True
        if self.hud_menu.credits_requested: # menu to credits
            self.hud_menu.credits_requested = False
            self.hud_menu.active = False
            self.hud_credits.active = True
        if self.hud_buttons.return_to_ui2: # options to menu
            self.hud_menu.first_time = self.hud_buttons.first_time
            self.hud_buttons.return_to_ui2 = False
            self.hud_menu.controls_requested = False # juste au cas où
            self.hud_buttons.active = False
            self.hud_menu.active = True
        if self.hud_intro.animation_ended: # intro to game
            self.hud_intro.animation_ended = False
            self.hud_intro.active = False
        if self.hud_credits.animation_ended: # credits to menu
            self.hud_credits.animation_ended = False
            self.hud_credits.active = False
            self.hud_menu.first_time = True
            self.hud_menu.active = True
            pg.mouse.set_visible(True)

        # Only hide the mouse if no UI is active.
        if not self.hud_menu.active and not self.hud_buttons.active:
            pg.mouse.set_visible(False)

        # No need to update the mesh it is done in the render

    def render(self):
        self.ui_surface.fill((0, 0, 0, 0))
        
        if self.hud_intro.active:
            self.hud_intro.draw()
        elif self.hud_credits.active:
            self.hud_credits.draw()
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