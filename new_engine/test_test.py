from random import randint
import copy

class tableau:
    def __init__(self,taille = 3):
        '''Initialise le jeu vide (que des 0)'''

        self.tab = [[0]*taille for _ in range(taille)]
        self.taille = taille

    def display(self):
        '''Affiche dans la console l'état actuel du jeu'''
        print("Display:")
        s = ""
        for i in range(self.taille):
            for j in range(self.taille):
                s+=str(self.tab[i][j])+" "
            s+="\n"
        print(s)
        print("Display ended.")

    def play(self,l,c,p):
        '''Prend en paramètres les coordonnées d'une case et le numéro du jouer
        effectue un tour de jeu (numéro du joueur dans la case), si elle est vide'''

        assert self.tab[l][c] == 0
        self.tab[l][c] = p

    def settab(self, t):
        self.tab = t

    def gridMax(self):
        '''Renvoie True si il n'y a plus de case vide donc plus de coup à jouer, False sinon'''
        for i in range(self.taille):
            for j in range(self.taille):
                if self.tab[i][j] == 0:
                    return False
        return True

    def stratNaive(self):
        '''Renvoie une case aléatoire dans laquelle on peut jouer (ligne, colone)'''
        if not self.gridMax():
            cases_jouables = []
            for i in range(3):
                for j in range(3):
                    if self.tab[i][j] == 0:
                        cases_jouables.append((i,j))
            return cases_jouables[randint(0, len(cases_jouables)-1)]
        return -1

    def situSuivantes(self, situation, joueur):
        """ renvoie l'ensemble des cases jouables """
        if not self.gridMax():
            cases_jouables = []
            situations = []
            for i in range(3):
                for j in range(3):
                    if self.tab[i][j] == 0:
                        cases_jouables.append((i,j))
            for i in range(len(cases_jouables)):
                tmp_situation = copy.deepcopy(situation)
                tmp_situation.play(cases_jouables[i][0],cases_jouables[i][1], joueur)
                situations.append(tmp_situation)
            return situations
        return -1

    def verifh(self):
        '''Verification horizontale : renvoi le numéro du joueur gagnant s'il y en a, -1 sinon'''

        for j in range(1,3):
            for i in range(self.taille):
                cpt=0
                for k in range(self.taille):
                    if self.tab[i][k] == j:
                        cpt+=1
                if cpt == self.taille:
                    return j
        return -1

    def verifv(self):
        '''Verification verticale : renvoi le numéro du joueur gagnant s'il y en a, -1 sinon'''

        for j in range(1,3):
            for k in range(self.taille):
                cpt = 0
                for i in range(self.taille):
                    if self.tab[i][k] == j:
                        cpt += 1
                if cpt == self.taille:
                    return j
        return -1

    def verifd(self):
        '''Verification diagonale : renvoi le numéro du joueur gagnant s'il y en a, -1 sinon'''

        for j in range(1,3):
            cpt = 0
            for i in range(3):
                if self.tab[i][i] == j:
                    cpt += 1
            if cpt == self.taille:
                return j
            cpt = 0
            for i in range(3):
                if self.tab[i][2-i] == j:
                    cpt += 1
            if cpt == self.taille:
                return j
        return -1

    def win(self):
        '''Renvoie le numéro du joueur gagnant s'il y en a, -1 sinon, à l'aide des 3 vérifications'''

        return max([self.verifv(), self.verifh(), self.verifd()])

    def eval(self):
        '''Renvoie -100 si c'est le joueur qui gagne, 100 si c'est l'ordinateur, 0 si il y a match nul et -1 si la partie n'est pas fini'''
        gagnant = self.win()
        if gagnant == 1:
            return -100
        elif gagnant == 2:
            return 100
        elif gagnant == -1:
            return 0
        return -1

    def minmax(self, joueur):
        '''Renvoie la valeur max ou min et l'instance de jeu associé'''
        #on regarde si la situation est finale
        if self.gridMax() or self.win() != -1:
            return self.eval(), [self]

        #on simule toutes les posibilités de jeu et on les stocke dans suiv
        suiv = self.situSuivantes(self, joueur)

        #si c'est un tour de l'ordinateur alors on cherche le meilleur résultat possible dans les fils (suiv) qui nous emmènerait à une victoire
        resultats = []
        if joueur == 2:
            valeur = -1000
            for suivante in suiv:
                result, _ = suivante.minmax(1)
                resultats.append(result)
                valeur = max(result, valeur)
            
            return valeur, [suiv[i] for i in range(len(resultats)) if resultats[i] == valeur]
        
        else:
            valeur = 1000
            for suivante in suiv:
                result, _ = suivante.minmax(2)
                resultats.append(result)
                valeur = min(result, valeur)
                
            return valeur, [suiv[i] for i in range(len(resultats)) if resultats[i] == valeur]




def main():
    game = tableau()
    print("État initial du jeu:")
    game.display()
    
    # Simulation d'un jeu avec des coups aléatoires
    joueur = 1
    for _ in range(3):
        l, c = game.stratNaive()
        game.play(l, c, joueur)
        print(f"Joueur {joueur} joue en ({l}, {c})")
        game.display()
        joueur = 3 - joueur  # Alterner entre 1 et 2
    
    value = game.minmax(2)
    print(f"Minmax: {value[0]}")
    board = value[1]
    board.display()

def specific_test():
    game = tableau()
    test = [
        [1, 2, 1],
        [0, 0, 0],
        [2, 0, 1]
    ]
    game.settab(test)
    value, boards = game.minmax(2)
    print("Minmax", value)
    for board in boards:
        board.display()

if __name__ == "__main__":
    specific_test()