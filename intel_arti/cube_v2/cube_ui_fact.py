import math
import pygame, sys, os, pyautogui
from random import choice
import time
from pygame import Vector2, SurfaceType, Vector3
from agent import Agent
from tensorflow.keras.models import load_model #type: ignore
from cube import Cube
from generators import GameSaver
from cube_ui import *

def cinematique_debut_cube(screen: SurfaceType, clock,
                           cube_length: int = SCREEN_HEIGHT * math.pi,
                           camera_distance: float = 10.0,
                           time_length: float = 3.0,
                           number_of_rotations: float = 1.5) -> None | CubeUI :
    """Cinématique de lancement qui fait tourner le cube (c'est joli)"""
    frame_speed = lambda x: (2 * x - x ** 2) * 2 * math.pi * number_of_rotations - 1 * math.pi / 3
    frame_distance = lambda x: lerp2(10 * camera_distance, camera_distance, x)
    camera = Camera(latitude=math.radians(30), longitude=2 * math.pi / 3, distance=camera_distance)
    renderer = Renderer(screen_data=Vector2(SCREEN_WIDTH, SCREEN_HEIGHT), camera=camera)
    cube = Cube()
    cube_ui = CubeUI(cube=cube, renderer=renderer, side_length=cube_length)
    start_time = time.time()
    last_time = time.time()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
        pourcentage_time = (last_time - start_time) / time_length
        if pourcentage_time >= 1:
            camera.longitude = 2 * math.pi / 3
            camera.latitude = math.pi / 6
            camera.reset_position()
            renderer.reset()
            cube_ui.reset_info()
            break

        camera.longitude = frame_speed(pourcentage_time)
        camera.distance = frame_distance(pourcentage_time)
        camera.reset_position()
        renderer.reset()
        cube_ui.reset_info()

        screen.fill(BLACK)
        cube_ui.draw(screen, Vector2(pygame.mouse.get_pos()), False)
        pygame.display.flip()

        clock.tick(60)
        last_time = time.time()
    camera.distance = camera_distance

    return cube_ui

class PartieIA :
    def __init__(self) :
        self.player = 1
        self.ia_player = choice((-1, 1))
        self.coup_interdit = -1
        self.fini = False


class EnvCube :
    def __init__(self, screen : SurfaceType):
        self.screen = screen
        self.partie = PartieIA()
        lenght = SCREEN_HEIGHT * math.pi
        self.cube_ui = cinematique_debut_cube(screen, clock, lenght)
        if self.cube_ui is None:
            sys.exit()
        self.mouse_click = [0, 0]
        self.prev_mouse_x, self.prev_mouse_y = pygame.mouse.get_pos()
        self.agent = Agent(True)
        self.agent.model = load_model(MODEL_PATH)
        self.saver = GameSaver()


    def step(self) :
        if not self.partie.fini and self.partie.player == self.partie.ia_player :
            action = self.agent.choisir(self.cube_ui.cube, self.partie.player, self.partie.coup_interdit)
            self.cube_ui.cube.jouer(action, self.partie.player)
            self.partie.player *= -1
            if action < 18 :
                if action < 9 :
                    self.partie.coup_interdit = action + 9
                else :
                    self.partie.coup_interdit = action - 9
            else :
                self.partie.coup_interdit = -1
            self.saver.save(self.cube_ui.cube.get_flatten_state())
            print("step was saved")
            if self.cube_ui.cube.terminal_state()[0]:
                self.partie.fini = True
                self.saver.save_game()
        show_visible_face = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN :
                if event.key == pygame.K_RETURN :
                    show_visible_face = True
                elif event.key == pygame.K_r :
                    self.cube_ui.cube.reset()
                    self.partie.fini = False
                    self.partie.player = 1
                    self.partie.ia_player = choice((1, -1))
                elif event.key == pygame.K_p :
                    self.cube_ui.renderer.camera.longitude = 0
                    self.cube_ui.renderer.camera.latitude = 0
                    self.cube_ui.renderer.reset()
                    self.cube_ui.reset_info()
                elif event.key == pygame.K_c :
                    self.cube_ui.cube.aleatoire()

        # Mouse detections
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        # Update mouse clicks
        for index in range(2):
            if mouse_buttons[2 * index]:
                self.mouse_click[index] += 1
            else:
                self.mouse_click[index] = 0

        # Check if the right mouse button is pressed
        if self.mouse_click[1] != 0:  # Right click is held down
            current_mouse_x, current_mouse_y = mouse_pos
            delta_x = (self.prev_mouse_x - current_mouse_x) * self.cube_ui.renderer.camera.orientation
            delta_y =  self.prev_mouse_y - current_mouse_y
            self.prev_mouse_x, self.prev_mouse_y = current_mouse_x, current_mouse_y

            self.cube_ui.renderer.camera.update_camera_from_mouse(delta_x, delta_y)
            self.cube_ui.renderer.reset()
            self.cube_ui.reset_info()
        else:
            self.prev_mouse_x, self.prev_mouse_y = mouse_pos
        change = False
        if self.cube_ui.events_listener.button_clicked != (-1, -1) and not self.partie.fini :
            i, j = self.cube_ui.events_listener.button_clicked
            pion_string = "cross" if self.partie.player == 1 else "circle"
            if self.cube_ui.cube.get_pion((0, j, i)) != 0:
                print(f"Can't place a {pion_string} there")
            else:
                print(f"A {pion_string} got placed at coordinates {(i, j)}")
                self.cube_ui.cube.set_pion((0, j, i), self.partie.player)
                self.cube_ui.conseil.desactivate()
                self.partie.player *= -1
                self.partie.coup_interdit = -1
                change = True
        elif (rotation := self.cube_ui.events_listener.turn_button_pressed) != -1 and not self.partie.fini:
            actual_rotation = ROTATION_TRANSLATOR[rotation]
            if actual_rotation == self.partie.coup_interdit :
                print("Il s'agit d'un coup interdit. L'action a été annulée.")
            else :
                self.cube_ui.cube.jouer_tourner(actual_rotation)
                self.cube_ui.conseil.desactivate()
                print(f"Le joueur a décidé de tourner {actual_rotation} (originalement indice {rotation})")
                self.partie.player *= -1
                if actual_rotation < 18 :
                    if actual_rotation < 9 :
                        self.partie.coup_interdit = actual_rotation + 9
                    else :
                        self.partie.coup_interdit = actual_rotation - 9
                change = True
        if change :
            self.saver.save(self.cube_ui.cube.get_flatten_state())
            print("step was saved")
            if self.cube_ui.cube.terminal_state()[0]:
                self.partie.fini = True
                self.saver.save_game()

        # Fill the screen with black
        self.screen.fill(BLACK)

        # Draw the cube
        faces = self.cube_ui.draw(self.screen, Vector2(mouse_pos), self.mouse_click[0] == 1)

        if show_visible_face:
            print(self.cube_ui.cube)
            print([index for index in faces])



def go_position_initial(nb_frame : int = 120) :
    """fonction du bouton 'affichage base' qui replace le cube dans sa position initiale."""
    if camera.longitude == 2 * math.pi / 3 and camera.latitude == math.pi / 6 :
        return
    longitude_actuelle = cube_ui.renderer.camera.longitude
    latitude_actuelle = cube_ui.renderer.camera.latitude
    longitude_finale = 2 * math.pi / 3
    latitude_finale = math.pi / 6
    if longitude_actuelle > math.pi + longitude_finale :
        step_x = (longitude_finale + 2 * math.pi - longitude_actuelle) / nb_frame
    else :
        step_x = (longitude_finale - longitude_actuelle) / nb_frame
    step_y = (latitude_finale - latitude_actuelle) / nb_frame
    for i in range(nb_frame) :
        if i != nb_frame - 1 :
            coeff = 2 * (nb_frame - i) / nb_frame
            cube_ui.renderer.camera.longitude += step_x * coeff
            cube_ui.renderer.camera.latitude += step_y * coeff
        else :
            cube_ui.renderer.camera.longitude = longitude_finale
            cube_ui.renderer.camera.latitude = latitude_finale
        renderer.reset()
        cube_ui.reset_info(renderer)
        # Fill the screen with black
        screen.fill(BLACK)

        # Draw the cube
        cube_ui.draw(screen, Vector2(mouse_pos), False)
        pygame.display.flip()
        clock.tick(60)
    camera.reset_position()
    renderer.reset()
    cube_ui.reset_info(renderer)

def give_advise(agent : Agent, cube : Cube) :
    """fonction du bouton 'conseil' qui affiche les conseils de l'IA au joueur"""
    action = agent.choisir(cube, ia_player * -1, coup_interdit)
    print("Coup conseillé :", action)
    if 0 not in faces or 1 not in faces or not cube_ui.faces[1].proportion_suffisante():
        go_position_initial()
    cube_ui.conseil.activate(action)


if __name__ == "__main__" :
    running = True
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    env = EnvCube(screen)
    while running :
        env.step()
        pygame.display.flip()
        clock.tick(60)