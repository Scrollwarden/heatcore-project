import sys
import pygame
from agent_morpion import AgentMorpion, Choices
from tensorflow.keras.models import load_model #type: ignore

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 400
LINE_WIDTH = 3
BLACK = (0, 0, 0)
GREY = (200, 200, 200)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
NOMBRE_NEURONES = 100
SPACE = 50
MODEL_PATH = f"model_morpion{NOMBRE_NEURONES}.h5"


pygame.init()
FONT = pygame.font.Font(None, 20)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
choix = Choices()
agent = AgentMorpion(choix, -1)
agent.model = load_model(MODEL_PATH)
model_weights, bias = agent.model.layers[1].get_weights()
output_weights, out_bias = agent.model.layers[2].get_weights()
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



def display() :
    screen.fill(BLACK)
    rect = pygame.Rect(SPACE, SPACE, 300, 300)
    pygame.draw.rect(screen, GREY, rect)
    colors = weights_color(neurone_weights)
    for x in range(3) :
        left = SPACE + x*100
        for y in range(3) :
            top = SPACE + y*100
            corners = (
                (left, top),
                (left + 100, top),
                (left + 100, top+100),
                (left, top+100)
            )
            pygame.draw.polygon(screen, colors[y*3+x], corners)
    # Lignes horizontales
    pygame.draw.line(screen, WHITE, (SPACE, 150), (349, 150), LINE_WIDTH)
    pygame.draw.line(screen, WHITE, (SPACE, 250), (349, 250), LINE_WIDTH)
    # Lignes verticales
    pygame.draw.line(screen, WHITE, (150, SPACE), (150, 349), LINE_WIDTH)
    pygame.draw.line(screen, WHITE, (250, SPACE), (250, 349), LINE_WIDTH)
    screen.blit(FONT.render(f"Poids de sortie : {round(output_weights[num_neurone][0], 7)}", True, WHITE), (0, 0))




while True :
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
    display()
    pygame.display.flip()
    clock.tick(10)