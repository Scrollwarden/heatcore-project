'''
Tous les générateurs de situations de jeu pour entrainer l'agent.
'''

from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from random import randint, choice
from cube import Cube, check_type
from numpy import zeros, ndarray, append, array
from time import time


class GeneratorWinState:
    '''
    Génère des situations où le jeu est gagné par l'agent.

    METHODES
    - generate_all_states()
    - generate_random_states()
    - get_n_states()
    '''
    def __init__(self):
        self.cube = Cube()
        self.liste_win_state = []

    def generate_all_states(self, times=1):
        """
        Génère une liste de toutes les situations où le jeu est gagné par l'agent.

        INPUT
        - times (int) : le nombre de fois où chaque situation sera générée
        avec le reste des cases définies aléatoirement (1 par défaut)
        """
        self.liste_win_state = []
        for face in range(6):
            self._win_on_line(face, times),
            self._win_on_column(face, times),
            self._win_on_diagonal(face, times)

    def generate_random_states(self, n=1):
        """
        Génère une liste de situations où le jeu est gagné par l'agent.
        Ces situations sont choisies aléatoirement
        
        INPUT
        - n (int) : le nombre d'états a générer
        """
        self.liste_win_state = []
        for _ in range(n):
            face = randint(0, 5)
            situation_type = randint(0, 2)
            if situation_type == 0:
                self._win_on_line(face)
            elif situation_type == 1:
                self._win_on_column(face)
            else:
                self._win_on_diagonal(face)
        return self.liste_win_state

    def get_n_states(self, n=None):
        """
        génère n situations où l'agent a gagné.
        Cette méthode est un générateur yield.
        """
        for _ in range(n):
            i = randint(0, len(self.liste_win_state)-1)
            yield self.liste_win_state[i]

    def _randomize_cube(self):
        """
        Pose aléatoirement des pions sur le cube.
        Enpose moins que la méthode .aleatoire du cube.
        """
        self.cube.reset()
        for _ in range(randint(10, 20)):
            self.cube.set_pion((randint(0, 5), randint(0, 2), randint(0, 2)), choice((-1, 1)))
        
    def _win_on_line(self, face, times=1):
        """
        Génère un état où le jeu est gagné par l'agent sur une ligne.

        INPUTS
        - face (int) : la face sur laquelle on veut générer une victoire
        - times (int) : le nombre de fois où la même génération sera générée (par défaut 1)
        """
        for _ in range(times):
            line = times%3
            self._randomize_cube()
            situation = deepcopy(self.cube)
            situation.set_ligne(face, line, array([1, 1, 1]))
            self.liste_win_state.append(situation)

    def _win_on_column(self, face, times=1):
        """
        Génère un état où le jeu est gagné par l'agent sur une colonne.

        INPUTS
        - face (int) : la face sur laquelle on veut générer une victoire
        - times (int) : le nombre de fois où la même génération sera générée (par défaut 1)
        """
        for _ in range(times):
            column = times%3
            self._randomize_cube()
            situation = deepcopy(self.cube)
            situation.set_ligne(face, column, array([1, 1, 1]))
            self.liste_win_state.append(situation)

    def _win_on_diagonal(self, face, times=1):
        """
        Génère un état où le jeu est gagné par l'agent sur une diagonale.

        INPUTS
        - face (int) : la face sur laquelle on veut générer une victoire
        - times (int) : le nombre de fois où la même génération sera générée (par défaut 1)
        """
        # première diagonale
        for _ in range(times):
            if times % 2 == 0:
                self._randomize_cube()
                situation = deepcopy(self.cube)
                for line, case in ((0, 0), (1, 1), (2, 2)):
                    situation.set_pion((face, line, case), 1)
                self.liste_win_state.append(situation)
            # on recommence pour la diagonale inversée
            else:
                self._randomize_cube()
                situation = deepcopy(self.cube)
                for line, case in ((0, 2), (1, 1), (2, 0)):
                    situation.set_pion((face, line, case), 1)
                self.liste_win_state.append(situation)


# WORKING ON
# ----------
# class GeneratorWinType:
#     '''
#     Génère un seul type de situation où l'agent est gagant.

#     METHODS
#     - generate_state_line()
#     - generate_state_column()
#     - generate_state_diagonal()
#     '''
#     def __init__(self):
#         pass

class GeneratorPartie:
    def __init__(self, do : bool = False) :
        """Initialise une partie."""
        self.joueur = 1
        self.coup_interdit = -1
        self.cube = Cube()
        self.scratch_cube = Cube()
        if do :
            self.wise_random_partie()
            self.eval_states()
    
    @check_type(True, int)
    def is_allowed(self, action : int) :
        """Renvoie si l'action souhaitée est autorisée dans l'état actuel du cube.
        
        Param
        -----
            action (int) : L'action désirée
        """
        actions_possibles = self.cube.actions_possibles(self.coup_interdit)
        return action in actions_possibles
    
    @check_type(True, int, bool, bool)
    def step(self, action : int, force : bool = False, on_scratch : bool = False) :
        """Joue une étape de la partie.
        
        Params
        -------
            action (int) : L'action désirée
            force (bool, optional) : Permet de forcer le coup à être jouer même s'il n'est pas autorisé.
                                     Peut aussi être utilisé lorsque l'on est certain que le coup est légal
                                     pour éviter de faire des tests inutiles
            on_scratch (bool, optional) : Si True, l'étape ne sera pas appliquée au cube mais au scratch_cube
        """
        if force or self.is_allowed(action) :
            if on_scratch :
                self.scratch_cube.jouer(action, self.joueur)
            else :
                self.cube.jouer(action, self.joueur)
                self.joueur *= -1
                if action < 18 :
                    self.coup_interdit = (action + 9) % 18
                else :
                    self.coup_interdit = -1
        else :
            print("Action non autorisée :", action)
    
    def random_step(self) -> None:
        """Joue un coup aléatoirement."""
        actions_possibles = self.cube.actions_possibles(self.coup_interdit)
        action = choice(actions_possibles)
        self.step(action, True)
        return self.cube.get_state() * (self.joueur * -1)
    
    def wise_random_step(self) -> ndarray :
        """Joue un coup aléatoirement tout en assurant de changer l'état du cube."""
        actions_possibles = self.cube.actions_possibles(self.coup_interdit)
        action = choice(actions_possibles)
        if self.cube != self.scratch_cube :
            # réinitialise le scratch cube à l'état actuel du cube
            self.scratch_cube.set_state(self.cube.grille, True)
        self.step(action, True, True)
        while action < 18 and self.cube == self.scratch_cube :
            actions_possibles.remove(action)
            action = choice(actions_possibles)
            if action < 18 :
                self.step(action, True, True)
        self.step(action, True)
        return self.cube.get_state() * (self.joueur * -1)
    
    def random_partie(self) :
        states = []
        while not (gagnant := self.cube.terminal_state())[0] :
            states.append(self.random_step())
        self.gagnant = gagnant[1]
        self.states = states
    
    def wise_random_partie(self) :
        states = []
        while not (gagnant := self.cube.terminal_state())[0] :
            states.append(self.wise_random_step())
        self.gagnant = gagnant[1]
        self.states = states
    
    def eval_states(self) :
        self.rewards = zeros((len(self.states), 1))
        if self.gagnant == 1 : # Le joueur 1 a gagné
            for i in range(0, len(self.states), 2) :
                self.rewards[i, 0] = 1/(1<<(len(self.states)-i)//2)
            for i in range(1, len(self.states), 2) :
                self.rewards[i, 0] = -1/(1<<(len(self.states)-i-1)//2)
        elif self.gagnant == -1 : # Le joueur -1 (ou 2) a gagné
            for i in range(1, len(self.states), 2) :
                self.rewards[i, 0] = 1/(1<<(len(self.states)-i)//2)
            for i in range(0, len(self.states), 2) :
                self.rewards[i, 0] = -1/(1<<(len(self.states)-i-1)//2)
        else : # Egalite
            pass
    
    def step_by_step(self) :
        states = []
        while not (gagnant := self.cube.terminal_state())[0] :
            state = self.random_step()
            print(self.joueur*-1, state)
            states.append(state)
            input()
        self.gagnant = gagnant[1]
        self.states = states
    
    def get_data(self) :
        return self.states, self.rewards

class DataRubi :
    def __init__(self, n : int) -> None:
        self.x = ndarray((0, 6, 3, 3), int)
        self.y = ndarray((0, 1))
        self.gagnants = [0, 0, 0]
        self.add_data(n)
    
    def add_data(self, n : int) :
        for _ in range(n) :
            partie = GeneratorPartie(True)
            new_x, new_y = partie.get_data()
            self.x = append(self.x, new_x, 0)
            self.y = append(self.y, new_y, 0)
            if partie.gagnant == 1 :
                self.gagnants[0] += 1
            elif partie.gagnant == -1 :
                self.gagnants[1] += 1
            else :
                self.gagnants[2] += 1
    
    def reset(self) :
        self.x = ndarray((0, 3, 3, 1), int)
        self.y = ndarray((0, 1))

    def get_datas(self) :
        return self.x, self.y

def generator_datas(batch_size) :
    while True :
        partie = GeneratorPartie(True)
        x, y = partie.get_data()
        return x, y

def play_random_partie(i) :
    """Fonction donnée en thread pour les parties aléatoires"""
    partie = GeneratorPartie()
    partie.random_partie()
    return len(partie.states)

def play_wise_random_partie(i) :
    """Fonction donnée en thread pour les parties aléatoires sans coups inutiles"""
    partie = GeneratorPartie()
    partie.wise_random_partie()
    return len(partie.states)

# if __name__ == "__main__":
#     somme = 0
#     start = time()

#     # mise en threading des fonctions précédentes sur tous les cores 10000 fois.
#     with ProcessPoolExecutor() as executor:
#         results = executor.map(play_random_partie, range(10000))

#     somme = sum(results)

#     print("Temps :", time()-start)
#     print("Somme :", somme)
#     print('---------')
#     somme = 0
#     start = time()

#     with ProcessPoolExecutor() as executor:
#         results = executor.map(play_wise_random_partie, range(10000))
    
#     somme = sum(results)

#     print("Temps :", time()-start)
#     print("Somme :", somme)




# backup 
# ============
# 
# def generate_state(self, times=1):
#         """
#         Génère un état où le jeu est gagné par l'agent.
#         Cette methode est un générateur qui fonctionne avec yield.

#         INPUT
#         - times (int) : le nombre de fois où chaque situation sera générée
#         avec le reste des cases définies aléatoirement (1 par défaut)
#         """
#         for face in range(6):
#             for line_win in self._win_on_line(face, times):
#                 yield line_win
#             for column_win in self._win_on_column(face, times):
#                 yield column_win
#             for diagonal_win in self._win_on_diagonal(face, times):
#                 yield diagonal_win
#         # TODO : instead of yielding each, store and then yeld one of the loop output randomly
