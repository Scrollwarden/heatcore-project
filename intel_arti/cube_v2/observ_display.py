import pygame, sys
import time
from agent import Agent
from tensorflow.keras.models import load_model #type: ignore
from parameters import changes_model, date_model

# Screen constants
LINE_WIDTH = 3
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500
ZOOM = 3
# Model constants
NUM_MODEL = 4
MODEL_PATH = f"cube_v2/models/model{NUM_MODEL}.h5"
# linux (depuis la racine de Matthew) : "cube_v2/models/model{NUM_MODEL}.h5"
# window (depuis la racine de Lou) : "models\\model{NUM_MODEL}.h5"
NOMBRE_NEURONES = 200 if NUM_MODEL <= 7 else 400

# Colors
BLACK = (0, 0, 0)
GREY = (200, 200, 200)
WHITE = (255, 255, 255)

agent = Agent(True)
agent.model = load_model(MODEL_PATH)
model_weights, bias = agent.model.layers[0].get_weights()
output_weights, out_bias = agent.model.layers[1].get_weights()
num_neurone = 0
neurone_weights = model_weights[:, num_neurone]

def weights_color(weights : list[float]) :
    maxi = max(weights)
    mini = min(weights)
    ref = max(abs(maxi), abs(mini))
    couleurs = []
    for w in weights :
        if w > 0 :
            couleurs.append((int(255*(w/ref)), 0, 0))
        elif w < 0 :
            w = -w
            couleurs.append((0, 0, int(255*(w/ref))))
        else :
            couleurs.append(GREY)
    return couleurs


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

def display_face(screen, param: Param, face: int, border_placement: callable, colors : list):
    box = tuple(param.screen_coordinates(border_placement(x, y)) for x, y in ((0, 0), (3, 0), (3, 3), (0, 3)))
    for y in range(3) :
        for x in range(3):
            corners = tuple(param.screen_coordinates(border_placement(i, j)) for i, j in ((x, y), (x+1, y), (x+1, y+1), (x, y+1)))
            pygame.draw.polygon(screen, colors[y*3+x], corners, 0)
    for i in range(2):
        point0, point1 = param.screen_coordinates(border_placement(1 + i, 0)), param.screen_coordinates(border_placement(1 + i, 3))
        pygame.draw.line(screen, WHITE, point0, point1, LINE_WIDTH)
    for i in range(2):
        point0, point1 = param.screen_coordinates(border_placement(0, 1 + i)), param.screen_coordinates(border_placement(3, 1 + i))
        pygame.draw.line(screen, WHITE, point0, point1, LINE_WIDTH)
    pygame.draw.polygon(screen, WHITE, box, LINE_WIDTH)

def add_points(point1, point2):
    assert len(point1) == len(point2)
    return tuple(point1[i] + point2[i] for i in range(len(point1)))

def display_front(screen, param: Param):
    distance = 6.5
    colors = weights_color(neurone_weights)
    display_face(screen, param, 0, lambda x, y: (x, 3 - y, 0), colors[:9])
    display_face(screen, param, 2, lambda x, y: (0, 3 - y, 3 - x), colors[18:27])
    display_face(screen, param, 1, lambda x, y: (x, 0, y), colors[9:18])
    display_face(screen, param, 4, lambda x, y: (distance, 3 - y, x), colors[36:45])
    display_face(screen, param, 3, lambda x, y: (x, distance, 3 - y), colors[27:36])
    display_face(screen, param, 5, lambda x, y: (3 - x, 3 - y, distance), colors[45:])


if __name__ == "__main__":
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # Setup
    param = Param()
    temp = time.time()

    # infos
    font_for_text = pygame.font.Font(None, 36)
    font_for_infos = pygame.font.Font(None, 20)
    text_model_used = font_for_text.render(f"Model : {NUM_MODEL}", True, WHITE)
    text_date_model = font_for_infos.render(f"Date of creation : {date_model(NUM_MODEL)}", True, WHITE)
    text_changes_model = font_for_infos.render(f"M{NUM_MODEL-1} vs M{NUM_MODEL} : {changes_model(NUM_MODEL)}", True, WHITE)

    # Main loop
    while True:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT :
                    num_neurone = (num_neurone+1) % NOMBRE_NEURONES
                    neurone_weights = model_weights[:, num_neurone]
                elif event.key == pygame.K_LEFT :
                    num_neurone = (num_neurone-1) % NOMBRE_NEURONES
                    neurone_weights = model_weights[:, num_neurone]

        # Fill the screen with black
        screen.fill(BLACK)
        
        # Display
        display_front(screen, param)
        screen.blit(text_model_used, (10, 10))
        screen.blit(text_date_model, (10, 40))
        screen.blit(text_changes_model, (10, 60))
        text_num_neurone = font_for_text.render(f"Neurone {num_neurone}", True, WHITE)
        text_biais_neurone = font_for_infos.render(f"Biais : {str(bias[num_neurone])[:10]}", True, WHITE)
        text_wieght_neurone = font_for_infos.render(f"Poids de sortie : {str(output_weights[num_neurone][0])[:10]}", True, WHITE)
        screen.blit(text_num_neurone, (10, 100))
        screen.blit(text_biais_neurone, (10, 130))
        screen.blit(text_wieght_neurone, (10, 150))
        # Update the display
        pygame.display.flip()
        
        clock.tick(60)