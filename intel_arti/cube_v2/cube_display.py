import pygame, sys
import time
from cube import Cube
from agent import Agent
from tensorflow.keras.models import load_model #type: ignore
from generators import GameSaver

# Screen constants
LINE_WIDTH = 3
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500
ZOOM = 3
NUM_MODEL = 4
MODEL_PATH = f"cube_v2/models/model{NUM_MODEL}.h5"
# linux (depuis la racine de Matthew) : "cube_v2/models/model{NUM_MODEL}.h5"
# window (depuis la racine de Lou) : "models\\model{NUM_MODEL}.h5"
DATE_ALL_MODELS = {
    1: '~ 21-11-2024',
    2: '~ 21-11-2024',
    3: '~ 21-11-1014',
    4: '~ 26-11-2024',
    5: '~ 26-11-2024',
    6: '~ 26-11-2024',
    7: '~ 26-11-2024'
}
DATE_MODEL = DATE_ALL_MODELS[NUM_MODEL]

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

# Key                Explications par rapport à la vue du joueur et la face du dessus comme référenciel
KEY_MAP = {#         EXPLICATIONS FAUSSES, A REVERIFIER
    pygame.K_r: "R", # - Tourne la face directe droite
    pygame.K_l: "L", # - Tourne la face indirecte gauche
    pygame.K_f: "F", # - Tourne la face directe gauche
    pygame.K_b: "B", # - Tourne la face indirecte droite
    pygame.K_u: "U", # - Tourne la couronne du haut
    pygame.K_d: "D", # - Tourne la couronne du bas
    pygame.K_m: "M", # - Tourne la rangée du milieu de la face directe gauche
    pygame.K_e: "E", # - Tourne la tranche du milieu
    pygame.K_s: "S", # - Tourne la rangée du milieu de la face directe droite
}

KEY_NUM = (
    pygame.K_1, # - Pion en bas de la rangée gauche
    pygame.K_2, # - Pion au milieu de la rangée gauche
    pygame.K_3, # - Pion en haut de la rangée gauche
    pygame.K_4, # - Pion en bas de la rangée milieu
    pygame.K_5, # - Pion au milieu de la rangée milieu
    pygame.K_6, # - Pion en haut de la rangée milieu
    pygame.K_7, # - Pion en bas de la rangée droite
    pygame.K_8, # - Pion au milieu de la rangée droite
    pygame.K_9 # - Pion en haut de la rangée droite
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
    for y, sub in enumerate(cube.get_face(face)) :
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
    display_face(screen, param, cube, 2, lambda x, y: (0, 2 - y, 2 - x), LEFT_CROSS, LEFT_SQUARE, colors, lambda x, y: (0, 3 - y, 3 - x)) # Orange face
    display_face(screen, param, cube, 1, lambda x, y: (x, 0, y), RIGHT_CROSS, RIGHT_SQUARE, colors, lambda x, y: (x, 0, y)) # Green face

def display_back(screen, param: Param, cube: Cube, faded_color: bool=False, distance: int=6.5):
    colors = FADED_COLORS if faded_color else COLORS
    display_face(screen, param, cube, 4, lambda x, y: (distance, 2 - y, x), LEFT_CROSS, LEFT_SQUARE, colors, lambda x, y: (distance, 3 - y, x)) # Red face
    display_face(screen, param, cube, 3, lambda x, y: (x, distance, 2 - y), RIGHT_CROSS, RIGHT_SQUARE, colors, lambda x, y: (x, distance, 3 - y)) # Blue face
    display_face(screen, param, cube, 5, lambda x, y: (2 - x, 2 - y, distance), TOP_CROSS, TOP_SQUARE, colors, lambda x, y: (3 - x, 3 - y, distance)) # Yellow face


if __name__ == "__main__":
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # Setup
    agent = Agent(True)
    agent.model = load_model(MODEL_PATH)
    param = Param()
    temp = time.time()
    cube = Cube()
    reverse_display = False
    saver = GameSaver()
    # files = []
    # for i in range(8):
    #     files.append(f'cube_v2/data_from_human_games/game_m4_vs_human/game_m4_vs_human_game{i}.npz')
    # saver.load_all_from_files(*files)

    player = 1
    coup_interdit = -1
    action = 50
    winner = (False, 0)
    font_for_text = pygame.font.Font(None, 36)
    font_for_infos = pygame.font.Font(None, 20)
    text_model_used = font_for_text.render(f"Model : {NUM_MODEL}", True, (255, 255, 255))
    text_date_model = font_for_infos.render(f"Date of creation : ({DATE_MODEL})", True, (255, 255, 255))
    
    # Main loop
    while True:
        if not winner[0] and player == 1 :
            action = agent.choisir(cube, player, coup_interdit)
            cube.jouer(action, player)
            player *= -1
            winner = cube.terminal_state()
            print(winner)
            print(cube)
            # sauvegarde de la partie dans saver
            saver.save(cube.get_flatten_state())
            print("step was saved")
            if cube.terminal_state()[0]:
                saver.save_game('current')
        if action < 18 :
            if action < 9 :
                coup_interdit = action + 9
            else :
                coup_interdit = action - 9
        else :
            coup_interdit = -1
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                saver.save_all_to_files(f'game_m{NUM_MODEL}_vs_human')
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in KEY_MAP:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        action = cube.string_to_move(KEY_MAP[event.key] + "'", player, False)
                    else:
                        action = cube.string_to_move(KEY_MAP[event.key], player, False)
                    if action in cube.actions_possibles(coup_interdit) :
                        print(f"WARNING !!! Coup interdit joué par le joueur{player}")
                    if action < 18 :
                        if action < 9 :
                            coup_interdit = action + 9
                        else :
                            coup_interdit = action - 9
                    else :
                        coup_interdit = -1
                    winner = cube.terminal_state()
                    print(winner)
                    print(cube)
                    # sauvegarde de la partie dans saver
                    saver.save(cube.get_flatten_state())
                    print("step was saved")
                    if cube.terminal_state()[0]:
                        saver.save_game()
                    player *= -1
                elif event.key in KEY_NUM:
                    action = event.key - 31
                    cube.jouer(action, player)
                    if action in cube.actions_possibles(coup_interdit) :
                        print(f"WARNING !!! Coup interdit joué par le joueur{player}")
                    if action < 18 :
                        if action < 9 :
                            coup_interdit = action + 9
                        else :
                            coup_interdit = action - 9
                    else :
                        coup_interdit = -1
                    player *= -1
                    winner = cube.terminal_state()
                    print(winner)
                    print(cube)
                    # sauvegarde de la partie dans saver
                    saver.save(cube.get_flatten_state())
                    print("step was saved")
                    if cube.terminal_state()[0]:
                        saver.save_game()
                elif event.key == pygame.K_SPACE:
                    reverse_display = not reverse_display
                elif event.key == pygame.K_p :
                    cube.reset()
                    player = 1
                    coup_interdit = -1

        # Fill the screen with black
        screen.fill(BLACK)
        
        # Display
        if reverse_display:
            display_front(screen, param, cube, True)
            display_back(screen, param, cube, False)
        else:
            display_back(screen, param, cube, True)
            display_front(screen, param, cube, False)
        screen.blit(text_model_used, (10, 10))
        screen.blit(text_date_model, (10, 40))
        text_saved_games = font_for_infos.render(f"Saved games : {saver.get_all_games()}", True, (255, 255, 255))
        screen.blit(text_saved_games, (10, 450))
        # Update the display
        pygame.display.flip()
        
        clock.tick(60)