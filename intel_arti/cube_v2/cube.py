from numpy import zeros, array, ndarray, array_equal, fliplr
from copy import deepcopy
from random import randint
from time import perf_counter

# Pour des raisons de practicités, le "sens horaire" d'une action est définie d'après la première action de sa catégorie
# Cela signifie qu'appuyer successivement sur f, b et s revient à tourner entièrement le cube vers la droite

# Nouvel ordre des actions : f, b, l, r, u, d, s, m, e
# Ancien ordre des actions : f, b, r, l, u, d, m, s, e

CORRESP_FACE_ACT = (1, 3, 2, 4, 0, 5)


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

@check_type(False, int, int, int)
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

@check_type(False, int)
def complement_2(n : int) -> int:
    """Renvoie le nombre nécessaire pour que n plus ce nombre fasse 2.
    
    Param
    ------
        n (int) : Le nombre en question
    
    Return
    -------
        int : Le résultat de 2-n
    """
    return 2-n

def find(liste : list|tuple, ele) -> int:
    """Trouve la position de l'élément ele dans liste. Si l'élément n'est pas présent, renvoie -1.
    
    Params
    ------
        liste (list|tuple) : La liste à regarder
        ele (Any) : L'élément recherché
    
    Return
    -------
        int : La position de l'élement dans la liste
    """
    for i in range(len(liste)) :
        if liste[i] == ele :
            return i
    return -1

class Surface :
    """Cette classe donne une représentation de la surface d'un cube de côté 3 et permet de le manipuler."""
    def __init__(self, surface : ndarray = None) -> None :
        """Initialise la Surface
        Param
        ------
            surface (ndarray, optional) : La surface d'un cube. Doit être de forme (6, 3, 3)
        """
        if surface is not None :
            self.set_state(surface)
        else :
            self.reset()
    
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
    
    def __eq__(self, value):
        if issubclass(type(value), Surface) :
            return array_equal(self.grille, value.grille)
        if isinstance(value, ndarray) :
            return value.shape == (6, 3, 3) and array_equal(self.grille, value)
        return False

    @check_type(True, int)
    def afficher_face(self, face : int) -> None :
        """Affiche la face demandée dans le terminal.
        
        Param
        ------
            n_face (int) : La face à afficher
        """
        affichage = ""
        for i in range(3) :
            ligne = (f"{self.get_pion((face, i, j)):>2.0f}" for j in range(3))
            affichage += " ".join(ligne) + "\n"
        print(affichage, end="")
    
    def reset(self) -> None:
        """Remet le cube à zéro."""
        self.grille = zeros((6, 3, 3))

    def get_state(self) -> ndarray :
        """Renvoie l'état actuel du Cube
        
        Return
        ------
            ndarray : L'état du cube
        """
        return self.grille
    
    def get_flatten_state(self) -> ndarray :
        return self.grille.flatten()

    @check_type(True, ndarray, bool)
    def set_state(self, state : ndarray, differenciate : bool = False) -> None :
        """Change l'état du cube en celui passé en paramètre.
        
        Param
        ------
            state (ndarray) : L'état à appliqué au cube
            differenciate (bool, optional) : Si l'état doit être copié ou juste appliqué
        """
        if differenciate :
            self.grille = deepcopy(state)
        else :
            self.grille = state
                
    def set_flatten_state(self, state : ndarray) -> None :
        self.grille = state.reshape((6, 3, 3))
    
    def check_pos(self, pos : tuple[int, int, int]) -> None:
        """Vérifie que la position passée en argument est valide
        
        Param
        -------
            pos (tuple[int, int, int]) : La position à vérifier sous la forme : face, ligne, colonne.
        """
        if not (0 <= pos[0] <= 5 and 0 <= pos[1] <= 2 and 0 <= pos[2] <= 2) :
            raise ValueError(f"La position n'est pas valide : elle est de {pos}")
    
    def get_pion(self, pos : tuple[int, int, int]) -> int :
        """Renvoie le pion qui se trouve à la position demandée.
        
        Param
        ------
            pos (tuple[int, int, int]) : La position demandée.
        
        Return
        ------
            int : Le pion qui se trouve à la position pos
        """
        self.check_pos(pos)
        return self.grille[*pos]
    
    def set_pion(self, pos : tuple[int, int, int], pion : int) -> None :
        """Change le pion à la postion pos par celui donné par pion.
        
        Params
        ------
            pos (tuple[int, int, int]) : La position demandée.
            pion (int) : Le pion à mettre à la position pos
        """
        self.check_pos(pos)
        self.grille[*pos] = pion
    
    @check_type(True, int, int)
    def get_ligne(self, face : int, ligne : int) -> ndarray :
        """Renvoie la ligne de la face et de la ligne spécifée.
        
        Params
        -----
            face (int) : Le numéro de la face.
            ligne (int) : Le numéro de la ligne.
        Return
        -------
            ndarray : La ligne demandée
        """
        self.check_pos((face, ligne, 0))
        return self.grille[face, ligne]
    
    @check_type(True, int, int, ndarray)
    def set_ligne(self, face : int, num_ligne : int, new_ligne : ndarray) -> None :
        """Remplace la ligne spécifiée par celle indiquée par new_ligne.
        
        Params
            face (int) : Le numéro de la face.
            num_ligne (int) : Le numéro de la ligne.
            new_ligne (ndarray) : La nouvelle ligne.
        """
        self.check_pos((face, num_ligne, 0))
        self.grille[face, num_ligne] = new_ligne

    @check_type(True, int, int)
    def get_colonne(self, face : int, num_col : int) -> ndarray:
        """Renvoie la colonne de la face et du numéro de colonne spécifés.
        
        Params
        -----
            face (int) : Le numéro de la face.
            num_col (int) : Le numéro de la colonne.
        Return
        -------
            ndarray : La colonne demandée
        """
        self.check_pos((face, 0, num_col))
        return self.grille[face, :, num_col]
    
    @check_type(True, int, int, ndarray)
    def set_colonne(self, face : int, num_col : int, new_col : ndarray) -> None:
        """Remplace la colonne spécifiée par celle indiquée par new_col.
        
        Params
            face (int) : Le numéro de la face.
            num_col (int) : Le numéro de la colonne.
            new_col (ndarray) : La nouvelle colonne.
        """
        self.check_pos((face, 0, num_col))
        self.grille[face, :, num_col] = new_col
    
    def get_diagonale(self, face : int, num_diag : int) -> ndarray :
        """Renvoie la diagonale de la face et du numéro de diagonale spécifés.

        Params
        ------
            face (int) : Le numéro de la face.
            num_diag (int) : Le numéro de la diagonale.
        Return
        -------
            ndarray : La diagonale demandée
        """
        self.check_pos((face, 0, 0))
        self.check_pos((face, 2, 2))
        if num_diag == 0 :
            return array([self.get_pion((face, i ,i)) for i in range(3)])
        else :
            return array([self.get_pion((face, i , complement_2(i))) for i in range(3)])

    def set_diagonale(self, face : int, num_diag : int, new_dia : ndarray) :
        for i in range(3) :
            if num_diag == 0 :
                self.set_pion((face, i, i), new_dia[i])
            else :
                self.set_pion((face, i, complement_2(i)), new_dia[i])

    def get_diagonale(self, face : int, num_diag : int) -> ndarray :
        """Renvoie la diagonale de la face et du numéro de diagonale spécifés.

        Params
        ------
            face (int) : Le numéro de la face.
            num_diag (int) : Le numéro de la diagonale.
        Return
        -------
            ndarray : La diagonale demandée
        """
        if num_diag == 0 :
            return array([self.get_pion((face, i , i)) for i in range(3)])
        else :
            return array([self.get_pion((face, i , complement_2(i))) for i in range(3)])

    @check_type(True, int)
    def get_face(self, face : int) -> ndarray :
        """Renvoie la face demandée.
        
        Param
        -----
            face (int) : Le numéro de la face.
        Return
        -------
            ndarray : La face demandée
        """
        self.check_pos((face, 0, 0))
        return self.grille[face]
    
    @check_type(True, int, ndarray)
    def set_face(self, face : int, new_face : ndarray) -> None :
        """Remplace la face spécifiée par celle indiquée par new_face.
        
        Param
        -----
            face (int) : Le numéro de la face.
            new_face (int) : La nouvelle face
        """
        self.check_pos((face, 0, 0))
        self.grille[face] = new_face
    
    def any_face(self, face : int) -> bool :
        return bool(self.get_face(face).any())
    
    def any_ligne(self, face : int, ligne : int) -> bool :
        return bool(self.get_ligne(face, ligne).any())
    
    def any_colonne(self, face : int, col : int) -> bool :
        return bool(self.get_colonne(face, col).any())

    def any_out_face(self, face : int) -> bool :
        if self.any_ligne(face, 0) or self.any_ligne(face, 2) :
            return True
        return self.get_pion((face, 1, 0)) != 0 or self.get_pion((face, 1, 2)) != 0
    

class Cube(Surface) :
    """Le cube sur lequel on joue au Morpion-Rubick's Cube. Cette classe fait office de plateau.
    A noter que cette classe ne vise un but qu'utilitaire et ne vérifie strictement pas si une action
    demandée est autorisée ou non.
    Un 0 indique une case vide. Un 1 indique une croix. Un -1 indique un rond.
    """
    def __init__(self, surface : Surface = None) -> None :
        """Initialise le cube.

        Param
        ------
            surface (Surface, optionnel) : La surface a appliqué au cube dans le cas où l'on souhaite commencer
                                            à un état prédefini, notamment lors de test
        """
        if surface is not None :
            super().__init__(surface.get_state())
        else :
            super().__init__()

    @check_type(True, ndarray, ndarray, ndarray)
    def remember_lignes(self, *lignes : ndarray) -> None :
        """Affecte à la mémoire une copie des lignes demandées.
        Ici le terme de ligne n'est pas à prendre par opposition à une colonne
        mais simplement comme une succession de 3 pions.

        Params
        -------
            *lignes (ndarray) : Les lignes à mettre en mémoire
        """
        self.memoire = deepcopy(lignes)
    
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
        """Joue l'action passée en argument.
        Les actions 0 à 17 tournent les faces du cube.
        Les actions 18 à 26 ajoutent un symbole sur la face supérieur.

        Params
        --------
            action (int) : L'action à joueur. Doit être entre 0 et 26 inclus.
            joueur (int) : Le joueur qui est en train de jouer. Soit 1, soit -1.
        """
        if action >= 18 :
            self.joueur_symbole(action, joueur)
        else :
            self.jouer_tourner(action)
    
    @check_type(True, int, int)
    def joueur_symbole(self, action : int, joueur : int) :
        """Gère la partie des actions consistant à placer un symbole.
        Place donc le symbole du joueur à la position référée par action.

        Params
        --------
            action (int) : L'action jouée. Doit être entre 0 et 8 inclus
            joueur (int) : Le joueur qui est en train de jouer. Soit 1, soit -1.
        """
        pos = (0, *divmod(action-18, 3))
        self.set_pion(pos, joueur)

    @check_type(True, int)
    def jouer_tourner(self, action : int) -> None :
        """Gère la partie des actions consistant à tourner une face du cube.

        Params
        --------
            action (int) : L'action jouée. Doit être entre 0 et 17 inclus
        """
        if reverse := action >= 9 :
            action -= 9
        if (ligne := find((1, 6, 0), action)) != -1 :
            self.tourner_couronne_horizontale(ligne, reverse)
        elif (ligne := find((2, 7, 3), action)) != -1 :
            self.tourner_couronne_verticale(ligne, reverse)
        elif (ligne := find((4, 8, 5), action)) != -1 :
            self.tourner_couronne_plate(ligne, reverse)
        if action < 6 :
            face = CORRESP_FACE_ACT[action]
            if face == 5 :
                reverse = not reverse
            self.tourner_face(face, reverse)

    @check_type(True, int, bool)
    def tourner_couronne_plate2(self, ligne : int, reverse : bool = False) -> None:
        """Tourne l'une des couronnes qui se trouve autour de la face du-dessus.
        
        Params
        -------
            ligne (int) : Le numéro de la couronne. Entre 0 et 2 inclus.
            reverse (bool, optional) : Si on tourne dans l'autre sens.
        """
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
    def tourner_couronne_plate(self, ligne: int, reverse: bool = False) -> None:
        """Tourne une couronne autour de la face supérieure.

        Params
        -------
            ligne (int) : Le numéro de la couronne à tourner (entre 0 et 2 inclus).
            reverse (bool, optional) : Si True, tourne dans le sens inverse.
        """
        # Détermine le chemin des lignes/colonnes autour de la face du dessus
        chemin = (ligne, complement_2(ligne), complement_2(ligne), ligne)
        # Détermine l'ordre des faces à traiter selon le sens de rotation
        if reverse:
            face_order = range(1, 5)
            sec_face_order = first_last(1, 5)
            memoire_func = self.get_ligne
        else:
            face_order = range(4, 0, -1)
            sec_face_order = first_last(4, 0, -1)
            memoire_func = self.get_colonne
        # Sauvegarde la ligne ou colonne initiale en fonction du sens de rotation
        self.remember_lignes(memoire_func(face_order.start, chemin[face_order.start-1]))
        # Boucle sur les faces pour effectuer les échanges de lignes/colonnes
        for i, (face, sec_face) in enumerate(zip(face_order, sec_face_order)):
            is_last_step = (i == 3)
            is_col = face in (2, 4)
            # Obtenir la ligne ou colonne à copier
            if is_last_step:
                src = self.memoire[0][::-1]
            elif is_col : # comme c'est une colonne, on prend une ligne
                src = self.get_ligne(sec_face, chemin[sec_face-1])
            else :
                src = self.get_colonne(sec_face, chemin[sec_face-1])
            if sec_face not in (1, 4) and face not in (1, 4): # L'inverser dans certains cas mystérieux
                src = src[::-1]
            # Déterminer si on doit travailler avec des lignes ou colonnes
            if is_col:
                self.set_colonne(face, chemin[face-1], src)
            else:
                self.set_ligne(face, chemin[face-1], src)

    
    @check_type(True, int, bool)
    def tourner_couronne_horizontale(self, ligne : int, reverse : bool = False) -> None:
        """Tourne l'une des couronnes horizontales sur le patron.
        
        Params
        -------
            ligne (int) : Le numéro de la couronne. Entre 0 et 2 inclus.
            reverse (bool, optional) : Si on tourne dans l'autre sens.
        """
        ordre = (0, 4, 5, 2) if reverse else (0, 2, 5, 4)
        self.remember_lignes(self.get_ligne(0, ligne))
        for i in range(3) :
            self.set_ligne(ordre[i], ligne, self.get_ligne(ordre[i+1], ligne))
        self.set_ligne(ordre[3], ligne, self.memoire[0])

    @check_type(True, int, bool)
    def tourner_couronne_verticale(self, colonne : int, reverse : bool = False) -> None:
        """Tourne l'une des couronnes verticales sur le patron.
        
        Params
        -------
            ligne (int) : Le numéro de la couronne. Entre 0 et 2 inclus.
            reverse (bool, optional) : Si on tourne dans l'autre sens.
        """
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
    def etat_suppose_terminal_old(self, state : ndarray) :
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
        return end or full, int(somme)

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
        return action
    
    def aleatoire(self) -> None:
        """Change les faces du Cube de façon entièrement aléatoire.
        Si uniquement des -1, 0 et 1 sont utilisés, cela ne signifie pas
        pour autant que la situation est succeptible d'être atteinte."""
        for face in range(6) :
            for ligne in range(3) :
                for colonne in range(3) :
                    self.set_pion((face, ligne, colonne), randint(-1, 1))

    @check_type(True, bool, bool)
    def symetrie(self, horizontale : bool, verticale : bool) -> ndarray:
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

    @check_type(True, bool, bool)
    def set_symetrie(self, horizonatale : bool, verticale : bool) -> None:
        """Applique une symétrie au cube.
        
        Params
        -------
            horizontale (bool) : Si la symétrie horizontale doit être appliquée
            verticale (bool) : Si la symétrie verticale doit être appliquée
        """
        self.set_state(self.symetrie(horizonatale, verticale))
    
    @check_type(True, int)
    def actions_possibles(self, coup_interdit : int = -1) -> list[int]:
        """Renvoie toutes les actions possibles dans l'état du jeu.
        
        Param
        ------
            coup_interdit (int, optional) : Le coup inverse de celui joué avant et par conséquent interdit.
        Return
        ------
            list[int] : La liste de coups possibles dans l'état actuel. Contient entre 17 et 27 coups.
        """
        actions = list(range(18))
        if coup_interdit != -1 :
            actions.remove(coup_interdit)
        for li in range(3) :
            for col in range(3) :
                if self.get_pion((0, li, col)) == 0 :
                    actions.append(18 + 3 * li + col)
        return actions
    
    def not_wise(self, action : int) :
        if action < 18 :
            return False
        if action >= 9 :
            action -= 9
        non_wise = False
        if (ligne := find((1, 6, 0), action)) != -1 :
            faces = (0, 4, 5, 2)
            for face in faces :
                non_wise = non_wise or self.any_ligne(face, ligne)
        elif (ligne := find((2, 7, 3), action)) != -1 :
            faces = (0, 1, 5, 3)
            for i in range(4) :
                colonne = ligne if i % 2 else complement_2(ligne)
                non_wise = non_wise or self.any_colonne(faces[i], colonne)
        elif (ligne := find((4, 8, 5), action)) != -1 :
            faces = range(1, 5)
            chemin = (ligne, complement_2(ligne), complement_2(ligne), ligne)
            for face in faces :
                if face % 2 :
                    self.any_colonne(face, chemin[face-1])
        if action < 6 :
            non_wise = non_wise or self.any_out_face(CORRESP_FACE_ACT[action])
        return non_wise
        
        


if __name__ == "__main__" :
    # s = Surface(array([[[-1, -1, -1], [0, 0, 0], [1, 1, 1]], [[1, 0, -1], [-1, 0, 1], [0, 1, -1]], [[1, 1, 0], [1, -1, 0], [0, 0, 1]], [[0, 1, 0], [1, 0, 0], [0, 0, 1]], [[1, -1, 1], [1, 0, 1], [0, 0, 1]],[[-1, 1, 1], [1, -1, 0], [1, -1, -1]]]))
    # cube = Cube(s)
    cube = Cube()
    cube.aleatoire()
    print(cube)
    # print(cube)
    # cube.tourner_couronne_verticale(0)
    # print()
    # print(cube)
    print(cube.get_diagonale(0, 0))
    print(cube.get_diagonale(0, 1))