'''
Tous les générateurs de situations de jeu pour entrainer l'agent.
'''

from cube import Cube
from copy import deepcopy
from numpy import array

class GeneratorWinState:
    '''
    Génère des situations où le jeu est gagné par l'agent.

    METHODES
    - generate_state()
    '''
    def __init__(self):
        self.cube = Cube()

    def generate_state(self, times=1):
        """
        Génère un état où le jeu est gagné par l'agent.
        Cette methode est un générateur qui fonctionne avec yield.

        INPUT
        - times (int) : le nombre de fois où chaque situation sera générée
        avec le reste des cases définies aléatoirement (1 par défaut)
        """
        for face in range(6):
            for line_win in self._win_on_line(face, times):
                yield line_win
            for column_win in self._win_on_column(face, times):
                yield column_win
            for diagonal_win in self._win_on_diagonal(face, times):
                yield diagonal_win
        # TODO : any importances having many yield instead of one at the end ?

    def win_on_line(self, face, times=1):
        """
        Génère un état où le jeu est gagné par l'agent sur une ligne.
        Cette methode est un générateur qui fonctionne avec yield.

        INPUTS
        - face (int) : la face sur laquelle on veut générer une victoire
        - times (int) : le nombre de fois où la même génération sera générée (par défaut 1)
        """
        for _ in range(times):
            for line in range(3):
                situation = deepcopy(self.cube)
                situation.aleatoire()
                situation.set_ligne(face, line, array([1, 1, 1]))
                yield situation

    def win_on_column(self, face, times=1):
        """
        Génère un état où le jeu est gagné par l'agent sur une colonne.
        Cette methode est un générateur qui fonctionne avec yield.

        INPUTS
        - face (int) : la face sur laquelle on veut générer une victoire
        - times (int) : le nombre de fois où la même génération sera générée (par défaut 1)
        """
        for _ in range(times):
            for column in range(3):
                situation = deepcopy(self.cube)
                situation.aleatoire()
                situation.set_ligne(face, column, array([1, 1, 1]))
                yield situation

    def win_on_diagonal(self, face, times=1):
        """
        Génère un état où le jeu est gagné par l'agent sur une diagonale.
        Cette methode est un générateur qui fonctionne avec yield.

        INPUTS
        - face (int) : la face sur laquelle on veut générer une victoire
        - times (int) : le nombre de fois où la même génération sera générée (par défaut 1)
        """
        # PS : c'est pas beau ici, j'aime pas les deux yield en cas-par-cas

        # première diagonale
        for _ in range(times):
            situation = deepcopy(self.cube)
            situation.aleatoire()
            for line, case in ((0, 0), (1, 1), (2, 2)):
                situation.set_pion((face, line, case), 1)
            yield situation
        # on recommence pour la diagonale inversée
        for _ in range(times):
            situation = deepcopy(self.cube)
            situation.aleatoire()
            for line, case in ((0, 2), (1, 1), (2, 0)):
                situation.set_pion((face, line, case), 1)
            yield situation




# # tests
# generator = GeneratorWinState()
# list_situations = []
# for win_situation in generator.generate_state():
#     list_situations.append(win_situation)
# print(len(list_situations), f'for {6*(3+3+2)} expected')