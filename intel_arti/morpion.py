from typing import Any
from numpy import zeros, ndarray, append
from copy import deepcopy
from random import getrandbits, choice

class Plateau :
    def __init__(self) -> None:
        self.grille = zeros((3, 3, 1))
    
    def __str__(self) -> str:
        lignes = map(lambda li : f"{int(li[0, 0]): } {int(li[1, 0]): } {int(li[2, 0]): }", self.grille)
        return "\n".join(lignes)
    
    def get_state(self) -> ndarray :
        return self.grille
    
    def set_grille(self, plateau) -> None :
        self.grille = deepcopy(plateau.get_state())
    
    def placer_pion(self, pos : tuple[int, int], joueur : int) -> None:
        self.grille[*pos, 0] = joueur
    
    def reset(self) -> None:
        self.grille = zeros((3, 3, 1))
    
    def get_pion(self, pos : tuple[int, int]) -> int:
        return self.grille[*pos, 0]
    
    def is_full(self) -> bool:
        for i in range(3) :
            for j in range(3) :
                if self.get_pion((i, j)) == 0 :
                    return False
        return True
    
    def is_empty(self) -> bool:
        for i in range(3) :
            for j in range(3) :
                if self.get_pion((i, j)) != 0 :
                    return False
        return True


class Morpion :
    def __init__(self) :
        self.plateau = Plateau()
        self.plateau_modif = Plateau()
        self.joueur = 1
    
    def __str__(self) -> str:
        affichage = "\n---------\n".join(" | ".join((" ", "x", "o")[int(self.plateau.grille[j, i, 0])] for i in range(3))for j in range(3))
        return affichage
    
    def reset(self) :
        self.plateau.reset()
        self.plateau_modif.reset()
        self.joueur = 1
    
    def jouer(self, action : int, on_plateau : bool = True) :
        pos = divmod(action, 3)
        if on_plateau :
            if not self.plateau.get_pion(pos) :
                self.plateau.placer_pion(pos, self.joueur)
                self.joueur *= -1
            else :
                print("Coup interdit.")
        else :
            self.plateau_modif.placer_pion(pos, self.joueur)
    
    def actions_possibles(self) :
        actions = []
        for i in range(3) :
            for j in range(3) :
                if self.plateau.get_pion((i, j)) == 0:
                    actions.append(3 * i + j)
        return actions
    
    def reset_plateau_modif(self) :
        self.plateau_modif.set_grille(self.plateau)

    def generate_possibilite(self):
        actions = self.actions_possibles()
        for action in actions :
            self.reset_plateau_modif()
            self.jouer(action, False)
            yield action, self.plateau_modif
    
    def terminal_state(self, plateau : Plateau = None) :
        if not isinstance(plateau, Plateau) :
            plateau = self.plateau
        gagnant = 0
        terminal = False
        for i in range(3) :
            if plateau.get_pion((i, 0)) == plateau.get_pion((i, 1)) == plateau.get_pion((i, 2)) != 0 :
                gagnant += plateau.get_pion((i, 0))
                terminal = True
        for i in range(3) :
            if plateau.get_pion((0, i)) == plateau.get_pion((1, i)) == plateau.get_pion((2, i)) != 0 :
                gagnant += plateau.get_pion((0, i))
                terminal = True
        if plateau.get_pion((0, 0)) == plateau.get_pion((1, 1)) == plateau.get_pion((2, 2)) != 0 :
            gagnant += plateau.get_pion((0, 0))
            terminal = True
        if plateau.get_pion((0, 2)) == plateau.get_pion((1, 1)) == plateau.get_pion((2, 0)) != 0 :
            gagnant += plateau.get_pion((0, 2))
            terminal = True
        terminal = terminal or plateau.is_full()
        gagnant = int(gagnant // abs(gagnant)) if gagnant else 0
        return terminal, gagnant
    
    def get_state(self) :
        return self.plateau.get_state()

class PartieIAvsH :
    def __init__(self) -> None:
        self.jeu = Morpion()
        self.ia_turn = getrandbits(1)
    
    def recommencer(self) :
        self.jeu.reset()
        self.ia_turn = getrandbits(1)
    
    def step(self, action : int = None) :
        if not self.ia_turn :
            print(f"C'est au tour du joueur {self.jeu.joueur}.")
            while not (action := input("Action souhaitée : ")).isdigit() or not 0 <= int(action) <= 8:
                pass
            action = int(action)
        else :
            print(f"L'IA a choisi l'action {action}")
        self.jeu.jouer(action)
        self.ia_turn = not self.ia_turn
        return self.jeu.get_state()

class PartiesIAvsIA :
    def __init__(self, ia1, ia2) -> None:
        self.ia1 = ia1
        self.ia2 = ia2
        self.jeu = Morpion()
        self.gagnants = [0, 0, 0]
    
    def add_gagnant(self, gagnant) :
        if gagnant[1] == 1 :
            self.gagnants[0] += 1
        elif gagnant[1] == -1 :
            self.gagnants[1] += 1
        else :
            self.gagnants[2] += 1
    
    def evaluate(self) :
        while not (gagnant := self.jeu.terminal_state())[0] :
            if self.jeu.joueur == 1 :
                self.step(self.ia1(self.jeu))
            else :
                self.step(self.ia2(self.jeu))
        self.add_gagnant(gagnant)
        self.recommencer()
        while not (gagnant := self.jeu.terminal_state())[0] :
            if self.jeu.joueur == 1 :
                self.step(self.ia2(self.jeu))
            else :
                self.step(self.ia1(self.jeu))
        self.add_gagnant(gagnant)
        self.recommencer()
    
    def recommencer(self) :
        self.jeu.reset()
    
    def step(self, action : int) :
        self.jeu.jouer(action)

class RandomPartie :
    def __init__(self) -> None:
        self.jeu = Morpion()
        self.jouer_partie()
        self.eval_states()
    
    def jouer_coup(self) :
        action = choice(self.jeu.actions_possibles())
        self.jeu.jouer(action)
        return self.jeu.get_state() * (self.jeu.joueur * -1)
    
    def jouer_partie(self) :
        states = []
        while not (gagnant := self.jeu.terminal_state())[0] :
            states.append(self.jouer_coup())
        self.gagnant = gagnant[1]
        self.states = states
    
    def eval_states(self) :
        self.rewards = zeros((len(self.states), 1), float)
        if self.gagnant == 1 : # Le joueur 1 a gagné
            for i in range(0, len(self.states), 2) :
                self.rewards[i, 0] = 1/(2<<(len(self.states)-i)//2)
            for i in range(1, len(self.states), 2) :
                self.rewards[i, 0] = -1/(2<<(len(self.states)-i)//2)
        elif self.gagnant == -1 : # Le joueur -1 ou 2 a gagné
            for i in range(1, len(self.states), 2) :
                self.rewards[i, 0] = 1/(2<<(len(self.states)-i)//2)
            for i in range(0, len(self.states), 2) :
                self.rewards[i, 0] = -1/(2<<(len(self.states)-i)//2)
        else : # Egalite
            pass
    
    def get_data(self) :
        return self.states, self.rewards

class DataMorpion :
    def __init__(self, n : int) -> None:
        self.x = ndarray((0, 3, 3, 1), int)
        self.y = ndarray((0, 1))
        self.gagnants = [0, 0, 0]
        self.add_data(n)
    
    def add_data(self, n : int) :
        for _ in range(n) :
            partie = RandomPartie()
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
    

if __name__ == "__main__" :
    data = DataMorpion(1000)
    x, y = data.get_datas()
