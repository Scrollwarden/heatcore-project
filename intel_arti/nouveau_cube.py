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


def check_type(ignore_first : bool, *args_type : type) :
    """Vérifie que tous les arguments d'une fonction soient du type demandé
    
    Param 
    -------
        ignore_first (bool) : S'il faut ignorer le premier argument de la fonction (pour que self soit ignoré dans les méthodes)
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

def first_last(start : int, stop : int, step : int = 1):
    """Agit strictement comme un range excepté que l'élément qui aurait été renvoyé en premier est renvoyé en dernier.

    Params
    -------
        start (int) : Le nombre spécifiant à quel position commencer
        stop (int) : Le nombre spécifiant à quel position s'arrêter
        step (int, optional) : Le pas utilisé
    
    Return
    -------
        Genrator[int] : Le générateur de nombre
    """
    for i in range(start + step, stop, step) :
            yield i
    yield start

def complement_2(n : int) :
    return 2-n

def find(liste : list|tuple, ele) :
    for i in range(len(liste)) :
        if liste[i] == ele :
            return i
    return -1

class Surface :
    """Cette classe donne une représentation de la surface d'un cube de côté 3 et permet de le manipuler.

    """
    def __init__(self, surface : ndarray = None) :
        if surface is not None :
            self.grille = surface
        else :
            self.grille = zeros((6, 3, 3))
    
    def __str__(self) -> str:
        """Retourne un string dès lors qu'on fait str(Surface) par exemple dans print(Surface).
        Cette représentation est sous la forme d'un patron du cube qui suit ce modèle pour la disposition des faces :
            3
         2  0  4  5
            1

        Return
        -------
            str: Le string retourné représentant la surface du cube
        """
        ligne_vide = " " * 9
        affichage = ""
        for i in range(3) :
            ligne = (f"{self.get_pion((3, i, j)):>2.0f}" for j in range(3))
            affichage += ligne_vide + " ".join(ligne) + "\n"
        for i in range(3) :
            ligne = ((f"{self.get_pion((f, i, j)):>2.0f}" for j in range(3)) for f in (2, 0, 4, 5))
            affichage += "|".join(" ".join(morceau) for morceau in ligne) + "\n"
        for i in range(3) :
            ligne = (f"{self.get_pion((1, i, j)):>2.0f}" for j in range(3))
            affichage += ligne_vide + " ".join(ligne) 
            affichage += "\n" if i != 2 else ""
        return affichage
    
    def get_state(self) :
        return self.grille
    
    def set_state(self, state : ndarray) :
        self.grille = state
    
    def check_pos(self, pos : tuple[int, int, int]) :
        if not (0 <= pos[0] <= 5 and 0 <= pos[1] <= 2 and 0 <= pos[2] <= 2) :
            raise ValueError(f"La position n'est pas valide : elle est de {pos}")
    
    def get_pion(self, pos : tuple[int, int, int]) :
        self.check_pos(pos)
        return self.grille[*pos]
    
    def set_pion(self, pos : tuple[int, int, int], pion : int) :
        self.check_pos(pos)
        self.grille[*pos] = pion
    
    def get_ligne(self, face : int, ligne : int) :
        self.check_pos((face, ligne, 0))
        return self.grille[face, ligne]
    
    def set_ligne(self, face : int, num_ligne : int, new_ligne : ndarray) :
        self.check_pos((face, num_ligne, 0))
        self.grille[face, num_ligne] = new_ligne

    def get_colonne(self, face : int, num_col : int) :
        self.check_pos((face, 0, num_col))
        return self.grille[face, :, num_col]
    
    def set_colonne(self, face : int, num_col : int, new_col : ndarray) :
        self.check_pos((face, 0, num_col))
        self.grille[face, :, num_col] = new_col
    
    def get_face(self, face : int) :
        self.check_pos((face, 0, 0))
        return self.grille[face]
    
    def set_face(self, face : int, new_face : ndarray) :
        self.check_pos((face, 0, 0))
        self.grille[face] = new_face


class Cube(Surface) :
    """Le cube sur lequel on joue au Morpion-Rubick's Cube. Cette classe fait office de plateau.
    A noter que cette classe ne vise un but qu'utilitaire et ne vérifie strictement pas si une action
    demandée est autorisée ou non.
    """
    def __init__(self, surface : Surface = None) -> None :
        if surface is not None :
            super().__init__(surface.get_state())
        else :
            super().__init__()

    @check_type(True, ndarray, ndarray)
    def remember_lignes(self, *lignes : ndarray) -> None :
        """Affecte à la mémoire une copie des lignes demandées.
        Ici le terme de ligne n'est pas à prendre par opposition à une colonne
        mais simplement comme une succession de 3 pions.

        Params
        -------
            *lignes (ndarray) : Les lignes à mettre en mémoire
        """
        self.memoire = deepcopy(lignes)
    
    def reset(self) :
        self.grille = zeros((6, 3, 3))
    
    def __str__(self) -> str:
        """Retourne un string dès lors qu'on fait str(Cube) par exemple dans print(Cube)

        Return
        -------
            str: Le string retourné représentant le cube
        """
        ligne_vide = " " * 13
        ligne_sep = "-" * 9
        pions = (" ", "x", "o")
        affichage = ligne_vide
        lignes = lambda i : map(lambda x: pions[int(x)], self.get_ligne(3, i))
        affichage += f"\n{ligne_vide}".join(" | ".join(lignes(i)) for i in range(3)) + "\n" + ligne_vide + ligne_sep + '\n'
        for i in range(3) :
            lignes = map(lambda f : map(lambda x: pions[int(x)], self.get_ligne(f, i)), (2, 0, 4, 5))
            affichage += " || ".join(" | ".join(ele for ele in ligne) for ligne in lignes) + '\n'
        affichage += ligne_vide + ligne_sep + '\n' + ligne_vide
        lignes = lambda i : map(lambda x: pions[int(x)], self.get_ligne(1, i))
        affichage += f"\n{ligne_vide}".join(" | ".join(lignes(i)) for i in range(3))
        return affichage
    
    @check_type(True, int, int)
    def jouer(self, action : int, joueur : int) :
        if action >= 18 :
            self.joueur_symbole(action, joueur)
        else :
            self.jouer_tourner(action)
    
    @check_type(True, int, int)
    def joueur_symbole(self, action : int, joueur : int) :
        pos = (0, *divmod(action-18, 3))
        self.set_pion(pos, joueur)

    @check_type(True, int)
    def jouer_tourner(self, action : int) -> None:
        if reverse := action >= 9 :
            action -= 9
        if (ligne := find((1, 6, 0), action)) != -1 :
            self.tourner_couronne_horizontale(ligne, reverse)
        elif (ligne := find((2, 7, 3), action)) != -1 :
            self.tourner_couronne_verticale(ligne, reverse)
        elif (ligne := find((4, 8, 5), action)) != -1 :
            self.tourner_couronne_plate(ligne, reverse)
        if action < 6 :
            self.tourner_face((1, 3, 2, 4, 0, 5)[action], reverse)

    @check_type(True, int, bool)
    def tourner_couronne_plate(self, ligne : int, reverse : bool = False) :
        chemin = (ligne, complement_2(ligne), complement_2(ligne), ligne)
        ordre = range(1, 5) if reverse else range(4, 0, -1)
        sec_ordre = first_last(1, 5) if reverse else first_last(4, 0, -1)
        if reverse :
            self.remember_lignes(self.get_ligne(ordre.start, chemin[ordre.start-1]))
        else :
            self.remember_lignes(self.get_colonne(ordre.start, chemin[ordre.start-1]))
        # face : la face que l'on modifie
        # sec_face : la face qui donne ses pions
        for face, sec_face, i in zip(ordre, sec_ordre, range(4)) :
            if i == 3 :
                if face == 1 :
                    self.set_ligne(face, chemin[face-1], self.memoire[0][::-1])
                else :
                    self.set_colonne(face, chemin[face-1], self.memoire[0][::-1])
            else :
                if face in (2, 4) :
                    if face == 4 or sec_face in (1, 4):
                        self.set_colonne(face, chemin[face-1], self.get_ligne(sec_face, chemin[sec_face-1]))
                    else :
                        self.set_colonne(face, chemin[face-1], self.get_ligne(sec_face, chemin[sec_face-1])[::-1])
                else :
                    if face == 1 or sec_face in (1, 4) :
                        self.set_ligne(face, chemin[face-1], self.get_colonne(sec_face, chemin[sec_face-1]))
                    else :
                        self.set_ligne(face, chemin[face-1], self.get_colonne(sec_face, chemin[sec_face-1])[::-1])

    @check_type(True, int, bool)
    def tourner_couronne_horizontale(self, ligne : int, reverse : bool = False) :
        ordre = (0, 4, 5, 2) if reverse else (0, 2, 5, 4)
        self.remember_lignes(self.get_ligne(0, ligne))
        for i in range(3) :
            self.set_ligne(ordre[i], ligne, self.get_ligne(ordre[i+1], ligne))
        self.set_ligne(ordre[3], ligne, self.memoire[0])

    @check_type(True, int, bool)
    def tourner_couronne_verticale(self, colonne : int, reverse : bool = False) :
        ordre = (0, 1, 5, 3) if reverse else (0, 3, 5, 1)
        self.remember_lignes(self.get_colonne(0, colonne))
        for i in range(3) :
            if i == 2 :
                self.set_colonne(ordre[i], complement_2(colonne), self.get_colonne(ordre[i+1], colonne)[::-1])
            elif i == 1 :
                self.set_colonne(ordre[i], colonne, self.get_colonne(ordre[i+1], complement_2(colonne))[::-1])
            else :
                self.set_colonne(ordre[i], colonne, self.get_colonne(ordre[i+1], colonne))
        self.set_colonne(ordre[3], colonne, self.memoire[0])

    @check_type(True, int, bool)
    def tourner_face(self, face : int, reverse : bool = False) -> None :
        """Tourne la face sur elle-même dans le sens horaire par défaut
        et dans le sens anti-horaire quand reverse vaut True.
        Attention : cette méthode ne modifie rien d'autre que la face spécifiée. Cela implique que les symboles
        se trouvant sur la même tranche que la face ne tourneront pas. 
        
        Params
        --------
            face (int) : La face à tourner. Doit être entre 0 et 5 inclus.
            reverse (bool, optional) : Dans le sens anti-horaire si True.
        """
        if not 0 <= face <= 5 :
            raise ValueError(f"La face doit être entre 0 et 5. Elle est actuellement de {face}")
        reverse = not reverse if face in (3, 4) else reverse
        self.remember_lignes(self.get_ligne(face, 0), self.get_ligne(face, 2))
        gauche = self.get_pion((face, 1, 0))
        droite = self.get_pion((face, 1, 2))
        if reverse :
            self.set_colonne(face, 2, self.memoire[1][::-1])
            self.set_colonne(face, 0, self.memoire[0][::-1])
        else :
            self.set_colonne(face, 2, self.memoire[0])
            self.set_colonne(face, 0, self.memoire[1])
        self.set_pion((face, 0, 1), (gauche, droite)[reverse])
        self.set_pion((face, 2, 1), (droite, gauche)[reverse])
    
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
        return end or full, int(somme // abs(somme)) if somme != 0 else 0
    
    def terminal_state(self) -> tuple[bool, int] :
        """Renvoie si la partie est finie et si oui, qui a gagné.

        Returns
        --------
            bool : Si la partie est finie
            int : Qui a gagné 
        """
        return self.etat_suppose_terminal(self.grille)
    
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
    
    def aleatoire(self) -> None:
        """Change les faces du Cube de façon entièrement aléatoire.
        Si uniquement des -1, 0 et 1 sont utilisés, cela ne signifie pas
        pour autant que la situation est succeptible d'être atteinte."""
        for face in range(6) :
            for ligne in range(3) :
                for colonne in range(3) :
                    self.set_pion((face, ligne, colonne), randint(-1, 1))


    @check_type(True, bool, bool)
    def symetrie(self, horizontale : bool, verticale : bool) :
        """Renvoie l'état du Cube avec la ou les symétries axiales demandées
        
        Params
        -------
            horizontale (bool) : Si la symétrie horizontale doit être appliquée
            verticale (bool) : Si la symétrie verticale doit être appliquée
        """
        faces = deepcopy(self.grille)
        original = self.grille
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

    def set_symetrie(self, horizonatale : bool, verticale : bool) :
        self.set_state(self.symetrie(horizonatale, verticale))
    
    def actions_possibles(self) :
        actions = list(range(18))
        for li in range(3) :
            for col in range(3) :
                if self.get_pion((0, li, col)) == 0 :
                    actions.append(18 + 3 * li + col)
        return actions

class NCube :
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
        return end or full, int(somme // abs(somme)) if somme != 0 else 0
    
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
    """cube = NCube(s)
    print(cube)"""
    s = Surface(array([[[-1, -1, -1], [0, 0, 0], [1, 1, 1]], [[1, 0, -1], [-1, 0, 1], [0, 1, -1]], [[1, 1, 0], [1, -1, 0], [0, 0, 1]], [[0, 1, 0], [1, 0, 0], [0, 0, 1]], [[1, -1, 1], [1, 0, 1], [0, 0, 1]],[[-1, 1, 1], [1, -1, 0], [1, -1, -1]]]))
    cube = Cube(s)
    print(cube)
    cube.tourner_couronne_verticale(0)
    print()
    print(cube)
