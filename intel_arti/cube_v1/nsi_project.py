from random import randint, choice

class Cube:
    def __init__(self) -> None:
        self.faces: list[list[list[int]]]
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
            ligne = (f"{self.faces[3][i][j]:>2.0f}" for j in range(3))
            affichage += ligne_vide + " ".join(ligne) + "\n"
        for i in range(3) :
            ligne = ((f"{self.faces[f][i][j]:>2.0f}" for j in range(3)) for f in (2, 0, 4, 5))
            affichage += "|".join(" ".join(morceau) for morceau in ligne) + "\n"
        for i in range(3) :
            ligne = (f"{self.faces[1][i][j]:>2.0f}" for j in range(3))
            affichage += ligne_vide + " ".join(ligne) 
            affichage += "\n" if i != 2 else ""
        return affichage

    def aleatoire(self) -> None:
        """Change les faces du Cube de façon entièrement aléatoire.
        Si uniquement des -1, 0 et 1 sont utilisés, cela ne signifie pas
        pour autant que la situation est succeptible d'être atteinte."""
        for face in range(6) :
            for ligne in range(3) :
                for colonne in range(3) :
                    self.faces[face][ligne][colonne] = randint(-1, 1)
    
    def __str2__(self) -> str:
        """Retourne un string dès lors qu'on fait str(Cube) par exemple dans print(Cube)

        Returns:
            str: Le string retourné
        """
        return "\n\n".join("\n".join(" ".join(str(number) for number in line) for line in face) for face in self.faces) + "\n\n"
    
    def reset_cube(self) -> None:
        """Remet le cube à zéro"""
        self.faces = [[[0 for _ in range(3)] for _ in range(3)] for _ in range(6)]
        for face in range(6) :
            self.faces[face][0][0] = 1
            self.faces[face][0][1] = 1
        self.faces[1][1][1] = -1
        self.faces[4][0][1] = -1
    
    def terminal_state(self, state : list[list[list[int]]] = None) -> tuple[bool, int]:
        draw = True
        end = False
        count = 0
        state = self.faces if state == None else state
        for face in state:
            for i in range(3):
                if abs(sum(face[i])) == 3:  # Check rows
                    count += face[i][0]
                    end = True
                if abs(sum(face[j][i] for j in range(3))) == 3:  # Check columns
                    count += face[0][i]
                    end = True
            if abs(sum(face[i][i] for i in range(3))) == 3:  # Top-left to bottom-right
                count += face[0][0]
                end = True
            if abs(sum(face[i][2-i] for i in range(3))) == 3:  # Top-right to bottom-left
                count += face[0][2]
                end = True
            if any(cell == 0 for row in face for cell in row): # Check for any empty cell
                draw = False
        if count > 0:
            return (True, 1)
        elif count < 0:
            return (True, -1)
        else:
            return (end or draw, 0)
    
    def general_move(self, 
                     face_path: tuple[int],
                     piece_replacement: tuple[tuple[tuple[int, int]]],
                     face_rotation: int = 0,
                     reverse: bool = False,
                     cancel_face_rotation: bool = False) -> None:
        """Fonction qui permet d'effectuer n'importe quel mouvement :)

        Args:
            face_path (tuple[int]): Les faces du cube (dans l'ordre) où on effectue le mouvement
            piece_replacement (tuple[tuple[tuple[int, int]]]): Les pieces de chaque face à enlever (en fonction de la face)
            face_rotation (int, optional): La face où s'effectue la rotation. Defaults to 0.
            reverse (bool, optional): Si on inverse le mouvement (dans l'autre sens). False de base.
            cancel_face_rotation (bool, optional): Est-ce qu'on effectue pas la rotation de face (pour les tranches). False de base.
        """
        starting_face = face_path[0]
        piece_corner_rotation = ((0, 0), (2, 0), (2, 2), (0, 2), (0, 0))
        piece_edge_rotation = ((1, 0), (2, 1), (1, 2), (0, 1), (1, 0))
        if reverse:
            face_path = face_path[::-1]
            piece_replacement = piece_replacement[::-1]
            piece_corner_rotation = piece_corner_rotation[::-1]
            piece_edge_rotation = piece_edge_rotation[::-1]
        
        temp = [self.faces[starting_face][y][x] for x, y in piece_replacement[0]]
        for i, face in enumerate(face_path[1:]):
            for j, (x, y) in enumerate(piece_replacement[i+1]):
                temp[j], self.faces[face][y][x] = self.faces[face][y][x], temp[j]
        
        if not cancel_face_rotation:
            temp = self.faces[face_rotation][0][0]
            for x, y in piece_corner_rotation[1:]:
                temp, self.faces[face_rotation][y][x] = self.faces[face_rotation][y][x], temp
            temp = self.faces[face_rotation][0][1]
            for x, y in piece_edge_rotation[1:]:
                temp, self.faces[face_rotation][y][x] = self.faces[face_rotation][y][x], temp
    
    def f_move(self, reverse=False) -> None:
        """Mouvement dans le sens des aiguilles du montre de la face frontale

        Args:
            reverse (bool, optional): Rotation anti-horaire. False de base.
        """
        face_path = (0, 3, 5, 1, 0)
        usual = tuple((i, 2) for i in range(3))
        piece_replacement = tuple(usual for _ in range(5))
        face_rotation = 2
        self.general_move(face_path, piece_replacement, face_rotation, reverse)
    
    def b_move(self, reverse=False) -> None:
        """Mouvement dans le sens des aiguilles du montre de la face arrière

        Args:
            reverse (bool, optional): Rotation anti-horaire. False de base.
        """
        face_path = (0, 1, 5, 3, 0)
        usual = ((0, 0), (1, 0), (2, 0))
        piece_replacement = tuple(usual for _ in range(5))
        face_rotation = 4
        self.general_move(face_path, piece_replacement, face_rotation, reverse)
    
    def r_move(self, reverse=False) -> None:
        """Mouvement dans le sens des aiguilles du montre de la face à droite

        Args:
            reverse (bool, optional): Rotation anti-horaire. False de base.
        """
        face_path = (0, 4, 5, 2, 0)
        usual = ((2, 0), (2, 1), (2, 2))
        piece_replacement = (usual, usual, ((0, 2), (0, 1), (0, 0)), usual, usual)
        face_rotation = 3
        self.general_move(face_path, piece_replacement, face_rotation, reverse)
    
    def l_move(self, reverse=False) -> None:
        """Mouvement dans le sens des aiguilles du montre de la face à gauche

        Args:
            reverse (bool, optional): Rotation anti-horaire. False de base.
        """
        face_path = (0, 2, 5, 4, 0)
        usual = ((0, 0), (0, 1), (0, 2))
        piece_replacement = (usual, usual, ((2, 2), (2, 1), (2, 0)), usual, usual)
        face_rotation = 1
        self.general_move(face_path, piece_replacement, face_rotation, reverse)
    
    def u_move(self, reverse=False) -> None:
        """Mouvement dans le sens des aiguilles du montre de la face du dessus

        Args:
            reverse (bool, optional): Rotation anti-horaire. False de base.
        """
        face_path = (2, 1, 4, 3, 2)
        piece_replacement = (((0, 0), (1, 0), (2, 0)), 
                             ((2, 0), (2, 1), (2, 2)),
                             ((2, 2), (1, 2), (0, 2)),
                             ((0, 2), (0, 1), (0, 0)),
                             ((0, 0), (1, 0), (2, 0)))
        face_rotation = 0
        self.general_move(face_path, piece_replacement, face_rotation, reverse)
    
    def d_move(self, reverse=False) -> None:
        """Mouvement dans le sens des aiguilles du montre de la face du dessous

        Args:
            reverse (bool, optional): Rotation anti-horaire. False de base.
        """
        face_path = (2, 3, 4, 1, 2)
        piece_replacement = (((0, 2), (1, 2), (2, 2)),
                             ((2, 2), (2, 1), (2, 0)),
                             ((2, 0), (1, 0), (0, 0)),
                             ((0, 0), (0, 1), (0, 2)),
                             ((0, 2), (1, 2), (2, 2)))
        face_rotation = 5
        self.general_move(face_path, piece_replacement, face_rotation, reverse)
    
    def m_move(self, reverse=False) -> None:
        """Mouvement dans le sens des aiguilles du montre (par rapport à la face gauche) de la tranche verticale

        Args:
            reverse (bool, optional): Rotation anti-horaire. False de base.
        """
        face_path = (0, 2, 5, 4, 0)
        usual = ((1, 0), (1, 1), (1, 2))
        piece_replacement = (usual, usual, usual[::-1], usual, usual)
        self.general_move(face_path, piece_replacement, reverse=reverse, cancel_face_rotation=True)
    
    def e_move(self, reverse=False) -> None:
        """Mouvement dans le sens des aiguilles du montre (par rapport à la face du dessous) de la tranche horizontale

        Args:
            reverse (bool, optional): Rotation anti-horaire. False de base.
        """
        face_path = (2, 3, 4, 1, 2)
        piece_replacement = (((0, 1), (1, 1), (2, 1)),
                             ((1, 2), (1, 1), (1, 0)),
                             ((2, 1), (1, 1), (0, 1)),
                             ((1, 0), (1, 1), (1, 2)),
                             ((0, 1), (1, 1), (2, 1)))
        self.general_move(face_path, piece_replacement, reverse=reverse, cancel_face_rotation=True)
    
    def s_move(self, reverse=False) -> None:
        """Mouvement dans le sens des aiguilles du montre (par rapport à la face frontale) de la tranche frontale

        Args:
            reverse (bool, optional): Rotation anti-horaire. False de base.
        """
        face_path = (0, 3, 5, 1, 0)
        usual = tuple((i, 1) for i in range(3))
        piece_replacement = tuple(usual for _ in range(5))
        self.general_move(face_path, piece_replacement, reverse=reverse, cancel_face_rotation=True)
    
    def string_to_move(self, string: str, print_move: bool=True):
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
        moves = "fbrludmes"
        funtion_translator = (self.f_move, self.b_move, self.r_move, self.l_move, self.u_move, self.d_move, self.m_move, self.e_move, self.s_move)
        index_translator = {letter: index for index, letter in enumerate(moves)}
        i = 0
        while i < len(string):
            move = string[i].lower()
            reverse = False
            twice = False
            if i + 1 < len(string):
                if string[i + 1] == "'":
                    reverse = True
                    i += 1
                elif string[i + 1] == "2":
                    twice = True
                    i += 1
            if move not in moves:
                raise ValueError(f"({i}) {move} is not accepted")
            foo = funtion_translator[index_translator[move]]
            foo(reverse)
            if print_move:
                print(f"Move: {move.upper()}", end='')
                if reverse:
                    print("'", end='')
                if twice:
                    foo(reverse)
                    print("2", end='')
                print()
            i += 1