from cube import Cube, check_type
from generators import GeneratorWinState
from random import choice
from numpy import zeros, ndarray, append
from time import time


class Partie :
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

class GenDataRubi :
    def __init__(self, batch_size : int):
        self.batch_size = batch_size
        self.gen_gagnant = GeneratorWinState()
    
    def datas(self) :
        while True :
            partie = Partie(True)
            x, y = partie.get_data()
            taille = self.batch_size-len(x)
            situation_gagnees = self.gen_gagnant.generate_random_states(taille)
            x.extend(situation_gagnees)
            y = append(y, [1.0]*taille)
            

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

def generator_datas(batch_size) :
    while True :
        partie = Partie(True)
        x, y = partie.get_data()
        return x, y


from concurrent.futures import ProcessPoolExecutor

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

if __name__ == "__main__":
    somme = 0
    start = time()

    # mise en threading des fonctions précédentes sur tous les cores 10000 fois.
    with ProcessPoolExecutor() as executor:
        results = executor.map(play_random_partie, range(10000))

    somme = sum(results)

    print("Temps :", time()-start)
    print("Somme :", somme)
    print('---------')
    somme = 0
    start = time()

    with ProcessPoolExecutor() as executor:
        results = executor.map(play_wise_random_partie, range(10000))
    
    somme = sum(results)

    print("Temps :", time()-start)
    print("Somme :", somme)
