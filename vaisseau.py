import pygame
import json

# Load polygons from file if available, otherwise use default
def load_polygons():
    try:
        with open("polygons.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [
            [(0, 0.5), (0, 3.5), (-1, 0.5)],
            [(0, 0), (0, 4), (-1.5, 0)],
            [(-1.5, 0), (-4.5, -1), (-5, -3), (-1.5, -3), (-3.7, -1.5)],
            [(0, -2.5), (0, -0.5), (-0.5, -0.5), (-0.5, -2), (-1.5, -2.7), (-1.5, -3), (-1, -3)],
            [(-1, -1), (0, -1), (0, 0), (-1, 0)]
        ]

polygons = load_polygons()

# Scale and shift to fit in window
SCALE = 50
WIDTH, HEIGHT = 600, 600
CENTER = (WIDTH // 2, HEIGHT // 2)


def transform(points):
    return [(int(CENTER[0] + x * SCALE), int(CENTER[1] - y * SCALE)) for x, y in points]


def inverse_transform(point):
    x, y = point
    return ((x - CENTER[0]) / SCALE, (CENTER[1] - y) / SCALE)


def save_polygons():
    with open("polygons.json", "w") as f:
        json.dump(polygons, f)




# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Polygon Display")
clock = pygame.time.Clock()

selected_point = None
running = True
while running:
    screen.fill((255, 255, 255))  # White background

    for i in range(len(polygons) - 1, -1, -1):
        poly = polygons[i]
        inverse_poly = [(- p[0], p[1]) for p in poly]
        for p in (poly, inverse_poly):
            if i == 0:
                pygame.draw.polygon(screen, (255, 255, 255), transform(p))
            elif i == 1:
                sx, sy = 0, 0
                for x, y in p:
                    sx += x
                    sy += y
                factor = 1.5
                tp = [[factor * (v[0] - sx / len(p)) + sx / len(p), factor * (v[1] - sy / len(p)) + sy / len(p)] for v in p]
                pygame.draw.polygon(screen, (255, 255, 255), transform(tp))
                pygame.draw.polygon(screen, (0, 0, 0), transform(p))
            else:
                pygame.draw.polygon(screen, (136, 40, 76), transform(p))

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_polygons()
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            for poly in polygons:
                for i, point in enumerate(transform(poly)):
                    if pygame.Rect(point[0] - 5, point[1] - 5, 10, 10).collidepoint(mouse_pos):
                        selected_point = (poly, i)
        elif event.type == pygame.KEYDOWN and selected_point:
            poly, i = selected_point
            if event.key == pygame.K_LEFT:
                poly[i] = (poly[i][0] - 0.05, poly[i][1])
            elif event.key == pygame.K_RIGHT:
                poly[i] = (poly[i][0] + 0.05, poly[i][1])
            elif event.key == pygame.K_UP:
                poly[i] = (poly[i][0], poly[i][1] + 0.05)
            elif event.key == pygame.K_DOWN:
                poly[i] = (poly[i][0], poly[i][1] - 0.05)

    clock.tick(60)

pygame.quit()
