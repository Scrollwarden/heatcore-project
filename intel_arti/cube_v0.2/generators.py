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
    - randomize()
    - generate_state()
    '''
    def __init__(self):
        self.cube = Cube()
        self.randomize()

    def randomize(self):
        """
        Remplit aléatoirement le cube, de sorte que l'agent ne prête aucune attention aux cases qui ne forment pas de victoire.
        """
        self.cube.aleatoire()
        self._SaD_random_wins()

    def generate_state(self):
        """
        Génère un état où le jeu est gagné par l'agent.
        Cette methode est un générateur qui fonctionne avec yield.
        """
        for face in range(6):
            for line_win in self._win_on_line(face):
                yield line_win
            for column_win in self._win_on_column(face):
                yield column_win
            for diagonal_win in self._win_on_diagonal(face):
                yield diagonal_win
        # TODO : any importances having many yield instead of one at the end ?

    def _SaD_random_wins(self):
        """
        Seek and Destroy random wins. Sert à enlever les victoires générées aléatoirement.
        Pas sûr que la methode soit nécessaire.
        """
        pass

    def _win_on_line(self, face):
        """
        Génère un état où le jeu est gagné par l'agent sur une ligne.
        Cette methode est un générateur qui fonctionne avec yield.
        Cette methode est interne à GeneratorWinState et ne devrait pas être utilisée directement.

        INPUTS
        - face (int) : la face sur laquelle on veut générer une victoire
        """
        for line in range(3):
            situation = deepcopy(self.cube)
            situation.set_ligne(face, line, array([1, 1, 1]))
            yield situation

    def _win_on_column(self, face):
        """
        Génère un état où le jeu est gagné par l'agent sur une colonne.
        Cette methode est un générateur qui fonctionne avec yield.
        Cette methode est interne à GeneratorWinState et ne devrait pas être utilisée directement.

        INPUTS
        - face (int) : la face sur laquelle on veut générer une victoire
        """
        for column in range(3):
            situation = deepcopy(self.cube)
            situation.set_ligne(face, column, array([1, 1, 1]))
            yield situation

    def _win_on_diagonal(self, face):
        """
        Génère un état où le jeu est gagné par l'agent sur une diagonale.
        Cette methode est un générateur qui fonctionne avec yield.
        Cette methode est interne à GeneratorWinState et ne devrait pas être utilisée directement.

        INPUTS
        - face (int) : la face sur laquelle on veut générer une victoire
        """
        situation = deepcopy(self.cube)
        for line, case in ((0, 0), (1, 1), (2, 2)):
            situation.set_pion((face, line, case), 1)
        yield situation
        for line, case in ((0, 2), (1, 1), (2, 0)):
            situation.set_pion((face, line, case), 1)
        yield situation




# # tests
# generator = GeneratorWinState()
# list_situations = []
# for win_situation in generator.generate_state():
#     list_situations.append(win_situation)
# print(len(list_situations), f'for {6*(3+3+2)} expected')