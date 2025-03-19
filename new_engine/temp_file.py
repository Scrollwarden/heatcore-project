import random
import math
import pygame

RADIUS = 200


def random_normal_vector():
    angle = math.radians(random.uniform(0, 360))
    return math.cos(angle), math.sin(angle)


def random_vector():
    return random.uniform(-1, 1), random.uniform(-1, 1)


def random_data():
    x, y = random_vector()
    while x ** 2 + y ** 2 > 1:
        x, y = random_vector()
    return (math.floor(x * RADIUS + 400), math.floor(y * RADIUS + 300)), random_normal_vector()


def intersect_circle(point, vector, center, radius, offset=0):
    dx, dy = vector
    px, py = point
    cx, cy = center

    a = dx ** 2 + dy ** 2
    b = 2 * ((px - cx) * dx + (py - cy) * dy) # 2 * sum((point - center) * vector)
    c = (px - cx) ** 2 + (py - cy) ** 2 - radius ** 2

    discriminant = b ** 2 - 4 * a * c
    if discriminant < 0:
        return None  # No intersection

    t = (-b + math.sqrt(discriminant)) / (2 * a)  # Take the farthest positive intersection
    return px + (t + offset) * dx, py + (t + offset) * dy


pygame.init()
screen = pygame.display.set_mode((800, 600))
running = True

point, vector = random_data()
end_point = intersect_circle(point, vector, (400, 300), RADIUS, offset=10)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                print("R key pressed")
                point, vector = random_data()
                end_point = intersect_circle(point, vector, (400, 300), RADIUS, offset=10)

    screen.fill((0, 0, 0))

    pygame.draw.circle(screen, (255, 0, 0), (400, 300), RADIUS, 5)
    pygame.draw.circle(screen, (0, 255, 0), point, 5)
    if end_point:
        pygame.draw.line(screen, (0, 0, 255), point, end_point, 4)

    pygame.display.flip()