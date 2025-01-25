import pygame
import sys

pygame.init()

width, height = 800, 600
screen = pygame.display.set_mode((width, height))

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
    def __init__(self, screen, x, y, yaw, color=(255, 255, 255), size=10, thickness=5):
        self.screen = screen
        self.x = x
        self.y = y
        self.yaw = yaw
        self.color = color
        self.size = size
        self.thickness = thickness

    def draw(self):
        start_pos = (self.x, self.y - self.size // 2)
        end_pos = (self.x, self.y + self.size // 2)
        pygame.draw.line(self.screen, self.color, start_pos, end_pos, self.thickness)

    def set_position(self, x):
        self.x = x

class ImageLoader:
    def __init__(self, screen, image_path, marker):
        self.screen = screen
        self.image = pygame.image.load(image_path)
        self.marker = marker
        self.offset_y = 20

    def draw(self):
        image_x = self.marker.x - self.image.get_width() // 2
        image_y = self.marker.y + self.offset_y
        self.screen.blit(self.image, (image_x, image_y))

compass_bar = CompassBar(screen, width // 2, 20, 600)

markers = [
    {
        "marker": CompassMarker(screen, width // 2, 20, yaw=0, thickness=8),
        "image_loader": ImageLoader(screen, "north_image.png", None)
    },
    {
        "marker": CompassMarker(screen, width // 2, 20, yaw=180, thickness=8),
        "image_loader": ImageLoader(screen, "custom_image.png", None)
    },
    {
        "marker": CompassMarker(screen, width // 2, 20, yaw=54, thickness=8),
        "image_loader": ImageLoader(screen, "custom_image.png", None)
    }
]

for item in markers:
    item["image_loader"].marker = item["marker"]

yaw = 0

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_q]:
        yaw = (yaw - 0.1) % 360
    if keys[pygame.K_d]:
        yaw = (yaw + 0.1) % 360

    screen.fill((100, 100, 100))

    compass_bar.draw()

    for item in markers:
        marker = item["marker"]
        image_loader = item["image_loader"]

        if abs((yaw - marker.yaw + 180) % 360 - 180) <= 90:
            marker_position = (width // 2) + ((yaw - marker.yaw + 180) % 360 - 180) / 90 * (compass_bar.length // 2)
            marker.set_position(marker_position)
            marker.draw()
            image_loader.draw()

    pygame.display.flip()

pygame.quit()
sys.exit()
