'''
Tous les générateurs de situations de jeu pour entrainer l'agent.
'''

from concurrent.futures import ProcessPoolExecutor
from random import randint, choice, gauss
from cube import Cube, check_type
from numpy import zeros, ndarray, append, array, ones
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
        self.liste_win_state = []

    def generate_all_states(self, times=1, joueur=1):
        """
        Génère une liste de toutes les situations où le jeu est gagné par l'agent.

        INPUT
        - times (int) : le nombre de fois où chaque situation sera générée
        avec le reste des cases définies aléatoirement (1 par défaut)
        - joueur (int) : l'équipe qui joue entre 1 et -1
        """
        self.liste_win_state = []
        for face in range(6):
            self._win_on_line(face, times, joueur),
            self._win_on_column(face, times, joueur),
            self._win_on_diagonal(face, times, joueur)

    def generate_random_states(self, n=1, joueur=1):
        """
        Génère une liste de situations où le jeu est gagné par l'agent.  
        Ces situations sont choisies aléatoirement
        
        INPUT
        - n (int) : le nombre d'états a générer
        - joueur (int) : l'équipe qui joue entre 1 et -1
        """
        self.liste_win_state = []
        limit = (n % 6) * 6
        for i in range(n):
            face = i % 6 if i < limit else randint(0, 5)
            situation_type = randint(0, 7)
            if situation_type < 3 :
                self._win_on_line(face, joueur=joueur)
            elif situation_type < 6 :
                self._win_on_column(face, joueur=joueur)
            else:
                self._win_on_diagonal(face, joueur=joueur)
        return self.liste_win_state

    def get_n_states(self, n=1):
        """
        prends dans la liste des états gagnants n situations.  
        Une génération de ces situations doit avoir eu lieu au préalable.  
        Cette méthode est un générateur yield.
        """
        for _ in range(n):
            i = randint(0, len(self.liste_win_state)-1)
            yield self.liste_win_state[i]

    def _win_on_line(self, face : int, times : int = 1, joueur : int = 1) :
        """
        Génère un état où le jeu est gagné par l'agent sur une ligne.

        INPUTS
        - face (int) : la face sur laquelle on veut générer une victoire
        - times (int) : le nombre de fois où la même génération sera générée (par défaut 1)
        - joueur (int) : l'équipe qui joue entre 1 et -1
        """
        limit = (times // 3) * 3
        for i in range(times):
            line = i % 3 if i < limit else randint(0, 2)
            situation = cube_neutre_random()
            situation.set_ligne(face, line, array([joueur]*3))
            self.liste_win_state.append(situation.get_flatten_state())

    def _win_on_column(self, face : int, times : int = 1, joueur : int = 1):
        """
        Génère un état où le jeu est gagné par l'agent sur une colonne.

        INPUTS
        - face (int) : la face sur laquelle on veut générer une victoire
        - times (int) : le nombre de fois où la même génération sera générée (par défaut 1)
        - joueur (int) : l'équipe qui joue entre 1 et -1
        """
        limit = (times // 3) * 3
        for i in range(times):
            column = i % 3 if i < limit else randint(0, 2)
            situation = cube_neutre_random()
            situation.set_colonne(face, column, array([joueur]*3))
            self.liste_win_state.append(situation.get_flatten_state())

    def _win_on_diagonal(self, face : int, times : int = 1, joueur : int = 1):
        """
        Génère un état où le jeu est gagné par l'agent sur une diagonale.

        INPUTS
        - face (int) : la face sur laquelle on veut générer une victoire
        - times (int) : le nombre de fois où la même génération sera générée (par défaut 1)
        - joueur (int) : l'équipe qui joue entre 1 et -1
        """
        limit = (times // 2) * 2
        for i in range(times) :
            num = i % 2 if i < limit else randint(0, 1)
            situation = cube_neutre_random()
            situation.set_diagonale(face, num, array([joueur]*3))
            self.liste_win_state.append(situation.get_flatten_state())

def cube_neutre_random() -> Cube:
    """
    Créé un cube remplis aléatoirement et ne comprennant  
    pas de victoires.
    """
    # cube = Cube()
    # randomize(cube)
    # SAD_random_wins(cube) - Semble plus couteux que de créer pleins de cubes jusqu'à trouver un neutre.
    # return cube
    return random_cube_perdant()

def random_cube_perdant():
    """
    """
    while (n_pions := round(gauss(8, 4))) < 0:
        pass
    winning = True
    while winning :
        cube = Cube()
        for _ in range(n_pions) :
            cube.set_pion((randint(0, 5), randint(0, 2), randint(0, 2)), choice((-1, 1)))
        winning = cube.terminal_state()[0]
    return cube

def SAD_random_wins(cube:Cube):
        """
        SAD désigne une fonction de type Seek and Destroy. Elle cherche une chose et la détruit.  
        = =  
        Enlève les positions de victoire dans un cube et les remplace par des positions neutres.

        INPUT
        - cube (Cube) : le cube dans lequel on veut enlever les positions de victoire
        """
        for face in range(6):
            # check des lignes
            for i_line in range(3):
                new_line = cube.get_ligne(face, i_line)
                if all(new_line == 1) or all(new_line == -1):
                    new_line[1] = 0 # on dégage le signe au milieu de la formation.
                    cube.set_ligne(face, i_line, new_line)
            # check des colonnes
            for i_column in range(3):
                new_column = cube.get_colonne(face, i_column)
                if all(new_column == 1) or all(new_column == -1):
                    new_column[1] = 0 # même logique qu'au dessus
                    cube.set_colonne(face, i_column, new_column)
            # check des diagonales
            for i_diagonal in range(2):
                new_diagonal = cube.get_diagonale(face, i_diagonal)
                if all(new_diagonal == 1) or all(new_diagonal == -1):
                    new_diagonal[1] = 0 # même logique qu'au dessus, on récupère toujour le centre de la face.
                    cube.set_diagonale(face, i_diagonal, new_diagonal)

def randomize(cube:Cube):
    """
    Remplit aléatoirement les cases d'un cube par -1, 0 ou 1.

    INPUT
    - cube (Cube) : le cube à remplir
    """
    for _ in range(randint(0, 30)) :
        cube.set_pion((randint(0, 5), randint(0, 2), randint(0, 2)), choice((-1, 1)))

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

class Partie:
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
        return self.cube.get_flatten_state() * (self.joueur * -1)
    
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
        return self.cube.get_flatten_state() * (self.joueur * -1)
    
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
    
    def get_data(self) -> tuple[ndarray, ndarray]:
        if not isinstance(self.states, ndarray) :
            self.states = array(self.states)
        return self.states, self.rewards

class DataRubi :
    def __init__(self, n : int) -> None:
        self.x = ndarray((0, 6, 3, 3), int)
        self.y = ndarray((0, 1))
        self.gagnants = [0, 0, 0]
        self.add_data(n)
    
    def add_data(self, n : int) :
        for _ in range(n) :
            partie = Partie(True)
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


def play_random_partie(i) :
    """Fonction donnée en thread pour les parties aléatoires"""
    partie = Partie()
    partie.random_partie()
    return len(partie.states)

def play_wise_random_partie(i) :
    """Fonction donnée en thread pour les parties aléatoires sans coups inutiles"""
    partie = Partie()
    partie.wise_random_partie()
    return len(partie.states)

class My :
    proportions = 0.5
    def __init__(self) :
        self.gagnants = {0 : 0, 1 : 0, -1 : 0}

    def generator_datas(self, batch_size : int) :
        gen = GeneratorWinState()
        while True :
            partie = Partie(True)
            self.gagnants[partie.gagnant] += 1
            x, y = partie.get_data()
            y = y.flatten()
            if (trop := x.shape[0] - batch_size) > 0 :
                x = x[trop:]
                y = y[trop:]
            elif (manque := batch_size - x.shape[0]) > 0 :
                x = append(x, array(gen.generate_random_states(manque)), 0)
                y = append(y, ones(manque))
            yield x, y
    
    def generator_datas_and_inv(self, batch_size : int) :
        gen = GeneratorWinState()
        while True :
            partie = Partie(True)
            self.gagnants[partie.gagnant] += 1
            x, y = partie.get_data()
            y = y.flatten()
            if (trop := x.shape[0] - batch_size) > 0 :
                x = x[trop:]
                y = y[trop:]
            elif (manque := batch_size - x.shape[0]) > 0 :
                # Le nombre de 
                positifs = int(manque * self.proportions)
                x = append(x, array(gen.generate_random_states(positifs, -1)), 0)
                y = append(y, ones(positifs)*(-1))
                x = append(x, array(gen.generate_random_states(manque - positifs, 1)), 0)
                y = append(y, ones(manque-positifs))
            yield x, y

    def generators_only_partie(self, batch_size : int) :
        partie = Partie(True)
        self.gagnants[partie.gagnant] += 1
        x, y = partie.get_data()
        y = y.flatten()
        while True :
            partie = Partie(True)
            self.gagnants[partie.gagnant] += 1
            new_x, new_y = partie.get_data()
            x = append(x, new_x, 0)
            y = append(y, new_y.flatten(), 0)
            if len(x) >= batch_size :
                yield x[:batch_size], y[:batch_size]
                x = x[batch_size:]
                y = y[batch_size:]


class GameSaver:
    '''
    Sauvegarde les parties jouées.
    Permet de posséder des jeux d'entraînements basés sur des choix humains.
    '''
    def __init__(self) -> None:
        self.accessed_data = []
        self.game_datas = {}
        self.nb_game_datas = 0

    def save(self, data):
        """
        sauvegarde un coup joué dans la liste actuellement modifiée
        
        INPUT
        - data (Cube.flatten_state) : l'état du jeu à sauvegarder
        """
        self.accessed_data.append(data)

    def save_game(self, name='current', call=True):
        """
        Ajoute la liste actuellement modifiée à un jeu du dictionnaire
        
        INPUT
        - name (str | int) : le nom d'un jeu existant auquel ajouter la liste.
        Si name = 'current', ajoute la liste à la première clef disponible.
        - call (bool) : si True, print une confirmation dans le terminal.
        """
        if name == 'current':
            self.game_datas[self.nb_game_datas] = self.accessed_data
            if call: print(f'Game saved as {self.nb_game_datas}')
        else:
            self.game_datas[name] = self.accessed_data
            if call: print(f'Game saved as {name}')
        self.accessed_data = []
        self.nb_game_datas += 1

    def get_game(self, name):
        """Retourne le jeu demandé du dictionnaire"""
        return self.game_datas[name]
    
    def yield_game(self, name):
        """Générateur qui retourne les coups joués dans un jeu demandé"""
        yield from self.game_datas[name]

    def get_all_games(self) -> list[str]:
        """retourne les noms de tous les jeux contenus dans le dictionnaire"""
        return list(self.game_datas.keys())

    def delete_game(self, name):
        """supprime un jeu du dictionnaire"""
        del self.game_datas[name]

    def delete_all_games(self):
        """vide le dictionnaire"""
        self.game_datas = {}

    def save_all_to_file(self, file_name=None):
        """
        enregistre toutes les données du dictionnaire dans un fichier.
        le fichier sera enregistré dans un dossier 'data_from_games'.
        """
        if file_name is None:
            ext = 'je sais pas'
            date = 'on met quoi comme discriminant ?'
            file_name = f'data_from_games_{date}.{ext}'

    def load_all_from_file(self, file):
        """charge toutes les données d'un fichier dans le dictionnaire (qui sera remplacé)"""



# Tests
# ======
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

if __name__ == "__main__" :
    obj = My()
    gen = obj.generator_datas(50)
    temps = time()
    for i in range(2) :
        print(next(gen))
    print(time()-temps)
