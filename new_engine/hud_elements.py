import sys
import pygame as pg
from intel_arti.cube_v2.cube import Cube
from intel_arti.cube_v2.cube_ui import Renderer, Camera, CubeUI
import math



DEFAULT_CONTROLS = {
    "Strafe Left": pg.K_q,
    "Forward": pg.K_z,
    "Strafe Right": pg.K_d,
    "Backward": pg.K_s,
    "Up": pg.K_SPACE,
    "Down": pg.K_LSHIFT,
    "Toggle Menu": pg.K_ESCAPE
}

class CompassBar:
    def __init__(self, screen, x, y, length, color=(255, 255, 255), thickness=5):
        self.screen = screen
        self.x = x
        self.y = y
        self.length = length
        self.color = color
        self.thickness = thickness

    def draw(self):
        start_pos = (self.x - self.length // 2, self.y)
        end_pos = (self.x + self.length // 2, self.y)
        pg.draw.line(self.screen, self.color, start_pos, end_pos, self.thickness)

class CompassMarker:
    def __init__(self, screen, x, y, yaw, color=(255, 255, 255), size=10, thickness=5, image_path=None):
        self.screen = screen
        self.x = x
        self.y = y
        self.yaw = yaw
        self.color = color
        self.size = size
        self.thickness = thickness
        self.image = pg.image.load(image_path) if image_path else None
        self.image_offset_y = 20

    def draw(self):
        start_pos = (self.x, self.y - self.size // 2)
        end_pos = (self.x, self.y + self.size // 2)
        pg.draw.line(self.screen, self.color, start_pos, end_pos, self.thickness)

        if self.image:
            image_x = self.x - self.image.get_width() // 2
            image_y = self.y + self.image_offset_y
            self.screen.blit(self.image, (image_x, image_y))

    def set_position(self, x):
        self.x = x

class HeatcoreBar:
    def __init__(self, screen, x, y, width, height):
        self.screen = screen
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.heatcore_count = 0
        self.sections = 3
        self.colors = {
            "inactive": (50, 50, 50),
            "active": (255, 165, 0),
            "full_base": (255, 165, 0),
            "full_target": (255, 255, 0),
        }
        self.pulsation_speed = 7

    def set_heatcore_count(self, count):
        self.heatcore_count = max(0, min(count, self.sections))

    def draw(self):
        section_spacing = 5  # Space between bars
        bar_height = (self.height - (self.sections - 1) * section_spacing) // self.sections

        for i in range(self.sections):
            color = self.colors["active"] if i < self.heatcore_count else self.colors["inactive"]
            self._draw_section(i, color, bar_height, section_spacing)

    def _draw_section(self, index, color, bar_height, section_spacing):
        rect_x = self.x
        rect_y = self.y + self.height - ((index + 1) * (bar_height + section_spacing))
        rect_width = self.width
        rect_height = bar_height

        border_radius = 10
        pg.draw.rect(self.screen, color, (rect_x, rect_y, rect_width, rect_height), border_radius=border_radius)


class UI1:
    def __init__(self, screen):
        self.screen = screen

        self.compass_bar_x = screen.get_width() // 2
        self.compass_bar_y = 50
        self.compass_bar_length = 600
        self.compass_bar = CompassBar(screen, self.compass_bar_x, self.compass_bar_y, self.compass_bar_length)

        marker_data = [
            {"yaw": 0, "color": (255, 0, 0), "size": 15, "thickness": 8},    # North
            {"yaw": 180, "color": (0, 255, 0), "size": 15, "thickness": 8},  # South
            {"yaw": 90, "color": (0, 0, 255), "size": 15, "thickness": 8},   # East
            {"yaw": 270, "color": (255, 255, 0), "size": 15, "thickness": 8},  # West
        ]
        self.compass_markers = [
            CompassMarker(
                screen,
                self.compass_bar_x,
                self.compass_bar_y,
                yaw=data["yaw"],
                color=data.get("color", (255, 255, 255)),
                size=data.get("size", 10),
                thickness=data.get("thickness", 5),
            )
            for data in marker_data
        ]

        height = 200
        width = 10
        x = screen.get_width() - (width + 50)
        y = screen.get_height() - (height + 50)
        self.heatcore_bar = HeatcoreBar(screen, x, y, width, height)

    def draw(self, yaw):
        self.compass_bar.draw()

        for marker in self.compass_markers:
            if abs((yaw - marker.yaw + 180) % 360 - 180) <= 90:
                marker_position = (
                    self.compass_bar_x
                    + (((yaw - marker.yaw + 180) % 360 - 180) / 90 * (self.compass_bar_length // 2))
                )
                marker.set_position(marker_position)
                marker.draw()

        self.heatcore_bar.draw()

    def update_heatcore_count(self, count):
        self.heatcore_bar.set_heatcore_count(count)

class UI2:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.active = False
        self.overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.bg_color = (20, 20, 20, 180)
        self.overlay.fill(self.bg_color)

        self.close_button_rect = pg.Rect(self.width - 130, 20, 100, 50)
        self.play_button_rect = pg.Rect((self.width - 200) // 2, (self.height - 100) // 2, 200, 50)
        self.controls_button_rect = pg.Rect((self.width - 150) // 2, self.play_button_rect.bottom + 20, 150, 50)

        self.font = pg.font.SysFont("Arial", 24)
        self.title_font = pg.font.SysFont("Arial", 48)
        self.subtitle_font = pg.font.SysFont("Arial", 32)

        self.controls_requested = False

    def draw_text_with_outline(self, text, font, text_color, center, outline_color=(0, 0, 0), outline_offset=2):
        base_text = font.render(text, True, text_color)
        text_rect = base_text.get_rect(center=center)
        for dx in range(-outline_offset, outline_offset + 1):
            for dy in range(-outline_offset, outline_offset + 1):
                if dx != 0 or dy != 0:
                    outline = font.render(text, True, outline_color)
                    outline_rect = outline.get_rect(center=(center[0] + dx, center[1] + dy))
                    self.screen.blit(outline, outline_rect)
        self.screen.blit(base_text, text_rect)

    def draw_low_poly_button(self, rect, color, text):
        x, y, w, h = rect
        offset = 10
        points = [
            (x, y + offset),
            (x + offset, y),
            (x + w - offset, y),
            (x + w, y + offset),
            (x + w, y + h - offset),
            (x + w - offset, y + h),
            (x + offset, y + h),
            (x, y + h - offset)
        ]
        pg.draw.polygon(self.screen, color, points)
        pg.draw.polygon(self.screen, (0, 0, 0), points, 2)
        btn_text = self.font.render(text, True, (255, 255, 255))
        btn_text_rect = btn_text.get_rect(center=rect.center)
        self.screen.blit(btn_text, btn_text_rect)

    def draw(self):
        self.screen.blit(self.overlay, (0, 0))

        top_poly_points = [
            (0, 0),
            (self.width * 0.5, self.height * 0.15),
            (self.width, 0),
            (self.width, self.height * 0.25),
            (self.width * 0.5, self.height * 0.35),
            (0, self.height * 0.25)
        ]
        pg.draw.polygon(self.screen, (30, 30, 30), top_poly_points)

        self.draw_text_with_outline("HEATCORE", self.title_font, (0, 255, 255),
                                    (self.width // 2, 60), outline_color=(0, 0, 0), outline_offset=2)
        self.draw_text_with_outline("frozen worlds", self.subtitle_font, (180, 180, 255),
                                    (self.width // 2, 110), outline_color=(0, 0, 0), outline_offset=1)

        self.draw_low_poly_button(self.close_button_rect, (200, 0, 0), "Fermer")
        self.draw_low_poly_button(self.play_button_rect, (0, 200, 0), "Jouer")
        self.draw_low_poly_button(self.controls_button_rect, (0, 0, 200), "Controls")

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if self.close_button_rect.collidepoint(mouse_pos):
                print("Close button clicked: Ending the game.")
                pg.quit()
                sys.exit()
            elif self.play_button_rect.collidepoint(mouse_pos):
                print("Play button clicked!")
                self.active = False
                pg.mouse.set_visible(False)
            elif self.controls_button_rect.collidepoint(mouse_pos):
                print("Controls button clicked: Accessing Control Settings.")
                self.active = False
                self.controls_requested = True
                pg.mouse.set_visible(True)

class UI2_1:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.active = False  # Whether this submenu is currently shown.
        self.overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.bg_color = (20, 20, 20, 200)  # Dark, translucent background.
        self.overlay.fill(self.bg_color)

        self.title_font = pg.font.SysFont("Arial", 48)
        self.font = pg.font.SysFont("Arial", 24)

        self.bindings = DEFAULT_CONTROLS.copy()

        self.control_buttons = {}
        start_y = 150
        spacing = 60
        button_width = 100
        button_height = 40
        for i, action in enumerate(self.bindings.keys()):
            x = self.width // 2 + 100
            y = start_y + i * spacing
            self.control_buttons[action] = pg.Rect(x, y, button_width, button_height)

        self.back_button_rect = pg.Rect((self.width - 150) // 2, self.height - 100, 150, 50)

        self.awaiting_binding = None

        self.return_to_ui2 = False

    def draw(self):
        self.screen.blit(self.overlay, (0, 0))

        title_text = self.title_font.render("Controls", True, (0, 255, 255))
        title_rect = title_text.get_rect(center=(self.width // 2, 60))
        self.screen.blit(title_text, title_rect)

        start_y = 150
        spacing = 60
        for i, (action, key) in enumerate(self.bindings.items()):
            label_text = self.font.render(action + ":", True, (255, 255, 255))
            label_rect = label_text.get_rect(midleft=(self.width // 2 - 100, start_y + i * spacing + 20))
            self.screen.blit(label_text, label_rect)
            button_rect = self.control_buttons[action]
            color = (255, 165, 0) if self.awaiting_binding == action else (0, 200, 0)
            pg.draw.rect(self.screen, color, button_rect)
            key_name = pg.key.name(key).upper()
            key_text = self.font.render(key_name, True, (255, 255, 255))
            key_rect = key_text.get_rect(center=button_rect.center)
            self.screen.blit(key_text, key_rect)

        pg.draw.rect(self.screen, (200, 0, 0), self.back_button_rect)
        back_text = self.font.render("Retour", True, (255, 255, 255))
        back_rect = back_text.get_rect(center=self.back_button_rect.center)
        self.screen.blit(back_text, back_rect)

    def handle_event(self, event):

        if self.awaiting_binding is not None:
            if event.type == pg.KEYDOWN:
                self.bindings[self.awaiting_binding] = event.key
                DEFAULT_CONTROLS[self.awaiting_binding] = event.key
                print(f"Rebound {self.awaiting_binding} to {pg.key.name(event.key).upper()}")
                self.awaiting_binding = None
            return

        if event.type == pg.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            for action, rect in self.control_buttons.items():
                if rect.collidepoint(mouse_pos):
                    self.awaiting_binding = action
                    print(f"Awaiting new key for {action}...")
                    return
            if self.back_button_rect.collidepoint(mouse_pos):
                print("Back button clicked: Returning to main menu (UI2).")
                self.active = False
                self.return_to_ui2 = True


class UI3:
    """
    UI3 creates an overlay that displays a cube game interface (similar to cube_ui)
    along with four buttons:
      - Reset View button: Resets the camera to its initial view.
      - Reset Game button: Resets the cube game.
      - Hint button: Uses a hint (with 5 available hints; remaining count is displayed).
      - Return button: Closes UI3 and returns to UI1.
    """

    def __init__(self, screen):
        self.screen = screen  # the ui_surface passed from GraphicsEngine
        self.width, self.height = self.screen.get_size()
        self.active = True  # UI3 is active when set to True

        # Define a game area (a subregion where the cube game is rendered)
        margin = 50
        self.game_rect = pg.Rect(margin, margin, self.width - 2 * margin, self.height - 200)
        self.game_surface = pg.Surface((self.game_rect.width, self.game_rect.height))

        # Create cube game objects.
        # (Here we set initial camera parameters similar to the cube_ui script.)
        self.camera = Camera(latitude=math.radians(30),
                             longitude=2 * math.pi / 3,
                             distance=10.0)
        # Note: We pass the game area size to the Renderer.
        self.renderer = Renderer(self.camera, screen_data=pg.math.Vector2(self.game_rect.width, self.game_rect.height))
        self.cube = Cube()
        # We use a side_length proportional to the game_rect height.
        self.cube_ui = CubeUI(self.cube, self.renderer, side_length=self.game_rect.height * math.pi)

        # Define buttons (positioned along the bottom of the ui surface)
        button_width = 150
        button_height = 50
        bmargin = 20
        self.buttons = {
            'reset_view': pg.Rect(bmargin, self.height - button_height - bmargin, button_width, button_height),
            'reset_game': pg.Rect(bmargin * 2 + button_width, self.height - button_height - bmargin, button_width,
                                  button_height),
            'hint': pg.Rect(bmargin * 3 + button_width * 2, self.height - button_height - bmargin, button_width,
                            button_height),
            'return': pg.Rect(self.width - button_width - bmargin, self.height - button_height - bmargin, button_width,
                              button_height)
        }
        self.button_color = (0, 128, 255)
        self.button_border_color = (255, 255, 255)
        self.hints_remaining = 5

        # Internal flag to signal exit from UI3
        self.exit_ui3 = False

    def handle_event(self, event):
        """Handle events for both the cube game and the overlay buttons."""
        if event.type == pg.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            # Check if any button is clicked:
            for name, rect in self.buttons.items():
                if rect.collidepoint(mouse_pos):
                    if name == 'reset_view':
                        self.reset_view()
                    elif name == 'reset_game':
                        self.reset_game()
                    elif name == 'hint':
                        self.use_hint()
                    elif name == 'return':
                        self.exit_ui3 = True
                    # If a button was pressed, we don’t pass the event further.
                    return

        # (Optional) Pass mouse motion events for cube rotation if the pointer is inside the game area.
        if event.type == pg.MOUSEMOTION:
            if self.game_rect.collidepoint(event.pos):
                # Example: if the right mouse button is held down, update the camera.
                if event.buttons[2]:
                    rel = event.rel
                    self.camera.update_camera_from_mouse(delta_x=rel[0], delta_y=rel[1])
        # You can also handle key events if desired.

    def reset_view(self):
        """Reset the camera view to its initial parameters."""
        self.camera.longitude = 2 * math.pi / 3
        self.camera.latitude = math.pi / 6
        self.camera.reset_position()
        self.renderer.reset()
        self.cube_ui.reset_info()
        print("Reset view button pressed.")

    def reset_game(self):
        """Restart the cube game with a new cube."""
        self.cube = Cube()
        self.cube_ui = CubeUI(self.cube, self.renderer, side_length=self.game_rect.height * math.pi)
        print("Reset game button pressed.")

    def use_hint(self):
        """Consume one hint (if available) and print a message.
           In your real game you could call an AI agent or display the suggested move.
        """
        if self.hints_remaining > 0:
            print("Hint used!")
            self.hints_remaining -= 1
        else:
            print("No hints remaining.")

    def update(self, dt):
        """
        Update any dynamic elements of the cube game.
        (For this example no explicit update is needed;
         however, you might want to add time‐dependent animations here.)
        """
        # For example, you could update the cube game state:
        # self.cube_ui.update(dt)  <-- if CubeUI provided an update() method.
        pass

    def draw(self):
        """Draw the cube game interface and the overlay buttons onto the UI surface."""
        # Clear the entire UI surface (with transparency if needed)
        self.screen.fill((0, 0, 0, 0))

        # Draw a background for the cube game area
        pg.draw.rect(self.screen, (30, 30, 30), self.game_rect)
        # Clear the game surface and draw the cube game
        self.game_surface.fill((0, 0, 0))
        # Note: We pass a mouse position relative to the game area.
        local_mouse = pg.math.Vector2(pg.mouse.get_pos()[0] - self.game_rect.x,
                                      pg.mouse.get_pos()[1] - self.game_rect.y)
        # The third parameter (False) indicates “no click” in this simple example.
        self.cube_ui.draw(self.game_surface, local_mouse, False)
        # Blit the game surface into the designated game area of the UI surface.
        self.screen.blit(self.game_surface, self.game_rect.topleft)

        # Draw the overlay buttons
        font = pg.font.SysFont("Arial", 20)
        for name, rect in self.buttons.items():
            pg.draw.rect(self.screen, self.button_color, rect)
            pg.draw.rect(self.screen, self.button_border_color, rect, 2)
            if name == 'reset_view':
                text = "Reset View"
            elif name == 'reset_game':
                text = "Reset Game"
            elif name == 'hint':
                text = f"Hint ({self.hints_remaining})"
            elif name == 'return':
                text = "Return"
            text_surf = font.render(text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=rect.center)
            self.screen.blit(text_surf, text_rect)