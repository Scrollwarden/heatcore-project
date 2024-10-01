import pygame, sys
import time
from nouveau_cube import Cube

# Screen constants
LINE_WIDTH = 3
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500
ZOOM = 3

# Crosses and Squares
SPACE = 0.2
TOP_CROSS = (((SPACE, SPACE, 0.0), (1 - SPACE, 1 - SPACE, 0.0)), 
             ((SPACE, 1 - SPACE, 0.0), (1 - SPACE, SPACE, 0.0)))
RIGHT_CROSS = (((SPACE, 0.0, SPACE), (1 - SPACE, 0.0, 1 - SPACE)), 
               ((SPACE, 0.0, 1 - SPACE), (1 - SPACE,0.0, SPACE)))
LEFT_CROSS = (((0.0, SPACE, SPACE), (0.0, 1 - SPACE, 1 - SPACE)), 
               ((0.0, SPACE, 1 - SPACE), (0.0, 1 - SPACE, SPACE)))
TOP_SQUARE = ((SPACE, SPACE, 0.0), (1 - SPACE, SPACE, 0.0),
              (1 - SPACE, 1 - SPACE, 0.0), (SPACE, 1 - SPACE, 0.0))
RIGHT_SQUARE = ((SPACE, 0.0, SPACE), (1 - SPACE, 0.0, SPACE),
                (1 - SPACE, 0.0, 1 - SPACE), (SPACE, 0.0, 1 - SPACE))
LEFT_SQUARE = ((0.0, SPACE, SPACE), (0.0, 1 - SPACE, SPACE),
              (0.0, 1 - SPACE, 1 - SPACE), (0.0, SPACE, 1 - SPACE))

# Colors
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 220, 0)
BLUE = (0, 128, 255)
ORANGE = (255, 128, 0)
YELLOW = (255, 255, 0)
GREY = (200, 200, 200)
WHITE = (255, 255, 255)
COLORS = {
    "black": BLACK,
    "red": RED,
    "green": GREEN,
    "blue": BLUE,
    "orange": ORANGE,
    "yellow": YELLOW,
    "grey": GREY,
    "white": WHITE
}
FADED_COLORS = {key: tuple(max(0, num - 80) for num in color) for key, color in COLORS.items()}

# Key
KEY_MAP = {
    pygame.K_r: "R",
    pygame.K_l: "L",
    pygame.K_f: "F",
    pygame.K_b: "B",
    pygame.K_u: "U",
    pygame.K_d: "D",
    pygame.K_m: "M",
    pygame.K_e: "E",
    pygame.K_s: "S",
}

KEY_NUM = (
    pygame.K_1,
    pygame.K_2,
    pygame.K_3,
    pygame.K_4,
    pygame.K_5,
    pygame.K_6,
    pygame.K_7,
    pygame.K_8,
    pygame.K_9
)

class Param:
    ROUND = 15
    LIMIT = 10
    
    def __init__(self) -> None:
        self.ij_data: tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
        self.reset((8.5, 5.0), (-8.5, 5.0), (0.0, -10.0))
    
    def reset(self, pdf_x = None, pdf_y = None, pdf_z = None) -> None:
        if pdf_x == None:
            pdf_x = self.ij_data[0]
        if pdf_y == None:
            pdf_y = self.ij_data[1]
        if pdf_z == None:
            pdf_z = self.ij_data[2]
        self.ij_data = (pdf_x, pdf_y, pdf_z)
    
    def screen_coordinates(self, point: tuple[float, float, float]) -> tuple[float, float]:
        i, j = 0.0, 0.0
        for k in range(3):
            i += point[k] * self.ij_data[k][0]
            j += point[k] * self.ij_data[k][1]
        return (SCREEN_WIDTH // 2 + i * ZOOM, SCREEN_HEIGHT // 2 - j * ZOOM)

def display_face(screen, param: Param, cube: Cube, face: int, corner_placement: callable, cross, square, colors, border_placement: callable):
    box = tuple(param.screen_coordinates(border_placement(x, y)) for x, y in ((0, 0), (3, 0), (3, 3), (0, 3)))
    pygame.draw.polygon(screen, colors["grey"], box, 0)
    pygame.draw.polygon(screen, colors["white"], box, LINE_WIDTH)
    for y, sub in enumerate(cube.faces[face]):
        for x, ele in enumerate(sub):
            corner = corner_placement(x, y)
            if ele == 1:
                for i in range(2):
                    temp = tuple(param.screen_coordinates(add_points(corner, point)) for point in cross[i])
                    pygame.draw.polygon(screen, colors["red"], temp, LINE_WIDTH)
            elif ele == -1:
                temp = tuple(param.screen_coordinates(add_points(corner, point)) for point in square)
                pygame.draw.polygon(screen, colors["blue"], temp, LINE_WIDTH)
    for i in range(2):
        point0, point1 = param.screen_coordinates(border_placement(1 + i, 0)), param.screen_coordinates(border_placement(1 + i, 3))
        pygame.draw.line(screen, colors["white"], point0, point1, LINE_WIDTH)
    for i in range(2):
        point0, point1 = param.screen_coordinates(border_placement(0, 1 + i)), param.screen_coordinates(border_placement(3, 1 + i))
        pygame.draw.line(screen, colors["white"], point0, point1, LINE_WIDTH)

def add_points(point1, point2):
    assert len(point1) == len(point2)
    return tuple(point1[i] + point2[i] for i in range(len(point1)))

def display_front(screen, param: Param, cube: Cube, faded_color: bool=False):
    colors = FADED_COLORS if faded_color else COLORS
    display_face(screen, param, cube, 0, lambda x, y: (x, 2 - y, 0), TOP_CROSS, TOP_SQUARE, colors, lambda x, y: (x, 3 - y, 0)) # White face
    display_face(screen, param, cube, 1, lambda x, y: (0, 2 - y, 2 - x), LEFT_CROSS, LEFT_SQUARE, colors, lambda x, y: (0, 3 - y, 3 - x)) # Orange face
    display_face(screen, param, cube, 2, lambda x, y: (x, 0, y), RIGHT_CROSS, RIGHT_SQUARE, colors, lambda x, y: (x, 0, y)) # Green face

def display_back(screen, param: Param, cube: Cube, faded_color: bool=False, distance: int=6.5):
    colors = FADED_COLORS if faded_color else COLORS
    display_face(screen, param, cube, 3, lambda x, y: (distance, 2 - y, x), LEFT_CROSS, LEFT_SQUARE, colors, lambda x, y: (distance, 3 - y, x)) # Red face
    display_face(screen, param, cube, 4, lambda x, y: (x, distance, 2 - y), RIGHT_CROSS, RIGHT_SQUARE, colors, lambda x, y: (x, distance, 3 - y)) # Blue face
    display_face(screen, param, cube, 5, lambda x, y: (2 - x, 2 - y, distance), TOP_CROSS, TOP_SQUARE, colors, lambda x, y: (3 - x, 3 - y, distance)) # Yellow face


if __name__ == "__main__":
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # Setup
    param = Param()
    temp = time.time()
    cube = Cube()
    cube.aleatoire()
    print(cube)
    print(cube.terminal_state())
    reverse_display = False

    player = 1

    # Main loop
    while True:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in KEY_MAP:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        cube.string_to_move(KEY_MAP[event.key] + "'", player, False)
                    else:
                        cube.string_to_move(KEY_MAP[event.key], player, False)
                    print(cube.terminal_state())
                    player *= -1
                elif event.key in KEY_NUM:
                    cube.jouer(event.key - 31, player)
                    player *= -1
                    print(cube.terminal_state())
                elif event.key == pygame.K_SPACE:
                    reverse_display = not reverse_display

        # Fill the screen with black
        screen.fill(BLACK)
        
        # Display
        if reverse_display:
            display_front(screen, param, cube, True)
            display_back(screen, param, cube, False)
        else:
            display_back(screen, param, cube, True)
            display_front(screen, param, cube, False)
        
        # Update the display
        pygame.display.flip()
        
        clock.tick(60)