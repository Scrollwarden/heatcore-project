import sys
import pygame as pg

DEFAULT_CONTROLS = {
    "Strafe Left": pg.K_q,
    "Forward": pg.K_z,
    "Strafe Right": pg.K_d,
    "Backward": pg.K_s,
    "Up": pg.K_a,
    "Down": pg.K_e,
    "Toggle Menu": pg.K_k
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

        self.draw_low_poly_button(self.close_button_rect, (200, 0, 0), "Close")
        self.draw_low_poly_button(self.play_button_rect, (0, 200, 0), "Play")
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

        title_text = self.title_font.render("Control Settings", True, (0, 255, 255))
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
        back_text = self.font.render("Back", True, (255, 255, 255))
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
