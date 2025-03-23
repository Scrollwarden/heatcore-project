import pygame as pg
import moderngl as mgl
import time

from new_engine.meshes.hud_mesh import HUDMesh
from new_engine.options import SCREEN_WIDTH, SCREEN_HEIGHT

class PopUp:
    def __init__(self, app, text, size, font_size, y, fade_in, wait_time, fade_out, center_text=False, border_radius=10, border_width=10):
        self.app = app
        self.context = app.context
        self.text = text
        self.size = size  # Maximum width of the message box
        self.font_size = font_size
        self.y = y
        self.fade_in = fade_in
        self.wait_time = wait_time
        self.fade_out = fade_out
        self.center_text = center_text
        self.border_radius = border_radius
        self.border_width = border_width
        self.start_time = time.time()
        self.finished = False

        self.font = pg.font.Font(None, font_size)
        self.mesh = HUDMesh(app)
        
        # Wrap text & render once
        self.lines = self.wrap_text()
        self.text_surfaces = [self.font.render(line, True, (255, 255, 255)) for line in self.lines]
        
        self.text_width = max(surf.get_width() for surf in self.text_surfaces)
        self.text_height = sum(surf.get_height() for surf in self.text_surfaces)

        # Pre-render UI surface
        self.ui_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
        self.render_static_ui()

        # Send texture once (alpha will be handled in shader)
        ui_texture_data = pg.image.tostring(self.ui_surface, "RGBA", True)
        self.mesh.ui_texture.write(ui_texture_data)

    def wrap_text(self):
        words = self.text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_width, _ = self.font.size(test_line)
            if test_width > self.size:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test_line

        if current_line:
            lines.append(current_line)

        return lines

    def render_static_ui(self):
        """Pre-render the text and background once to improve performance"""
        text_x = (SCREEN_WIDTH - self.text_width) // 2 if self.center_text else self.border_width
        text_y = self.y - self.text_height // 2

        # Background rectangle
        background_rect = pg.Rect(text_x - self.border_width, text_y - self.border_width, 
                                  self.text_width + self.border_width * 2, self.text_height + self.border_width * 2)
        pg.draw.rect(self.ui_surface, (0, 0, 0, 255), background_rect, border_radius=self.border_radius)

        # Blit text surfaces
        for surf in self.text_surfaces:
            text_x_aligned = (SCREEN_WIDTH - surf.get_width()) // 2 if self.center_text else text_x
            self.ui_surface.blit(surf, (text_x_aligned, text_y))
            text_y += surf.get_height()

    def get_alpha(self, elapsed):
        if elapsed < self.fade_in:
            return (elapsed / self.fade_in)
        elif elapsed < self.fade_in + self.wait_time:
            return 1.0
        elif elapsed < self.fade_in + self.wait_time + self.fade_out:
            fade_elapsed = elapsed - (self.fade_in + self.wait_time)
            return (1 - (fade_elapsed / self.fade_out))
        else:
            self.finished = True
            return 0.0

    def update(self):
        elapsed = time.time() - self.start_time
        if self.finished:
            return

        # Update alpha for shader instead of modifying the surface
        self.mesh.alpha = self.get_alpha(elapsed)
        self.mesh.update()

    def render(self):
        self.update()
        if self.mesh.alpha == 0:
            return # Do not render a fully transparent mesh
        self.context.disable(mgl.DEPTH_TEST)
        self.context.enable(mgl.BLEND)
        self.context.blend_func = (mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA)

        self.mesh.render()

        self.context.disable(mgl.BLEND)
        self.context.enable(mgl.DEPTH_TEST)

    def destroy(self):
        self.mesh.destroy()