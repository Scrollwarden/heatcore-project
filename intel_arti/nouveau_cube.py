from numpy import zeros, array, ndarray
from copy import deepcopy
from random import randint
from time import perf_counter

# La face à tourner par numéro d'action
CORRESP_FACE_ACT = (4, 2, 1, 3, 0, 5)
# Le chemin à prendre par numéro d'action
CORRESP_PATH_ACT = (
    (0, 1, 5, 3), # f, b, s
    (0, 2, 5, 4), # l, r, m
    (1, 2, 3, 4) # u, d, e
)
# Pour des raisons de practicités, le "sens horaire" d'une action est définie d'après la première action de sa catégorie
# Cela signifie qu'appuyer successivement sur f, b et s revient à tourner entièrement le cube vers la droite

# Nouvel ordre des actions : f, b, l, r, u, d, s, m, e
# Ancien ordre des actions : f, b, r, l, u, d, m, s, e


def check_type(ignore_first : bool, *args_type : type, **kwargs) :
    """Vérifie que tous les arguments d'une fonction soient du type demandé
    
    Param 
    -------

        args_type (type) : les types attendus pour chaque argument
    
    Return
    -------
        function : La fonction une fois validée
    """
    def decorateur(fonction) :
        def verification(*args) :
            for i in range(ignore_first, len(args)) :
                if not isinstance(args[i], args_type[i - ignore_first]) :
                    raise TypeError(f"L'argument {i} est du type {type(args[i])} au lieu du type {args_type[i - ignore_first]}")
            return fonction(*args)
        return verification
    return decorateur

def mesurer_temps(fonction):
    """Affiche le temps d'exécution de la fonction passée en argument
    
    Param
    --------
        fonction (function) La fonction
    
    Return
    --------
        function : La fonction dont le temps est mesurée
    """
    def fonction_modifiee(*args, **kwargs):
        debut = perf_counter()
        resultat = fonction(*args, **kwargs)
        fin = perf_counter()
        print(f"Temps d'exécution de {fonction.__name__}: {fin - debut} secondes.")
        return resultat
    return fonction_modifiee

class Cube :
    """La classe Cube enregistre l'état du cube à tout instant et permet de le modifier.
    Un 0 indique une case vide. Un 1 indique une croix. Un -1 indique un rond.
    """

    def __init__(self) -> None:
        """Initialise le Cube. Dans son état initial, celui-ci est entièrement vide"""
        self.reset_cube()
    
    def __str__(self) -> str:
        """Retourne un string dès lors qu'on fait str(Cube) par exemple dans print(Cube)

        Return
        -------
            str: Le string retourné représentant le cube
        """
        ligne_vide = " " * 9
        affichage = ""
        for i in range(3) :
            ligne = (f"{self.faces[3, i, j]:>2.0f}" for j in range(3))
            affichage += ligne_vide + " ".join(ligne) + "\n"
        for i in range(3) :
            ligne = ((f"{self.faces[f, i, j]:>2.0f}" for j in range(3)) for f in (2, 0, 4, 5))
            affichage += "|".join(" ".join(morceau) for morceau in ligne) + "\n"
        for i in range(3) :
            ligne = (f"{self.faces[1, i, j]:>2.0f}" for j in range(3))
            affichage += ligne_vide + " ".join(ligne) 
            affichage += "\n" if i != 2 else ""
        return affichage
    
    @check_type(True, int)
    def afficher_face(self, face : int) :
        """Affiche la face demandée dans le terminal.
        
        Param
        ------
            face (int) : La face à afficher
        """
        for i in range(3) :
            print(*self.faces[face, i])
    
    @mesurer_temps
    def aleatoire(self) -> None:
        """Change les faces du Cube de façon entièrement aléatoire.
        Si uniquement des -1, 0 et 1 sont utilisés, cela ne signifie pas
        pour autant que la situation est succeptible d'être atteinte."""
        for face in range(6) :
            for ligne in range(3) :
                for colonne in range(3) :
                    self.faces[face, ligne, colonne] = randint(-1, 1)

    def reset_cube(self) -> None:
        """Remet le Cube à son état initial."""
        self.faces = zeros((6, 3, 3))
    
    @check_type(True, ndarray)
    @mesurer_temps
    def set_faces(self, faces : ndarray) -> None:
        """Change entièrement l'état du Cube par celui passé en argument.
        Param
        ------
            faces (ndarray) : un array de la forme (6, 3, 3)
        """
        if not isinstance(faces, ndarray) :
            raise TypeError(f"Le paramètre faces est de type {type(faces)} alors qu'il est supposé être de type ndarray")
        if faces.shape != (6, 3, 3) :
            raise ValueError(f"L'array faces doit avoir la forme (6, 3, 3), mais la forme actuelle est {faces.shape}")
        self.faces = faces
    
    @check_type(True, int, int, int)
    def placer_symb(self, ligne : int, colonne : int, joueur : int) :
        """Place un symbole à la position demandée sur la face supérieure.
        
        Params
        -------
            ligne (int) : La ligne où placer le symbole. Doit être entre 0 et 2 inclus.
            colonne (int) : La colonne où placer le symbole. Doit être entre 0 et 2 inclus.
            joueur (int) : Le joueur qui est en train de jouer. Soit 1, soit -1.
        """
        if not 0 <= ligne <= 2 :
            raise ValueError(f"La ligne doit être incluse entre 0 et 2. Elle est actuellement de {ligne}")
        if not 0 <= colonne <= 2 :
            raise ValueError(f"La colonne doit être incluse entre 0 et 2. Elle est actuellement de {colonne}")
        if joueur not in (-1, 1) :
            raise ValueError(f"Le paramètre joueur ne peut être que 1 ou -1. Il est actuellement {joueur}")
        self.faces[0, ligne, colonne] = joueur

    @check_type(True, int, int, int, int)
    def ajouter_symb(self, face : int, ligne : int, colonne : int, joueur : int) -> None:
        """Ajoute un sympbole à la position demandée même si cette position n'est pas sur la face supérieure.
        Dans ce cas il ne s'agit pas d'un coup légal. Cette fonction n'a pas vocation à être utilisée pendant
        une partie mais plutôt pour créer une situation théorique, pour l'entrainement d'une IA notamment.
        Pour ajouter un symbole lors d'une partie, préférer placer_symb plutôt.

        Params
        -------
            face (int) : La face où ajouter le symbole. Doit être entre 0 et 5 inclus.
            ligne (int) : La ligne où ajouter le symbole. Doit être entre 0 et 2 inclus.
            colonne (int) : La colonne où ajouter le symbole. Doit être entre 0 et 2 inclus.
            joueur (int) : Le joueur qui est en train de jouer. Soit 1, soit -1.
        """
        if not 0 <= face <= 5 :
            raise ValueError(f"La face doit être incluse entre 0 et 5. Elle est actuellement de {face}")
        if not 0 <= ligne <= 2 :
            raise ValueError(f"La ligne doit être incluse entre 0 et 2. Elle est actuellement de {ligne}")
        if not 0 <= colonne <= 2 :
            raise ValueError(f"La colonne doit être incluse entre 0 et 2. Elle est actuellement de {colonne}")
        if joueur not in (-1, 1) :
            raise ValueError(f"Le paramètre joueur ne peut être que 1 ou -1. Il est actuellement {joueur}")
        self.faces[face, ligne, colonne] = joueur

    @check_type(True, int, int)
    def jouer(self, action : int, joueur : int) -> None:
        """Joue l'action passée en argument.
        Les actions 0 à 17 tournent les faces du cube.
        Les actions 18 à 26 ajoutent un symbole sur la face supérieur

        Params
        --------
            action (int) : L'action à joueur. Doit être entre 0 et 26 inclus.
            joueur (int) : Le joueur qui est en train de jouer. Soit 1, soit -1.
        """
        if not isinstance(action, int) :
            raise TypeError(f"Le paramètre action est du type {type(action)} alors qu'il est supposé être du type int")
        if not 0 <= action <= 26 :
            raise ValueError(f"L'action doit être comprise entre 0 et 26 inclus. Elle est actuellement de {action}")
        if joueur not in (-1, 1) :
            raise ValueError(f"Le paramètre joueur ne peut être que 1 ou -1. Il est actuellement {joueur}")
        
        if action < 18 :
            self.jouer_tourner(action)
        else :
            self.jouer_symbole(action-18, joueur)
    
    @check_type(True, int, int)
    def jouer_symbole(self, action : int, joueur : int) -> None:
        """Gère la partie des actions consistant à placer un symbole.
        Place donc le symbole du joueur à la position référée par action.

        Params
        --------
            action (int) : L'action jouée. Doit être entre 0 et 8 inclus
            joueur (int) : Le joueur qui est en train de jouer. Soit 1, soit -1.
        """
        ligne, colonne = divmod(action, 3)
        self.placer_symb(ligne, colonne, joueur)

    @check_type(True, int)
    def jouer_tourner(self, action : int) -> None:
        """Gère la partie des actions consistant à tourner une face du cube.

        Params
        --------
            action (int) : L'action jouée. Doit être entre 0 et 17 inclus
        """
        if not 0 <= action <= 17 :
            raise ValueError(f"L'action doit être incluse entre 0 et 17. Elle est actuellement de {action}")
        if reverse := action >= 9 :
            action -= 9
        if action < 6 :
            self.tourner_face(CORRESP_FACE_ACT[action], reverse)
            n_path = action // 2
            num = (2, 0, 2, 0, 0, 2)[action]
        else :
            n_path = action - 6
            num = 1
        self.tourner_couronne(CORRESP_PATH_ACT[n_path], n_path != 0, num, reverse)
    
    @check_type(True, int, bool)
    def tourner_face(self, face : int, reverse : bool = False) -> None :
        """Tourne la face sur elle-même dans le sens horaire par défaut et dans le sens anti-horaire.
        Attention : cette méthode ne modifie rien d'autre que la face spécifiée. Cela implique que les symboles
        se trouvant sur la même tranche que la face ne tourneront pas. 
        
        Params
        --------
            face (int) : La face à tourner. Doit être entre 0 et 5 inclus.
            reverse (bool, optional) : Dans le sens anti-horaire si True.
        """
        if not 0 <= face <= 5 :
            raise ValueError(f"La face doit être entre 0 et 5. Elle est actuellement de {face}")
        haut = deepcopy(self.faces[face, 0, :])
        bas = deepcopy(self.faces[face, 2, :])
        gauche = self.faces[face, 1, 0]
        droite = self.faces[face, 1, 2]
        haut_bas = (bas[::-1], haut[::-1]) if reverse else (haut, bas)
        self.faces[face, :, 2], self.faces[face, :, 0] = haut_bas
        self.faces[face, 0, 1] = (gauche, droite)[reverse]
        self.faces[face, 2, 1] = (droite, gauche)[reverse]

    @check_type(True, list|tuple, bool, int, bool)
    def tourner_couronne(self, liste_faces : list[int], est_ligne : bool, num : int, reverse : bool) -> None:
        """Tourne la couronne de nombres associée à un mouvement.
        
        Params
        --------
            liste_faces (list[int]) : La liste des 4 faces qui seront modifiées dans l'ordre.
            est_ligne (bool) : Si les lignes sont celles qui tournent ou les colonnes sur la premières face donnée.
            num (int) : Le numéro de la ligne ou colonne modifiée. Doit être entre 0 et 2 inclus.
            reverse (bool, optional) : Dans le sens anti-horaire si True.
        """
        if reverse :
            liste_faces = liste_faces[::-1]
        liste_faces
        if est_ligne :
            ligne, col = (num, slice(3))
        else :
            ligne, col = (slice(3), num)
        temp = deepcopy(self.faces[liste_faces[0], ligne, col])
        if 0 in liste_faces : # Cas le plus simple
            for i in range(len(liste_faces) - 1) :
                self.faces[liste_faces[i], ligne, col] = self.faces[liste_faces[i+1], ligne, col]
            self.faces[liste_faces[3], ligne, col] = temp
        else :
            lignes = (num, slice(3), (num+2)%3)
            if reverse :
                cols = (slice(3), (num+2)%3, slice(3), num)
            else :
                cols = (slice(3), num, slice(3), (num+2)%3)
            for i in range(len(liste_faces) - 1) :
                self.faces[liste_faces[i], lignes[i], cols[i]] = self.faces[liste_faces[i+1], lignes[i+1], cols[i+1]]
                ligne, col = col, ligne
            self.faces[liste_faces[3], lignes[3], cols[3]] = temp

    def general_move(self, 
                     face_path: tuple[int],
                     piece_replacement: tuple[tuple[tuple[int, int]]],
                     reverse: bool = False) -> None:
        """Fonction qui permet d'effectuer n'importe quel mouvement :)

        Args:
            face_path (tuple[int]): Les faces du cube (dans l'ordre) où on effectue le mouvement
            piece_replacement (tuple[tuple[tuple[int, int]]]): Les pieces de chaque face à enlever (en fonction de la face)
            reverse (bool, optional): Si on inverse le mouvement (dans l'autre sens). False de base.
        """
        starting_face = face_path[0]
        if reverse:
            face_path = face_path[::-1]
            piece_replacement = piece_replacement[::-1]
        
        temp = [self.faces[starting_face, y, x] for x, y in piece_replacement[0]]
        for i, face in enumerate(face_path[1:]):
            for j, (x, y) in enumerate(piece_replacement[i+1]):
                temp[j], self.faces[face, y, x] = self.faces[face, y, x], temp[j]
    
    @check_type(True, bool, bool)
    @mesurer_temps
    def symetrie(self, horizontale : bool, verticale : bool) :
        """Renvoie l'état du Cube avec la ou les symétries axiales demandées
        
        Params
        -------
            horizontale (bool) : Si la symétrie horizontale doit être appliquée
            verticale (bool) : Si la symétrie verticale doit être appliquée
        """
        faces = deepcopy(self.faces)
        original = self.faces
        if horizontale :
            for face in (0, 2, 4, 5) :
                faces[face, 0], faces[face, 2] = original[face, 2], original[face, 0]
            faces[1], faces[3] = original[3, ::-1], original[1, ::-1]
        if horizontale and verticale :
            original = deepcopy(faces)
        if verticale :
            for face in (0, 1, 3, 5) :
                faces[face, :, 0], faces[face, :, 2] = original[face, :, 2], original[face, :, 0]
            faces[2], faces[4] = original[4, :, ::-1], original[2, :, ::-1]
        return faces
    
    @check_type(True, ndarray)
    def etat_suppose_terminal(self, state : ndarray) :
        """Renvoie si la partie est finie et si oui, qui a gagné dans l'état donné.
        
        Param
        -------
            state (ndarray) : L'état d'une partie. Doit être de la forme (6, 3, 3)

        Returns
        --------
            bool : Si la partie est finie
            int : Qui a gagné 
        """
        somme = 0
        end = False
        full = True
        for face in range(6) :
            for i in range(3) :
                if state[face, i, 0] == state[face, i, 1] == state[face, i, 2] != 0 :
                    end = True
                    somme += state[face, i, 0]
                if state[face, 0, i] == state[face, 1, i] == state[face, 2, i] != 0 :
                    end = True
                    somme += state[face, 0, i]
                if full :
                    full = all(state[face, i])
            if state[face, 0, 0] == state[face, 1, 1] == state[face, 2, 2] != 0 :
                end = True
                somme += state[face, 0, 0]
            if state[face, 0, 2] == state[face, 1, 1] == state[face, 2, 0] != 0 :
                end = True
                somme += state[face, 0, 2]
        return end or full, somme
    
    def terminal_state(self) -> tuple[bool, int] :
        """Renvoie si la partie est finie et si oui, qui a gagné.

        Returns
        --------
            bool : Si la partie est finie
            int : Qui a gagné 
        """
        return self.etat_suppose_terminal(self.faces)
    
    def string_to_move(self, string: str, player : int, print_move: bool=True):
        """Permet d'effectuer des mouvements facilement grâce à un string:
        R -> self.r_move()
        L -> self.l_move()
        R' -> self.r_move(reverse=True)
        RU'RM -> self.r_move(); self.u_move(reverse=True); self.r_move(); self.m_move()
        R2UF2 -> self.r_move(); self.r_move(); self.u_move(); self.f_move(); self.f_move()

        Args:
            string (str): La série d'actions à effectuer

        Raises:
            ValueError: Quand on a un caractère incorrect
        """
        moves = "fblrudsme"
        index_translator = {letter: index for index, letter in enumerate(moves)}
        i = 0
        while i < len(string):
            move = string[i].lower()
            reverse = False
            if i + 1 < len(string):
                if string[i + 1] == "'":
                    reverse = True
                    i += 1
            if move not in moves:
                raise ValueError(f"({i}) {move} is not accepted")
            action = index_translator[move]
            if reverse :
                action += 9
            self.jouer(action, player)
            if print_move:
                print(f"Move: {move.upper()}", end='')
                if reverse:
                    print("'", end='')
                print()
            i += 1
    
    def actualize_display(self) :
        faces = deepcopy(self.faces)

        self.display_state = faces

if __name__ == "__main__" :
    cube = Cube()
    cube.aleatoire()
    print(cube)