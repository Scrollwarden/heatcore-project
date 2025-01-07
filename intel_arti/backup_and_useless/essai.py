import pygame

class Cube:
    def __init__(self, center):
        colors = ['firebrick', 'dodgerblue', 'purple', 'blue', 'orange', 'brown',
                  'white', 'yellow', 'lawngreen', 'pink', 'gray70', 'gray40']

        self.colors = [pygame.Color(c) for c in colors]
        self.center = pygame.Vector3(center)
        self.points = [
            pygame.Vector3(-1, -1, 1),
            pygame.Vector3(1, -1, 1),
            pygame.Vector3(1, 1, 1),
            pygame.Vector3(-1, 1, 1),
            pygame.Vector3(-1, -1, -1),
            pygame.Vector3(1, -1, -1),
            pygame.Vector3(1, 1, -1),
            pygame.Vector3(-1, 1, -1),
        ]

        self.lines = [(0, 1), (1, 2), (2, 3), (3, 0), # Front
                      (4, 5), (5, 6), (6, 7), (7, 4), # Back
                      (0, 4), (3, 7), # Left
                      (1, 5), (2, 6)  # Right
        ]

        self.scale = 100

    def draw(self, surface):
        for enum, (i, j) in enumerate(self.lines):
            a = self.points[i] * self.scale + self.center
            a = pygame.Vector2(a.x, a.y)
            b = self.points[j] * self.scale + self.center
            b = pygame.Vector2(b.x, b.y)
            pygame.draw.line(surface, self.colors[enum], a, b)

    def move(self, x, y, z):
        self.center += (x, y, z)

    def rotate(self, angle, x, y, z):
        vector = pygame.Vector3(x, y, z)
        for point in self.points:
            point.rotate_ip(angle, vector)

def main():
    pygame.display.set_caption("Rotating Cube")
    surface = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    rect = surface.get_rect()
    running = True
    delta = 0
    fps = 60

    center = rect.centerx, rect.centery, 0
    cube = Cube(center)
    velocity = 100

    while running:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEMOTION:
                x, y = event.pos
                cube.center = pygame.Vector3(x, y, 0)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    if cube.scale < 160:
                        cube.scale += 2
                elif event.button == 5:
                    if cube.scale > 21:
                        cube.scale -= 2

            elif event.type == pygame.QUIT:
                running = False

        surface.fill("black")
        cube.draw(surface)
        cube.rotate(velocity * delta, 1, 1, 1)
        pygame.display.flip()
        delta = clock.tick(fps) * 0.001

if __name__ == "__main__":
    pygame.init()
    main()
    pygame.quit()