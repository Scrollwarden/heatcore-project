import sys
import pygame as pg

DEFAULT_CONTROLS = {
    "Strafe Left": pg.K_q,    # typical AZERTY: Q for left
    "Forward": pg.K_z,        # Z is forward on AZERTY
    "Strafe Right": pg.K_d,   # D for right
    "Backward": pg.K_s,       # S is backward
    "Up": pg.K_a,             # New: A for vertical up
    "Down": pg.K_e,           # New: E for vertical down
    "Toggle Menu": pg.K_k     # Toggle the menu
}

# Preexisting UI element classes
class CompassBar:
    def __init__(self, screen, x, y, length, color=(255, 255, 255), thickness=5):
        """
        @return
        """
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

        border_radius = 10  # Fully rounded edges
        pg.draw.rect(self.screen, color, (rect_x, rect_y, rect_width, rect_height), border_radius=border_radius)


# UI container classes
class UI1:
    """
    This class holds all of the preexisting UI elements: the compass (bar and markers) and the heatcore bar.
    """
    def __init__(self, screen):
        self.screen = screen

        # Initialize CompassBar
        self.compass_bar_x = screen.get_width() // 2
        self.compass_bar_y = 50
        self.compass_bar_length = 600
        self.compass_bar = CompassBar(screen, self.compass_bar_x, self.compass_bar_y, self.compass_bar_length)

        # Initialize CompassMarkers for the four cardinal directions
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

        # Initialize HeatcoreBar
        height = 200
        width = 10
        x = screen.get_width() - (width + 50)
        y = screen.get_height() - (height + 50)
        self.heatcore_bar = HeatcoreBar(screen, x, y, width, height)

    def draw(self, yaw):
        """
        Draws the UI1 elements. The 'yaw' parameter is used to update the positions of the compass markers.
        """
        # Draw the compass bar
        self.compass_bar.draw()

        # Draw each compass marker if it is within ±90° of the current yaw
        for marker in self.compass_markers:
            if abs((yaw - marker.yaw + 180) % 360 - 180) <= 90:
                marker_position = (
                    self.compass_bar_x
                    + (((yaw - marker.yaw + 180) % 360 - 180) / 90 * (self.compass_bar_length // 2))
                )
                marker.set_position(marker_position)
                marker.draw()

        # Draw the heatcore bar
        self.heatcore_bar.draw()

    def update_heatcore_count(self, count):
        """
        Updates the heatcore count displayed by the heatcore bar.
        """
        self.heatcore_bar.set_heatcore_count(count)

class UI2:
    def __init__(self, screen):
        """
        A futuristic, low-poly style menu overlay.
        This menu now has three buttons:
          - Close (ends the game),
          - Play (resumes the game), and
          - Controls (opens the control settings submenu, UI2-1).
        """
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.active = False  # Whether this menu is displayed.
        # Create a translucent overlay.
        self.overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.bg_color = (20, 20, 20, 180)
        self.overlay.fill(self.bg_color)

        # Define button rectangles.
        self.close_button_rect = pg.Rect(self.width - 130, 20, 100, 50)
        self.play_button_rect = pg.Rect((self.width - 200) // 2, (self.height - 100) // 2, 200, 50)
        # Place the Controls button below the Play button.
        self.controls_button_rect = pg.Rect((self.width - 150) // 2, self.play_button_rect.bottom + 20, 150, 50)

        # Initialize fonts.
        self.font = pg.font.SysFont("Arial", 24)
        self.title_font = pg.font.SysFont("Arial", 48)
        self.subtitle_font = pg.font.SysFont("Arial", 32)

        # Flag to indicate that the Controls submenu was requested.
        self.controls_requested = False

    def draw_text_with_outline(self, text, font, text_color, center, outline_color=(0, 0, 0), outline_offset=2):
        """Draw text with an outline (neon-like effect)."""
        base_text = font.render(text, True, text_color)
        text_rect = base_text.get_rect(center=center)
        # Draw outline by rendering multiple copies at slight offsets.
        for dx in range(-outline_offset, outline_offset + 1):
            for dy in range(-outline_offset, outline_offset + 1):
                if dx != 0 or dy != 0:
                    outline = font.render(text, True, outline_color)
                    outline_rect = outline.get_rect(center=(center[0] + dx, center[1] + dy))
                    self.screen.blit(outline, outline_rect)
        self.screen.blit(base_text, text_rect)

    def draw_low_poly_button(self, rect, color, text):
        """Draw an angular, low-poly style button with an outline."""
        x, y, w, h = rect
        offset = 10  # for beveled corners.
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
        """Draw the futuristic UI2 overlay with title, subtitle, and three buttons."""
        # Draw the translucent background.
        self.screen.blit(self.overlay, (0, 0))

        # Draw a low-poly polygon for a futuristic accent.
        top_poly_points = [
            (0, 0),
            (self.width * 0.5, self.height * 0.15),
            (self.width, 0),
            (self.width, self.height * 0.25),
            (self.width * 0.5, self.height * 0.35),
            (0, self.height * 0.25)
        ]
        pg.draw.polygon(self.screen, (30, 30, 30), top_poly_points)

        # Draw title and subtitle.
        self.draw_text_with_outline("HEATCORE", self.title_font, (0, 255, 255),
                                    (self.width // 2, 60), outline_color=(0, 0, 0), outline_offset=2)
        self.draw_text_with_outline("frozen worlds", self.subtitle_font, (180, 180, 255),
                                    (self.width // 2, 110), outline_color=(0, 0, 0), outline_offset=1)

        # Draw the three buttons.
        self.draw_low_poly_button(self.close_button_rect, (200, 0, 0), "Close")
        self.draw_low_poly_button(self.play_button_rect, (0, 200, 0), "Play")
        self.draw_low_poly_button(self.controls_button_rect, (0, 0, 200), "Controls")

    def handle_event(self, event):
        """
        Process events when UI2 is active.
          - Clicking Close ends the game.
          - Clicking Play resumes the game.
          - Clicking Controls requests the Control Settings submenu.
        """
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
        """
        A futuristic control settings submenu (UI2‑1) where the player can rebind controls.
        The default bindings are copied from DEFAULT_CONTROLS.
        New controls include:
          - "Strafe Left"
          - "Forward"
          - "Strafe Right"
          - "Backward"
          - "Up"
          - "Down"
          - "Toggle Menu"
        """
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.active = False  # Whether this submenu is currently shown.
        self.overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.bg_color = (20, 20, 20, 200)  # Dark, translucent background.
        self.overlay.fill(self.bg_color)

        # Initialize fonts.
        self.title_font = pg.font.SysFont("Arial", 48)
        self.font = pg.font.SysFont("Arial", 24)

        # Copy the global default key bindings.
        self.bindings = DEFAULT_CONTROLS.copy()

        # Create button rectangles for each control.
        self.control_buttons = {}
        start_y = 150
        spacing = 60
        button_width = 100
        button_height = 40
        for i, action in enumerate(self.bindings.keys()):
            # Place each control's button to the right of its label.
            x = self.width // 2 + 100
            y = start_y + i * spacing
            self.control_buttons[action] = pg.Rect(x, y, button_width, button_height)

        # Back button to return to UI2.
        self.back_button_rect = pg.Rect((self.width - 150) // 2, self.height - 100, 150, 50)

        # This variable holds the action that is waiting for a new key press.
        self.awaiting_binding = None

        # Flag that signals the Back button was pressed to return to UI2.
        self.return_to_ui2 = False

    def draw(self):
        """Draw the control settings submenu with the current key bindings and a Back button."""
        # Draw the translucent background.
        self.screen.blit(self.overlay, (0, 0))

        # Draw the title.
        title_text = self.title_font.render("Control Settings", True, (0, 255, 255))
        title_rect = title_text.get_rect(center=(self.width // 2, 60))
        self.screen.blit(title_text, title_rect)

        # Draw each control's label and its corresponding key button.
        start_y = 150
        spacing = 60
        for i, (action, key) in enumerate(self.bindings.items()):
            # Draw the label.
            label_text = self.font.render(action + ":", True, (255, 255, 255))
            label_rect = label_text.get_rect(midleft=(self.width // 2 - 100, start_y + i * spacing + 20))
            self.screen.blit(label_text, label_rect)
            # Draw the button for this control.
            button_rect = self.control_buttons[action]
            # Highlight the button if this control is awaiting a new key.
            color = (255, 165, 0) if self.awaiting_binding == action else (0, 200, 0)
            pg.draw.rect(self.screen, color, button_rect)
            # Render the current key name.
            key_name = pg.key.name(key).upper()
            key_text = self.font.render(key_name, True, (255, 255, 255))
            key_rect = key_text.get_rect(center=button_rect.center)
            self.screen.blit(key_text, key_rect)

        # Draw the Back button.
        pg.draw.rect(self.screen, (200, 0, 0), self.back_button_rect)
        back_text = self.font.render("Back", True, (255, 255, 255))
        back_rect = back_text.get_rect(center=self.back_button_rect.center)
        self.screen.blit(back_text, back_rect)

    def handle_event(self, event):
        """
        Process events for rebinding keys:
          - If awaiting a new binding, any key press will rebind that action.
          - Mouse clicks on a control's button begin the rebinding process.
          - Clicking the Back button exits the submenu and signals a return to UI2.
        """
        # If we are awaiting a new key binding for an action.
        if self.awaiting_binding is not None:
            if event.type == pg.KEYDOWN:
                self.bindings[self.awaiting_binding] = event.key
                # Also update the global default keybind variable.
                DEFAULT_CONTROLS[self.awaiting_binding] = event.key
                print(f"Rebound {self.awaiting_binding} to {pg.key.name(event.key).upper()}")
                self.awaiting_binding = None
            return

        # If not awaiting a binding, check for mouse clicks.
        if event.type == pg.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            # Check if any control button is clicked.
            for action, rect in self.control_buttons.items():
                if rect.collidepoint(mouse_pos):
                    self.awaiting_binding = action
                    print(f"Awaiting new key for {action}...")
                    return
            # Check if the Back button is clicked.
            if self.back_button_rect.collidepoint(mouse_pos):
                print("Back button clicked: Returning to main menu (UI2).")
                self.active = False
                self.return_to_ui2 = True
