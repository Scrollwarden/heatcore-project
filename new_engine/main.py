from ast import Index
import sys
import time

import pygame as pg
import moderngl as mgl
import numpy as np
import matplotlib.pyplot as plt

from camera import Camera
from light import Light
from scene import Scene
from hud_elements import UI1, UI2, UI2_1, DEFAULT_CONTROLS  # Import UI classes and the default key bindings

# --------------------------------------------------------------------- #
# Deco FPS format
# --------------------------------------------------------------------- #
def format_fps(delta_time, target_fps):
    current_fps = 1 / delta_time
    diff_percentage = (current_fps - target_fps) / target_fps
    if diff_percentage >= -0.1:
        color_code = "\033[32m"  # Green
    elif diff_percentage >= -0.2:
        color_code = "\033[94m"  # Light Blue
    elif diff_percentage >= -0.4:
        color_code = "\033[34m"  # Blue
    elif diff_percentage >= -0.6:
        color_code = "\033[33m"  # Orange
    else:
        color_code = "\033[31m"  # Red

    reset_code = "\033[0m"
    formatted_fps = f"{current_fps:.3f}"
    return f"{color_code}{formatted_fps}{reset_code}"

# --------------------------------------------------------------------- #
# Logs
# --------------------------------------------------------------------- #
class Logs:
    def __init__(self, frame_count_limit: int = 10000):
        self.index = 0
        self.frame_count_limit = frame_count_limit
        self.times = np.zeros((frame_count_limit,), dtype=np.float32)
        self.accumulated_time = np.zeros((frame_count_limit,), dtype=np.float32)
        self.fps = np.zeros((frame_count_limit,), dtype=np.float32)
        self.chunks_loaded = np.zeros((frame_count_limit,), dtype=np.uint32)
        self.chunks_loading = np.zeros((frame_count_limit,), dtype=np.uint32)

    def add_to_log(self, delta_time, chunks_loaded, chunks_loading):
        if self.index >= self.frame_count_limit:
            print("===========================================================")
            print("!!! Not enough place in logs to add new information !!!")
            print("===========================================================")
            return
        self.times[self.index] = delta_time
        self.fps[self.index] = 1 / delta_time
        self.chunks_loaded[self.index] = chunks_loaded
        self.chunks_loading[self.index] = chunks_loading

        if self.index == 0:
            self.accumulated_time[self.index] = delta_time
        else:
            self.accumulated_time[self.index] = (
                self.accumulated_time[self.index - 1] + delta_time
            )

        self.index += 1

    def display_windows(self):
        x = self.accumulated_time[:self.index]

        metrics = [
            ("FPS", self.fps[:self.index], "Frames Per Second", "green"),
            ("Chunks Loaded", self.chunks_loaded[:self.index], "Chunks Loaded", "orange"),
            ("Chunks Loading", self.chunks_loading[:self.index], "Chunks Loading", "red"),
        ]

        for i, (title, data, ylabel, color) in enumerate(metrics):
            plt.figure(i + 1, figsize=(8, 5))
            plt.plot(x, data, label=title, color=color)
            plt.title(title)
            plt.xlabel("Time (s)")
            plt.ylabel(ylabel)
            plt.legend()
            plt.grid()
            plt.tight_layout()

        plt.show()

# --------------------------------------------------------------------- #
# Main GraphicsEngine Class
#  3D World    UI    Screen
# --------------------------------------------------------------------- #
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

        # Start with the mouse hidden (for world movement)
        pg.mouse.set_visible(False)

        self.context = mgl.create_context()
        self.context.enable(flags=mgl.DEPTH_TEST | mgl.CULL_FACE)

        self.light = Light()
        # IMPORTANT: Ensure your Camera update method consults self.engine.controls!
        self.camera = Camera(self)
        self.scene = Scene(self)
        self.logs = Logs()

        # Create a Pygame Surface for UI drawing (2D overlay).
        self.ui_surface = pg.Surface(self.window_size, pg.SRCALPHA)

        # Create UI elements.
        self.ui1 = UI1(self.ui_surface)     # In-game HUD
        self.ui2 = UI2(self.ui_surface)     # Main futuristic menu
        self.ui2_1 = UI2_1(self.ui_surface)   # Control settings submenu

        # Create a ModernGL texture to hold the UI surface data.
        self.ui_texture = self.context.texture(self.window_size, 4)
        self.ui_texture.filter = (mgl.LINEAR, mgl.LINEAR)

        # Create a simple program + quad to render the UI texture.
        self.prog = self.context.program(
            vertex_shader="""
            #version 330
            in vec2 in_pos;
            in vec2 in_uv;
            out vec2 v_uv;
            void main() {
                gl_Position = vec4(in_pos, 0.0, 1.0);
                v_uv = in_uv;
            }
            """,
            fragment_shader="""
            #version 330
            uniform sampler2D ui_texture;
            in vec2 v_uv;
            out vec4 f_color;
            void main() {
                f_color = texture(ui_texture, v_uv);
            }
            """
        )
        self.prog['ui_texture'] = 0

        vertices = np.array([
            #  x,    y,   u,   v
            -1.0, -1.0,  0.0,  0.0,
             1.0, -1.0,  1.0,  0.0,
            -1.0,  1.0,  0.0,  1.0,
             1.0,  1.0,  1.0,  1.0,
        ], dtype='f4')

        self.vbo = self.context.buffer(vertices.tobytes())
        self.vao = self.context.simple_vertex_array(
            self.prog, self.vbo, 'in_pos', 'in_uv'
        )

        # Import default controls from the UI module.
        self.controls = DEFAULT_CONTROLS.copy()

        print("Graphics engine initialized successfully")

    # ------------------------------------------------------------ #
    # Main Loop Methods
    # ------------------------------------------------------------ #
    def check_events(self):
        for event in pg.event.get():
            # Global quit events.
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.scene.destroy()
                pg.quit()
                self.logs.display_windows()
                sys.exit()

            # If the control settings submenu (UI2-1) is active, forward events to it.
            if self.ui2_1.active:
                self.ui2_1.handle_event(event)
                continue
            # Else if the main menu (UI2) is active, forward events to it.
            elif self.ui2.active:
                self.ui2.handle_event(event)
                continue
            else:
                # When no menu is active, check if the Toggle Menu key (from current bindings) was pressed.
                if event.type == pg.KEYDOWN and event.key == self.controls["Toggle Menu"]:
                    self.ui2.active = True
                    pg.mouse.set_visible(True)

            # (Other game events can be processed here if needed.)

        # Menu switching:
        # If UI2 requested the control settings submenu, switch to UI2-1.
        if self.ui2.controls_requested:
            self.ui2.controls_requested = False
            self.ui2_1.active = True
            pg.mouse.set_visible(True)

        # If no menu is active, ensure the mouse is hidden.
        if not self.ui2.active and not self.ui2_1.active:
            pg.mouse.set_visible(False)

    def get_time(self):
        self.time = pg.time.get_ticks() * 0.001

    def render(self):
        # --- Clear the 3D scene ---
        self.context.clear(color=(0.08, 0.16, 0.18, 1.0))
        self.scene.render()

        # --- Draw UI elements onto the Pygame surface ---
        self.ui_surface.fill((0, 0, 0, 0))  # Clear with full transparency

        if self.ui2_1.active:
            self.ui2_1.draw()
        elif self.ui2.active:
            self.ui2.draw()
        else:
            self.ui1.draw(self.camera.yaw)

        # --- Update the UI texture and render it ---
        ui_texture_data = pg.image.tostring(self.ui_surface, "RGBA", True)
        self.ui_texture.write(ui_texture_data)

        self.context.disable(mgl.DEPTH_TEST)    # Render UI on top
        self.context.enable(mgl.BLEND)          # Enable alpha blending
        self.context.blend_func = (mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA)

        self.ui_texture.use(location=0)
        self.vao.render(mgl.TRIANGLE_STRIP)

        self.context.disable(mgl.BLEND)
        self.context.enable(mgl.DEPTH_TEST)

        pg.display.flip()

    def run(self):
        while True:
            start_time = time.time()

            self.get_time()
            self.check_events()

            # Only update camera (and world movement) if no menu is active.
            if not (self.ui2.active or self.ui2_1.active):
                self.camera.update()  # Make sure your Camera uses self.engine.controls for movement

            # Update shader programs if needed.
            for shader_program in self.scene.shader_programs.values():
                shader_program.update()

            # Update control mappings from UI2-1 so new bindings take effect.
            if not self.ui2_1.active:
                self.controls = self.ui2_1.bindings

            self.render()

            self.delta_time = self.clock.tick(60)
            elapsed_time = time.time() - start_time

            print(f"FPS: {format_fps(elapsed_time, 60)}, Frame Time: {elapsed_time:.3f}s")

            num_loaded = len(self.scene.chunks)
            num_loading = len(self.scene.chunks_loading)
            self.logs.add_to_log(elapsed_time, num_loaded, num_loading)
            print()

# ------------------------------------------------------------ #
# Entry Point
# ------------------------------------------------------------ #
print("Please wait while loading ...")
if __name__ == '__main__':
    app = GraphicsEngine()
    app.run()
