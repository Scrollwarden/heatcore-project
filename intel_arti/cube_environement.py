import numpy as np
from nsi_project import Cube
import pygame
from nsi_project_display import Param, BLACK, display_front, display_back
from copy import deepcopy


class CubeEnv:
    def __init__(self):
        self.cube = Cube()
        self.action_space = 27  # 18 moves + 9 placements
        self.state_space = (6, 3, 3)  # 6 faces, each 3x3 grid
        self.current_player = 1  # 1 for cross, -1 for circle
        
        # Screen variables
        self.screen_width = 800
        self.screen_height = 500
        self.param = Param()
        self.pygame_initialized = False
    
    def init_pygame(self):
        """Juste pour la visualization (visualize.py)"""
        if not self.pygame_initialized:
            # Initialize Pygame
            pygame.init()
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
            self.clock = pygame.time.Clock()
            self.pygame_initialized = True

    def reset(self):
        self.cube.reset_cube()
        self.current_player = 1  # Cross starts
        return self.get_state()

    def step(self, action: int):
        """En fonction de quel neuronne est activé, on fait quelque chose sur le cube

        Args:
            action (int): Le numéro du neurone activé

        Returns:
            tuple: On renvoie
            * L'état du cube après le mouvement
            * La récompense donné après le mouvement
            * Si la partie est fini
        """
        temp_reward = 0
        if action < 18:
            # Handle move actions
            functions = (self.cube.f_move, self.cube.b_move, self.cube.r_move, self.cube.l_move, self.cube.u_move, self.cube.d_move, self.cube.m_move, self.cube.e_move, self.cube.s_move)
            foo = functions[action % 9]
            reverse = action > 9
            cube_before = deepcopy(self.cube.faces)
            foo(reverse)
            temp_reward += -100 if cube_before == self.cube.faces else 0
        else:
            # Handle placement actions
            face = 0
            pos = action - 18
            y, x = divmod(pos, 3)
            self.cube.faces[face][y][x] = self.current_player

        
        state = self.get_state()
        done, reward = self.check_done()
        reward += temp_reward
        self.current_player = -self.current_player  # Switch players
        return state, reward, done
    
    def single_step(self, action : int) :
        """En fonction de quel neuronne est activé, on fait quelque chose sur le cube

        Args:
            action (int): Le numéro du neurone activé

        Returns:
            bool : Si la partie est fini
        """
        if action < 18:
            # Handle move actions
            functions = (self.cube.f_move, self.cube.b_move, self.cube.r_move, self.cube.l_move, self.cube.u_move, self.cube.d_move, self.cube.m_move, self.cube.e_move, self.cube.s_move)
            foo = functions[action % 9]
            reverse = action > 9
            foo(reverse)
        else:
            # Handle placement actions
            face = 0
            pos = action - 18
            y, x = divmod(pos, 3)
            self.cube.faces[face][y][x] = self.current_player

        
        done, reward = self.check_done()
        return done, reward


    def get_reward(self, last_state : list[list[list[int]]], new_state : list[list[list[int]]]) :
        reward = 100 if last_state == new_state else 100
        result = self.cube.terminal_state()
        if result[0] :
            if result[1] == 1 :
                reward += 10_000
            elif result[1] == -1 :
                reward -= 10_000
            else :
                reward -= 50
        return reward


    def get_state(self):
        """L'état du cube actuellement

        Returns:
            np.array: Une liste des inputs à donner à l'IA (les neuronnes du début)
        """
        flattened_faces = np.array(self.cube.faces).flatten()
        state_with_player = flattened_faces * self.current_player
        return state_with_player

    def check_done(self):
        """On regarde si la partie est finie, et la récompense accordée

        Returns:
            _type_: _description_
        """
        terminal, winner = self.cube.terminal_state()
        if terminal:
            if winner == 0:
                return True, -50  # Draw
            elif winner == self.current_player :
                return True, 10000
            else :
                print("Winner :", winner, ", Current player :", self.current_player)
                return True, -10000 # En fonction du joueur
        return False, 0 # ça continue

    def render(self):
        """Juste pour la visualization (visualize.py)"""
        self.init_pygame()
        while True:
            # Handle Pygame events to keep the window responsive
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            # Fill the screen with black
            self.screen.fill(BLACK)

            # Display the cube using the existing display functions
            display_front(self.screen, self.param, self.cube, True)
            display_back(self.screen, self.param, self.cube, False)
            
            # Update the display
            pygame.display.flip()

            # Cap the frame rate
            self.clock.tick(60)