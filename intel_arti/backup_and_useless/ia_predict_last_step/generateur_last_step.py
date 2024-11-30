'''
Ce programme génère les situations gagnantes step n du jeu.
Gagnant step 1 signifie qu'il manque 1 coup pour gagner.
    Auteur : Matthew
    Date : 13/10/2024
'''

from numpy import zeros
from copy import deepcopy
import random

CUBE_VIDE = zeros(shape=(6, 3, 3))

class GenerateurSituationsGagnantes:
    '''
    génère des situations gagantes à n pas.
    1 pas signifie qu'il manque 1 coup pour gagner.

    ATTRIBUTS
    - cube (list) : le cube vide
    - liste_situations_gagnees (list) : la liste des situations gagnantes 0 steps

    METHODS
    - randomize()
    - seek_and_destroy_random_win()
    - cree_situation_gagnee()
    - cree_situations_gagnantes_step(n) NOT IMPLEMENTED YET
    '''
    def __init__(self):
        self.cube = CUBE_VIDE
        self.liste_situations_gagnees = []

    def randomize(self):
        """
        remplace tous les slots du cube par un nombre aléatoire en -1 et 1
        (il faut que le modèle sache que les autres cases n'ont pas d'importance)

        On note
        1 : le jeu de l'IA
        0 : une case vide
        -1 : le jeu du joueur
        """
        for face in range(6):
            for ligne in range(3):
                for slot in range(3):
                    self.cube[face, ligne, slot] = random.choice([-1, 0, 1])

    def seek_and_destroy_random_win(self):
        """
        vérifie si le cube randomisé possède une situation gagnée.
        Si c'est le cas, on l'enlève.
        (le mieux serait de la garder et de ne pas faire l'opération lors de la création de situations gagnantes, mais galère)
        """
        for face in range(6):
            # check des lignes
            for ligne in range(3):
                if ligne in ([1, 1, 1], [-1, -1, -1]):
                    self.cube[face, ligne, 1] = -self.cube[face, ligne, 1] # on change le signe au milieu de la formation pour être sûr
            # check des colonnes
            for colonne in range(3):
                if (self.cube[face][0][colonne], self.cube[face][1][colonne], self.cube[face][2][colonne]) in ((1, 1, 1), (-1, -1, -1)):
                    self.cube[face, 1, colonne] = -self.cube[face, 1, colonne] # on change le signe au milieu de la formation pour être sûr
            # check des diagonales
            if (self.cube[face, 0, 0], self.cube[face, 1, 1], self.cube[face, 2, 2]) in ((1, 1, 1),(-1, -1, -1)):
                self.cube[face, 1, 1] = -self.cube[face, 1, 1]
            if (self.cube[face, 2, 2], self.cube[face, 1, 1], self.cube[face, 0, 0]) in ((1, 1, 1),(-1, -1, -1)):
                self.cube[face, 1, 1] = -self.cube[face, 1, 1]

    def cree_situation_gagnee(self, nb_exemples=500):
        """
        Appel randomize et seek_and_destroy_random_win, puis
        créé les situations gagnées, donc pour chaque face :
        - trois situations pour chacune des lignes complétées
        - trois situations pour chacune des colones complétées
        - deux situations pour chacune des diagonales complétées

        nb_exemples : le nombre d'exemples produits pour chaque cas

        cette fonction copie des listes avec deepcopy et en produit un grand nombre.
        """
        for _ in range(nb_exemples):
            self.randomize()
            self.seek_and_destroy_random_win()
            # pour chaque face
            for face in range(6):
                for situation in self._cree_situation_gagnee_colonne(face) :
                    yield situation
                for situation in self._cree_situation_gagnee_ligne(face) :
                    yield situation
                for situation in self._cree_situation_gagnee_diagonale(face) :
                    yield situation

    def _cree_situation_gagnee_ligne(self, face):
        """
        sous-fonction de cree_situation_gagnee qui s'occupe des lignes.
        """
        # pour chaque ligne
        for ligne in range(3):
            # on créé une nouvelle situation
            situation = deepcopy(self.cube)
            # on remplit la ligne
            for slot in range(3):
                situation[face, ligne, slot] = 1
            yield situation

    def _cree_situation_gagnee_colonne(self, face):
        """
        sous-fonction de cree_situation_gagnee qui s'occupe des colonnes.
        """
        # pour chaque colonne
        for slot in range(3):
            # on créé une nouvelle situation
            situation = deepcopy(self.cube)
            # on remplit la colonne
            for ligne in range(3):
                situation[face, ligne, slot] = 1
            yield situation

    def _cree_situation_gagnee_diagonale(self, face):
        """
        sous-fonction de cree_situation_gagnee qui s'occupe des diagonales.

        PAS SUR QU'ELLE FONCTIONNE BIEN CELLE-LÀ
        """
        # pour chaque diagonale
        for diagonale in range(2):
            # on remplit la diagonale 1
            for ligne in range(3):
                # on créé une nouvelle situation
                situation1 = deepcopy(self.cube)
                situation1[face, ligne, ligne+diagonale] = 1
            # on remplit la diagonale 2
            for ligne in range(3):
                # on créé une nouvelle situation
                situation2 = deepcopy(self.cube)
                situation2[face, ligne, 2-ligne-diagonale] = 1
            return situation1, situation2

    def cree_situations_gagnantes_step(self, n):
        '''
        Appel cree_situation_gagnee, puis
        Créé les situations gagnantes n step, donc
        - copie 26 fois les situations gagnées
        - applique au 27 résultantes l'inverse des 27 coups existants
        - recommence jusqu'à n fois avec les résultantes précédentes

        pour l'instant on applique pas de coups de la part de l'adversaire.

        INPUT
        n (int) : le nombre de coups à jouer avant la victoire
        '''
        for situation_gagnee in self.cree_situation_gagnee():
            for _ in range(n):
                for coup in []: # if faut récupérer les coups possibles depuis le jeu
                    situation_gagnee # il faut un applique_coup qui vient du jeu
                    yield situation_gagnee

# application d'un coup inversé pour chaque nouvelle situation
# -> situations gagnantes step 1

generateur = GenerateurSituationsGagnantes()

for situation in generateur.cree_situation_gagnee(1):
    print(situation)