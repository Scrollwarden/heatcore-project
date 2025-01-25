import pygame
import math

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
        pygame.draw.line(self.screen, self.color, start_pos, end_pos, self.thickness)

class CompassMarker:
    def __init__(self, screen, x, y, yaw, color=(255, 255, 255), size=10, thickness=5, image_path=None):
        self.screen = screen
        self.x = x
        self.y = y
        self.yaw = yaw
        self.color = color
        self.size = size
        self.thickness = thickness
        self.image = pygame.image.load(image_path) if image_path else None
        self.image_offset_y = 20

    def draw(self):
        start_pos = (self.x, self.y - self.size // 2)
        end_pos = (self.x, self.y + self.size // 2)
        pygame.draw.line(self.screen, self.color, start_pos, end_pos, self.thickness)

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
        section_height = self.height // self.sections

        if self.heatcore_count == self.sections:
            self._draw_full_bar_with_smooth_pulse()
        else:
            for i in range(self.sections):
                color = self.colors["active"] if i < self.heatcore_count else self.colors["inactive"]
                self._draw_section(i, color)

    def _draw_section(self, index, color):

        section_height = self.height // self.sections
        rect_x = self.x
        rect_y = self.y + self.height - (index + 1) * section_height
        rect_width = self.width
        rect_height = section_height

        if index == 0:
            border_radius = 5
            pygame.draw.rect(self.screen, color, (rect_x, rect_y, rect_width, rect_height), border_top_left_radius=0, border_top_right_radius=0, border_bottom_left_radius=border_radius, border_bottom_right_radius=border_radius)
        elif index == self.sections - 1:
            border_radius = 5
            pygame.draw.rect(self.screen, color, (rect_x, rect_y, rect_width, rect_height), border_top_left_radius=border_radius, border_top_right_radius=border_radius, border_bottom_left_radius=0, border_bottom_right_radius=0)
        else:
            pygame.draw.rect(self.screen, color, (rect_x, rect_y, rect_width, rect_height), border_radius=0)

    def _draw_full_bar_with_smooth_pulse(self):
        current_time = pygame.time.get_ticks() / 1000
        pulsation_factor = (math.sin(2 * math.pi * current_time / self.pulsation_speed) + 1) / 2

        base_color = self.colors["full_base"]
        target_color = self.colors["full_target"]
        pulsate_color = (
            int(base_color[0] + (target_color[0] - base_color[0]) * pulsation_factor),
            int(base_color[1] + (target_color[1] - base_color[1]) * pulsation_factor),
            int(base_color[2] + (target_color[2] - base_color[2]) * pulsation_factor),
        )

        pygame.draw.rect(self.screen, pulsate_color, (self.x, self.y, self.width, self.height), border_radius=3)




def create_compass(screen):
    compass_bar_x = screen.get_width() // 2
    compass_bar_y = 50
    compass_bar_length = 600

    marker_data = [
        {"yaw": 0, "color": (255, 0, 0), "size": 15, "thickness": 8},  # North
        {"yaw": 180, "color": (0, 255, 0), "size": 15, "thickness": 8},  # South
        {"yaw": 90, "color": (0, 0, 255), "size": 15, "thickness": 8},  # East
        {"yaw": 270, "color": (255, 255, 0), "size": 15, "thickness": 8},  # West
    ]

    compass_bar = CompassBar(screen, compass_bar_x, compass_bar_y, compass_bar_length)
    markers = [
        CompassMarker(
            screen,
            compass_bar_x,
            compass_bar_y,
            yaw=data["yaw"],
            color=data.get("color", (255, 255, 255)),
            size=data.get("size", 10),
            thickness=data.get("thickness", 5),
        )
        for data in marker_data
    ]

    def draw_compass(yaw):
        compass_bar.draw()
        for marker in markers:
            if abs((yaw - marker.yaw + 180) % 360 - 180) <= 90:
                marker_position = (
                    compass_bar_x
                    + ((yaw - marker.yaw + 180) % 360 - 180) / 90 * (compass_bar_length // 2)
                )
                marker.set_position(marker_position)
                marker.draw()

    return draw_compass

def create_heatcore_bar(screen):
    x = 50
    height = 200
    y = screen.get_height() - (height + 50)
    width = 10
    return HeatcoreBar(screen, x, y, width, height)
