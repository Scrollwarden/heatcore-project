from numpy import zeros, array, ndarray
from copy import deepcopy

# La face à tourner par numéro d'action
CORRESP_FACE_ACT = (1, 3, 4, 2, 0, 5)

def check_type(ignore_first, *args_type : type) :
    """Vérifie que tous les arguments d'une fonction soient du type demandé
    
    Param 
    -------
        args_type (type) : les types attendus pour chaque argument
    
    """
    def decorateur(fonction) :
        def verification(*args) :
            for i in range(ignore_first, len(args)) :
                if not isinstance(args[i], args_type[i - ignore_first]) :
                    raise TypeError(f"L'argument {i} est du type {type(args[i])} au lieu du type {args_type[i - ignore_first]}")
            return fonction(*args)
        return verification
    return decorateur

class Cube :
    """La classe Cube enregistre l'état du cube à tout instant et permet de le modifier.
    Un 0 indique une case vide. Un 1 indique une croix. Un -1 indique un rond.
    """

    def __init__(self) -> None:
        """Initialise le Cube. Dans son état initial, celui-ci est entièrement vide"""
        self.reset_cube()
        # Pour les tests
        self.faces[0, 1] = array([1, -1, 1])
        self.faces[4, 1] = array([1, -1, -1])
        self.faces[5, 1] = array([1, 0, 0])
        self.faces[2, 1] = array([0, 1, -1])
    
    def __str__(self) -> str:
        """Retourne un string dès lors qu'on fait str(Cube) par exemple dans print(Cube)

        Return:
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

    def reset_cube(self) -> None:
        """Remet le Cube à son état initial."""
        self.faces = zeros((6, 3, 3))
    
    @check_type(True, ndarray)
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
        #self.tourner_couronne()
    
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

    @check_type(True, list, bool, int)
    def tourner_couronne(self, liste_faces : list[int], est_ligne : bool, num : int) -> None:
        """Tourne la couronne de nombres associée à un mouvement.
        
        Params
        --------
            liste_faces (list[int]) : La liste des 4 faces qui seront modifiées dans l'ordre.
            est_ligne (bool) : Si les lignes sont celles qui tournent ou les colonnes sur la premières face donnée.
            num (int) : Le numéro de la ligne ou colonne modifiée. Doit être entre 0 et 2 inclus.
        """
        if 0 in liste_faces : # Cas le plus simple
            if est_ligne :
                self.faces[liste_faces[0], num, :], self.faces[liste_faces[1], num, :], self.faces[liste_faces[2], num, :], self.faces[liste_faces[3], num, :] = self.faces[liste_faces[1], num, :], self.faces[liste_faces[2], num, :], self.faces[liste_faces[3], num, :], self.faces[liste_faces[0], num, :]
        else :
            pass
    
    @check_type(True, bool, bool)
    def symetrie(self, horizontale : bool, verticale : bool) :
        """Renvoie l'état du Cube avec la ou les symétries axiales demandées
        
        Params
        -------
            horizontale (bool) : Si la symétrie horizontale doit être appliquée
            verticale (bool) : Si la symétrie verticale doit être appliquée
        """

if __name__ == "__main__" :
    cube = Cube()
    print(cube)