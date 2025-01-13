import math
import pygame, sys, os, pyautogui
from random import choice
import time
from pygame import Vector2, SurfaceType, Vector3
from agent import Agent
from tensorflow.keras.models import load_model #type: ignore
from cube import Cube
from generators import GameSaver

LINE_WIDTH = 3
SCREEN_WIDTH = pyautogui.size().width
SCREEN_HEIGHT = pyautogui.size().height
NUM_MODEL = 9
MODEL_PATH = os.path.join(os.path.abspath(__file__).rstrip("cube_ui.py"), f"models/model{NUM_MODEL}.h5")

# Colors
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 220, 0)
BLUE = (0, 128, 255)
ORANGE = (255, 128, 0)
YELLOW = (255, 255, 0)
GREY = (200, 200, 200)
MIDDLE_GREY = (150, 150, 150)
DARK_GREY = (100, 100, 100)
WHITE = (255, 255, 255)
COLORS = {
    "black": BLACK,
    "red": RED,
    "green": GREEN,
    "blue": BLUE,
    "orange": ORANGE,
    "yellow": YELLOW,
    "grey": GREY,
    "white": WHITE
}
FADED_COLORS = {key: tuple(max(0, num - 80) for num in color) for key, color in COLORS.items()}

def lerp(a: float, b: float, t: float) -> float:
    return a * t + b * (1 - t)

def lerp2(a: float, b: float, t: float) -> float:
    return (b - a) * (2 * t - t ** 2) + a

# Barycentric approach
def point_in_triangle_barycentric(point: Vector2, triangle: tuple[Vector2, Vector2, Vector2]) -> bool:
    """Fonction qui dit si un point se situe à l'intérieur d'un triangle (détection de collision).

    Params:
    * point (Vector2): le point en question
    * triangle (tuple[Vector2, Vector2, Vector2]): le triangle auquel on veut savoir si le point se situe à l'intérieur

    Return:
    * bool: True si le point est dans le triangle, False sinon"""
    p0, p1, p2 = triangle
    v0 = p2 - p0
    v1 = p1 - p0
    v2 = point - p0
    dot00 = v0.dot(v0)
    dot01 = v0.dot(v1)
    dot02 = v0.dot(v2)
    dot11 = v1.dot(v1)
    dot12 = v1.dot(v2)
    temp = (dot00 * dot11 - dot01 * dot01)
    if temp == 0:
        return False
    inv_denom = 1 / temp
    u = (dot11 * dot02 - dot01 * dot12) * inv_denom
    v = (dot00 * dot12 - dot01 * dot02) * inv_denom
    return u >= 0 and v >= 0 and (u + v) <= 1


class Camera:
    __slots__ = ['latitude', 'longitude', 'distance', 'position', 'orientation']

    def __init__(self, latitude: float, longitude: float, distance: float) -> None:
        """Initialise la camera tournante autours de l'origine en le fixant

        Params:
        * latitude (float): la latitude, son degré de rotation vertical
        * longitude (float): la longitude, son degré de rotation horizontal
        * distance (float): la distance à l'origine de la caméra"""
        self.latitude = latitude
        self.longitude = longitude
        self.distance = distance
        self.position = self.calculate_position()

    def reset_position(self):
        """Reset la position de la caméra et remet la longitude entre 0 et 2 pi"""
        self.longitude %= 2 * math.pi
        self.position = self.calculate_position()

    def calculate_position(self) -> Vector3:
        """Calcul la position de la caméra autours du cube par rapport à latitude, longitude et distance

        Return:
        * Vector3: la position en 3D de la caméra"""
        self.orientation = self.calculate_orientation()
        x = self.distance * math.cos(self.latitude) * math.cos(self.longitude)
        y = self.distance * math.sin(self.latitude)
        z = self.distance * math.cos(self.latitude) * math.sin(self.longitude)
        return Vector3(x, y, z)
    
    def calculate_orientation(self) -> int :
        return 1 if -math.pi/2 <= self.latitude <= math.pi / 2 else -1

    def update_camera_from_mouse(self, delta_x: float, delta_y: float,
                                 speed_horizontal: float=0.025*0.25, speed_vertical: float=0.025*0.25) -> None:
        """Bouge la caméra en fonction du déplacement de la souris

        Args:
        * delta_x (float): le déplacement horizontale de la souris
        * delta_y (float): le déplacement verticale de la souris
        * speed_horizontal (float): paramètre variable sur la vitesse de déplacement horizontale
        * speed_vertical (float): paramètre variable sur la vitesse de déplacement verticale"""
        # Update longitude based on horizontal mouse movement
        self.longitude = self.longitude + delta_x * speed_horizontal
        # Update latitude based on vertical mouse movement, limiting the range
        self.latitude = (self.latitude - delta_y * speed_vertical + math.pi) % (math.pi * 2) - math.pi
        self.reset_position()

    def get_ij_data(self) -> tuple[Vector2, Vector2, Vector2]:
        """Calcul les coordonnées des points (1; 0; 0), (0; 1; 0) et (0; 0; 1) pour simplifier les calculs 3D

        Return:
        * tuple[Vector2, Vector2, Vector2]: les coordonnées sur l'écran de chaque point"""
        world_points = [
            Vector3(1, 0, 0),  # X-axis
            Vector3(0, 1, 0),  # Y-axis
            Vector3(0, 0, 1),  # Z-axis
        ]

        forward = -self.position.normalize()
        up = Vector3(0, 1, 0)
        right = forward.cross(up).normalize()
        up = right.cross(forward).normalize()

        transformed_points = []
        for point in world_points:
            relative_point = point - self.position

            x_proj = relative_point.dot(right) / self.distance
            y_proj = relative_point.dot(up) / self.distance

            transformed_points.append(Vector2(x_proj, y_proj))

        return tuple(transformed_points)


class Renderer:
    __slots__ = ['ij_data', 'screen_data', 'camera']

    def __init__(self, camera: Camera, screen_data: Vector2) -> None:
        """Initialise le Renderer

        Params:
        * camera (Camera): l'objet Camera
        * screen_data (Vector2): la résolutions de la fenêtre comme un Vector2"""
        self.ij_data: tuple[Vector2, Vector2, Vector2] | None = None
        self.screen_data = Vector2(screen_data.x // 2, screen_data.y // 2)
        self.camera = camera
        self.reset()

    def reset(self) -> None:
        """Update l'attribut `ij_data` basé sur l'orientation de la caméra"""
        self.camera.reset_position()
        self.ij_data = self.camera.get_ij_data()

    def screen_coordinates(self, point: Vector3, to_tuple: bool = False) -> Vector2 | tuple[float, float]:
        """Renvoie les coordonnées 2D sur la fenêtre d'un point 3D dans l'espace

        Params:
        * point (Vector3): le point 3D dans l'espace
        * to_tuple (bool): renvoie un tuple si True, sinon renvoie un Vector2

        Return:
        * Vector2 | tuple[float, float]: les coordonnées 2D sur la fenêtre du point (en Vector2 ou tuple)"""
        ij = sum((point[k] * self.ij_data[k] for k in range(3)), Vector2(0, 0))
        coordinates = self.screen_data + (ij * self.camera.orientation)
        if to_tuple:
            return coordinates.x, coordinates.y
        return coordinates

class Line:
    __slots__ = ['start', 'end', 'color', 'width', 'points_on_screen']

    def __init__(self, point1: Vector3, point2: Vector3, renderer: Renderer, color, width: int = 1):
        """Initialise une ligne entre deux points 3D dans l'espace.

        Params:
        * point1 (Vector3): le point de départ de la ligne.
        * point2 (Vector3): le point d'arrivée de la ligne.
        * renderer (Renderer): l'objet Renderer pour calculer les coordonnées écran.
        * color: la couleur de la ligne.
        * width (int): l'épaisseur de la ligne (par défaut 1)."""
        self.start = point1
        self.end = point2
        self.color = color
        self.width = width
        self.points_on_screen = None
        self.reset_info(renderer)

    def reset_info(self, renderer: Renderer):
        """Met à jour les informations de la ligne en recalculant les coordonnées écran.

        Params:
        * renderer (Renderer): l'objet Renderer utilisé pour recalculer."""
        self.points_on_screen = (renderer.screen_coordinates(self.start),
                                 renderer.screen_coordinates(self.end))

    def draw(self, screen):
        """Dessine la ligne sur l'écran.

        Params:
        * screen: l'écran sur lequel dessiner la ligne."""
        pygame.draw.line(screen, self.color, *self.points_on_screen, width=self.width)

class EventsListener:
    def __init__(self):
        self.button_hovered: tuple[int, int] = (-1, -1)
        self.button_clicked: tuple[int, int] = (-1, -1)
        self.turn_button_pressed: int = -1

    def reset(self):
        self.button_hovered: tuple[int, int] = (-1, -1)
        self.button_clicked: tuple[int, int] = (-1, -1)
        self.turn_button_pressed: int = -1

class ConvexPolygon:
    __slots__ = ['points', 'minimum_corner', 'maximum_corner', 'color']

    def __init__(self, points: tuple[Vector2, ...], color):
        """Initialise un polygone convexe en 2D.

        Params:
        * points (tuple[Vector2, ...]): les points définissant le polygone.
        * color: la couleur du polygone."""
        self.points = points
        self.minimum_corner = Vector2([min(point[k] for point in self.points) for k in range(2)])
        self.maximum_corner = Vector2([max(point[k] for point in self.points) for k in range(2)])
        self.color = color

    def lazy_rectangle_collision_check(self, point: Vector2) -> bool:
        """Vérifie si un point se trouve dans le rectangle englobant du polygone.

        Params:
        * point (Vector2): le point à vérifier.

        Return:
        * bool: True si le point est dans le rectangle, sinon False."""
        return all(self.minimum_corner[k] <= point[k] <= self.maximum_corner[k] for k in range(2))

    def full_collision_check(self, point: Vector2) -> bool:
        """Vérifie si un point se trouve dans le polygone via la méthode complète.

        Params:
        * point (Vector2): le point à vérifier.

        Return:
        * bool: True si le point est dans le polygone, sinon False."""
        if not self.lazy_rectangle_collision_check(point):
            return False
        for i in range(1, len(self.points) - 1):
            triangle = (self.points[0],
                        self.points[i],
                        self.points[i + 1])
            if point_in_triangle_barycentric(point, triangle):
                return True
        return False

    def draw(self, screen: SurfaceType, color = None, width: int = 0):
        """Dessine le contour du polygone sur l'écran.

        Params:
        * screen (SurfaceType): l'écran sur lequel dessiner.
        * color: couleur de remplissage (par défaut, utilise la couleur du polygone).
        * width (int): épaisseur des contours (0 pour un polygone rempli)."""
        pygame.draw.polygon(screen, color if color else self.color,
                            [(point.x, point.y) for point in self.points],
                            width=width)

    def draw_filled(self, screen: SurfaceType, color = None):
        """Dessine un polygone rempli sur l'écran.

        Params:
        * screen (SurfaceType): l'écran sur lequel dessiner.
        * color: couleur de remplissage (par défaut, utilise la couleur du polygone)."""
        pygame.draw.polygon(screen, color if color else self.color,
                            [(point.x, point.y) for point in self.points])

    def __repr__(self) -> str:
        """Retourne une représentation en chaîne de caractères du polygone."""
        return f"<ConvexPolygon{self.points}>"

class ConvexPolygon3D:
    __slots__ = ['points', 'points_screen_coordinates', 'minimum_corner', 'maximum_corner', 'color']

    def __init__(self, points: tuple[Vector3, ...], renderer: Renderer, color):
        """Initialise un polygone convexe en 3D.

        Params:
        * points (tuple[Vector3, ...]): les points définissant le polygone.
        * renderer (Renderer): l'objet Renderer pour les calculs 2D.
        * color: la couleur du polygone."""
        self.points = points
        self.points_screen_coordinates: tuple[Vector2, ...] | None = None
        self.minimum_corner: Vector2 | None = None
        self.maximum_corner: Vector2 | None = None
        self.color = color
        self.reset_info(renderer)

    def reset_info(self, renderer: Renderer):
        """Recalcule les informations du polygone en fonction du Renderer donné.

        Params:
        * renderer (Renderer): l'objet Renderer utilisé pour les calculs."""
        self.points_screen_coordinates = tuple(renderer.screen_coordinates(point) for point in self.points)
        self.minimum_corner = Vector2([min(point[k] for point in self.points_screen_coordinates) for k in range(2)])
        self.maximum_corner = Vector2([max(point[k] for point in self.points_screen_coordinates) for k in range(2)])

    def lazy_rectangle_collision_check(self, point: Vector2) -> bool:
        """Vérifie si un point se trouve dans le rectangle englobant du polygone.

        Params:
        * point (Vector2): le point à vérifier.

        Return:
        * bool: True si le point est dans le rectangle, sinon False."""
        return all(self.minimum_corner[k] <= point[k] <= self.maximum_corner[k] for k in range(2))

    def full_collision_check(self, point: Vector2) -> bool:
        """Vérifie si un point se trouve dans le polygone via la méthode complète.

        Params:
        * point (Vector2): le point à vérifier.

        Return:
        * bool: True si le point est dans le polygone, sinon False."""
        if not self.lazy_rectangle_collision_check(point):
            return False
        for i in range(1, len(self.points) - 1):
            triangle = (self.points_screen_coordinates[0],
                        self.points_screen_coordinates[i],
                        self.points_screen_coordinates[i + 1])
            if point_in_triangle_barycentric(point, triangle):
                return True
        return False

    def draw(self, screen: SurfaceType, color = None, width: int = 0):
        """Dessine le contour du polygone sur l'écran.

        Params:
        * screen (SurfaceType): l'écran sur lequel dessiner.
        * color: couleur de remplissage (par défaut, utilise la couleur du polygone).
        * width (int): épaisseur des contours (0 pour un polygone rempli)."""
        pygame.draw.polygon(screen, color if color else self.color,
                            [(point.x, point.y) for point in self.points_screen_coordinates],
                            width=width)

    def draw_filled(self, screen: SurfaceType, color = None):
        """Dessine un polygone rempli sur l'écran.

        Params:
        * screen (SurfaceType): l'écran sur lequel dessiner.
        * color: couleur de remplissage (par défaut, utilise la couleur du polygone)."""
        pygame.draw.polygon(screen, color if color else self.color,
                            [(point.x, point.y) for point in self.points_screen_coordinates])

    def __repr__(self) -> str:
        """Retourne une représentation en chaîne de caractères du polygone."""
        return f"<ConvexPolygon3D{self.points}>"

class Button:
    __slots__ = ['hitbox', 'border_color', 'border_width', 'actions', 'running']

    def __init__(self, hitbox: ConvexPolygon3D | ConvexPolygon, border_color, border_width: int):
        """
        Initialise un bouton cliquable avec une hitbox 3D ou 2D.

        Params:
        * hitbox (ConvexPolygon3D | ConvexPolygon): la hitbox définissant la zone du bouton.
        * border_color: la couleur de la bordure.
        * border_width: l'épaisseur de la bordure.
        """
        self.hitbox = hitbox
        self.border_color = border_color
        self.border_width = border_width
        self.actions = []

    def reset_info(self, renderer: Renderer):
        """Recalcule les informations de la hitbox avec un nouveau Renderer.

        Params:
        * renderer (Renderer): l'objet Renderer utilisé pour les calculs."""
        if isinstance(self.hitbox, ConvexPolygon3D):
            self.hitbox.reset_info(renderer)

    def add_action(self, action):
        """Ajoute une action au bouton.

        Params:
        * action: la fonction à exécuter lorsqu'on clique sur le bouton."""
        self.actions.append(action)

    def draw(self, screen: SurfaceType, mouse: tuple[int, int], click: bool) -> bool:
        """Dessine le bouton et détecte les interactions utilisateur.

        Params:
        * screen (SurfaceType): l'écran où dessiner le bouton.
        * mouse (tuple[int, int]): les coordonnées de la souris.
        * click (bool): indique si un clic est détecté.

        Return:
        * bool: True si le bouton est cliqué, sinon False."""
        self.hitbox.draw_filled(screen)
        if self.hitbox.full_collision_check(mouse):
            self.hitbox.draw(screen)
            self.hitbox.draw(screen, self.border_color, 3 * self.border_width)
            if click:
                for action in self.actions:
                    action()
            return True
        else:
            self.hitbox.draw(screen)
            self.hitbox.draw(screen, self.border_color, self.border_width)
            return False

    def __repr__(self) -> str:
        """Retourne une représentation en chaîne de caractères du bouton."""
        return f"<Button{self.hitbox}>"

class HiddenButton(Button):
    __slots__ = ['hitbox', 'show_area', 'color', 'border_width', 'actions']

    def __init__(self, hitbox: ConvexPolygon3D, show_area: ConvexPolygon3D, color, border_width):
        """Initialise un bouton caché qui ne peut être activé que si la souris est dans une zone visible.

        Params:
        * hitbox (ConvexPolygon3D): la zone où le bouton est cliquable
        * show_area (ConvexPolygon3D): la zone où le bouton peut apparaître
        * color: la couleur du bouton
        * border_width: l'épaisseur de la bordure"""
        super().__init__(hitbox, color, border_width)
        self.show_area = show_area

    def reset_info(self, renderer: Renderer):
        """Met à jour les informations de rendu pour le bouton et sa zone visible.

        Params:
        * renderer (Renderer): l'objet Renderer utilisé pour calculer les coordonnées sur l'écran"""
        super().reset_info(renderer)
        self.show_area.reset_info(renderer)

    def draw(self, screen: SurfaceType, mouse: tuple[int, int], click: bool) -> tuple[bool, bool]:
        """Dessine le bouton caché s'il est visible, et vérifie si un clic a eu lieu.

        Params:
        * screen (SurfaceType): la surface Pygame où le bouton sera dessiné
        * mouse (tuple[int, int]): la position actuelle de la souris
        * click (bool): True si un clic est détecté

        Return:
        * tuple[bool, bool]: (visible, cliqué)"""
        if not self.show_area.full_collision_check(mouse):
            return False, False
        return True, super().draw(screen, mouse, click)

    def __repr__(self) -> str:
        """Retourne une représentation en chaîne de caractères du bouton."""
        return f"<HiddenButton({self.hitbox}, {self.show_area})>"

class Face :
    DANS_PORTION = ((lambda camera : abs(camera.longitude - math.pi * 3 / 2) <= math.pi / 4,
                     lambda camera : abs(camera.longitude - math.pi / 2) <= math.pi / 4),
                    (lambda camera : abs(camera.longitude - math.pi) < math.pi / 4,
                     lambda camera : math.pi > abs(camera.longitude - math.pi) > math.pi * 3 / 4),
                    (lambda camera : abs(camera.longitude - math.pi / 2) <= math.pi / 4,
                     lambda camera : abs(camera.longitude - math.pi * 3 / 2) <= math.pi / 4),
                    (lambda camera : math.pi > abs(camera.longitude - math.pi) > math.pi * 3 / 4,
                     lambda camera : abs(camera.longitude - math.pi) < math.pi / 4))
    def __init__(self, polygone : ConvexPolygon3D, num : int, renderer : Renderer) -> None:
        """Initialise la face.
        
        Params :
        polygon (ConvesPolygon3D) : Le polygone qui représente la face.
        num (int) : Le numéro de la face. Entre 0 et 5 inclus.
        renderer (Renderer) : L'objet Renderer utilisé pour afficher la face."""
        self.polygone = polygone
        self.num = num
        self.is_top = num == 0
        self.renderer = renderer
        self.lines : tuple[Line] = ()
        self.buttons : list[HiddenButton] = []
        camera = self.renderer.camera
        if self.num == 1:
            self.fonction = lambda : (abs(camera.longitude - math.pi / 2) <= math.pi / 2) == (abs(camera.latitude) <= math.pi / 2)
        elif self.num == 2:
            self.fonction = lambda : (abs(camera.longitude - math.pi) >= math.pi / 2) == (abs(camera.latitude) <= math.pi / 2)
        elif self.num == 3:
            self.fonction = lambda : (abs(camera.longitude - math.pi / 2) >= math.pi / 2) == (abs(camera.latitude) <= math.pi / 2)
        elif self.num == 4:
            self.fonction = lambda : (abs(camera.longitude - math.pi) <= math.pi / 2) == (abs(camera.latitude) <= math.pi / 2)
        elif self.num == 5:
            self.fonction = lambda : camera.latitude < 0
        else :
            self.fonction = lambda : camera.latitude >= 0
        
    def proportion_suffisante(self) :
        if self.num in (0, 5) :
            return True
        if not self.visible() :
            return False
        camera = self.renderer.camera
        avant = abs(camera.latitude) <= math.pi / 2
        return self.DANS_PORTION[self.num-1][avant](camera)

    def add_button(self, button : HiddenButton) -> None :
        """Ajoute un bouton à la face.
        
        Params :
            button (HiddenButton) : Le bouton à ajouter
        """
        self.buttons.append(button)

    def set_lines(self, lines : tuple[Line]) -> None :
        """Enregistre les lignes de la face.
        
        Params :
            lines (tuple[Line]) : Les lignes à enregistrer
        """
        self.lines = lines

    def visible(self) -> bool:
        """Dit si la face est visible ou non.

        Return :
        * bool: si la face est visible ou pas"""
        return self.fonction()
    
    def draw_anyway(self, screen: SurfaceType, color = None, width: int = 0) -> None:
        """Dessine la face même si elle n'est pas supposée être visible.
        
        Params:
        * screen (SurfaceType): l'écran sur lequel dessiner.
        * color: couleur de remplissage (par défaut, utilise la couleur du polygone).
        * width (int): épaisseur des contours (0 pour un polygone rempli)."""
        if not self.is_top :
            self.polygone.draw_filled(screen)
            self.polygone.draw(screen, color, width)
            for line in self.lines :
                line.draw(screen)
        else :
            self.polygone.draw(screen, color, width)
    
    def draw(self, screen: SurfaceType,
             color = None, width: int = 0) -> bool:
        """Dessine la face uniquement si elle est censée être visible.
        Renvoie si oui ou non elle a été dessinée.

        Params:
        * screen (SurfaceType): l'écran sur lequel dessiner.
        * color: couleur de remplissage (par défaut, utilise la couleur du polygone).
        * width (int): épaisseur des contours (0 pour un polygone rempli)."""
        if self.visible() :
            self.draw_anyway(screen, color, width)
            return True
        return False
    
    def reset_info(self) -> None :
        """Recalcule les informations du polygone de la face."""
        self.polygone.reset_info(self.renderer)
        for button in self.buttons :
            button.reset_info(self.renderer)
        if not self.is_top :
            for line in self.lines:
                line.reset_info(self.renderer)

class Conseil :
    BOUTONS_FACE_1 = (4, 5, 8, 13, 14, 17)
    def __init__(self, boutons : list[Button]):
        self.active = False
        self.boutons = boutons
        self.action = 0

    def is_active(self) :
        return self.active
    
    def activate(self, action : int) :
        self.active = True
        self.action = action
    
    def desactivate(self) :
        self.active = False
    
    def draw_i(self, i : int) :
        self.boutons[i].hitbox.draw(screen, RED)

    def draw(self, screen, faces_visibles : list[int]) :
        if not self.is_active() :
            return
        if self.action < 18 :
            face_bouton = 1 if self.action in self.BOUTONS_FACE_1 else 0
            if face_bouton in faces_visibles :
                self.boutons[self.action].hitbox.draw(screen, RED)
        else :
            if 0 in faces_visibles :
                self.boutons[self.action].hitbox.draw(screen, RED, width=3)


class CubeUI:
    # Les points d'un carré
    DISPLACEMENT = ((0, 0), (1, 0), (1, 1), (0, 1))
    # Les définitions spécifiques des points 3D
    POINT_3D_PLACEMENT = (
        lambda i, j, da, db: Vector3(i - 1.5 + da,        - 1.5, 1.5 - j - db), # face 0
        lambda i, j, da, db: Vector3(i - 1.5 + da, j - 1.5 + db,        - 1.5), # face 1
        lambda i, j, da, db: Vector3(       - 1.5, 1.5 - i - da, 1.5 - j - db), # face 2
        lambda i, j, da, db: Vector3(i - 1.5 + da, 1.5 - j - db,          1.5), # face 3
        lambda i, j, da, db: Vector3(         1.5, i - 1.5 + da, 1.5 - j - db), # face 4
        lambda i, j, da, db: Vector3(1.5 - i - da,          1.5, 1.5 - j - db), # face 5
    )
    LINE_COLOR = WHITE
    FACE_COLOR = DARK_GREY
    TOP_FACE_COLOR = MIDDLE_GREY

    def __init__(self, cube: Cube, renderer: Renderer, side_length: float):
        """Initialise l'interface utilisateur pour manipuler un Rubik's Cube.

        Params:
        * cube (Cube): l'objet représentant le Rubik's Cube
        * renderer (Renderer): l'objet Renderer utilisé pour afficher le cube
        * side_length (float): la longueur d'un côté du cube"""
        self.cube = cube
        self.num = 0
        self.events_listener = EventsListener()
        self.renderer = renderer
        self.button_side_length = side_length / 3

        self.top_face_center = Vector3(0, 1.5, 0)
        self.top_face_normal = Vector3(0, 1, 0)
        self.top_face = [[None for _ in range(3)] for _ in range(3)]
        self.create_top_face()
        self.faces : list[Face] = []
        self.create_lines_and_faces()

        self.cube_cell_points = None
        self.create_cube_cell_points()

        self.create_turn_buttons()
        self.create_conseil()
    
    def create_conseil(self) :
        liste_boutons = []
        liste_boutons.append(self.faces[0].buttons[10])
        liste_boutons.append(self.faces[0].buttons[6])
        liste_boutons.append(self.faces[0].buttons[7])
        liste_boutons.append(self.faces[0].buttons[11])
        liste_boutons.append(self.faces[1].buttons[3])
        liste_boutons.append(self.faces[1].buttons[5])
        liste_boutons.append(self.faces[0].buttons[8])
        liste_boutons.append(self.faces[0].buttons[9])
        liste_boutons.append(self.faces[1].buttons[4])
        liste_boutons.append(self.faces[0].buttons[4])
        liste_boutons.append(self.faces[0].buttons[0])
        liste_boutons.append(self.faces[0].buttons[1])
        liste_boutons.append(self.faces[0].buttons[5])
        liste_boutons.append(self.faces[1].buttons[0])
        liste_boutons.append(self.faces[1].buttons[2])
        liste_boutons.append(self.faces[0].buttons[2])
        liste_boutons.append(self.faces[0].buttons[3])
        liste_boutons.append(self.faces[1].buttons[1])
        for i in range(3) :
            liste_boutons.extend(self.top_face[i])
        self.conseil = Conseil(liste_boutons)

    def reset_info(self, renderer: Renderer):
        """Met à jour les informations de rendu pour toutes les parties de l'interface utilisateur.

        Params:
        * renderer (Renderer): l'objet Renderer utilisé pour recalculer les coordonnées d'affichage"""
        for sub in self.top_face:
            for button in sub:
                button.reset_info(renderer)
        for face in self.faces:
            face.reset_info()

    def create_top_face(self):
        """Crée les boutons pour la face supérieure du cube."""
        def foo(x, y):
            def goo():
                print(f"Button ({x}, {y}) pressed !")
                self.events_listener.button_clicked = (x, y)
            return goo
        point_creation_function = self.POINT_3D_PLACEMENT[0]
        for j in range(3):
            for i in range(3):
                points = tuple(point_creation_function(i, j, da, db) * self.button_side_length
                               for da, db in self.DISPLACEMENT)
                polygon = ConvexPolygon3D(points, self.renderer, self.TOP_FACE_COLOR)
                button = Button(polygon, self.LINE_COLOR, 1)
                button.add_action(foo(i, j))
                self.top_face[j][i] = button

    def create_lines_and_faces(self):
        """Créer tous les objets 3D pour afficher le cube"""
        # Positions des lignes par rapport à la face
        lines_pos = (
            ((1, 0), (1, 3)),
            ((2, 0), (2, 3)),
            ((0, 1), (3, 1)),
            ((0, 2), (3, 2))
        )
        # Positions des coins dans chaque face
        faces_pos = ((0, 0), (3, 0), (3, 3), (0, 3))
        # Pour la face 0
        points = tuple(Vector3(-1.5 + 3 * da, -1.5, -1.5 + 3 * db) * self.button_side_length
                       for da, db in self.DISPLACEMENT)
        polygone = ConvexPolygon3D(points, self.renderer, self.LINE_COLOR)
        face = Face(polygone, 0, self.renderer)
        self.faces.append(face)
        for point_creation_function, i in zip(self.POINT_3D_PLACEMENT[1:], range(1, 6)):
            points = tuple(point_creation_function(i, j, 0, 0) * self.button_side_length for i, j in faces_pos)
            face = Face(ConvexPolygon3D(points, self.renderer, self.FACE_COLOR), i, self.renderer)
            face.set_lines(tuple(Line(point_creation_function(*p1, 0, 0) * self.button_side_length,
                                         point_creation_function(*p2, 0, 0) * self.button_side_length,
                                         self.renderer, self.LINE_COLOR, 1) for p1, p2 in lines_pos)) # Ajouts des lignes
            self.faces.append(face) # Ajouts des faces

    def create_cube_cell_points(self):
        """Crée les points des cellules du cube pour un rendu correct."""
        self.cube_cell_points = []
        for face in range(6):
            face_cells_points = []
            for j in range(3):
                column_cells_points = []
                for i in range(3):
                    column_cells_points.append(self.create_cell_points(face, i, j))
                face_cells_points.append(tuple(column_cells_points))
            self.cube_cell_points.append(tuple(face_cells_points))
        self.cube_cell_points = tuple(self.cube_cell_points)

    def create_cell_points(self, face_index: int, i: int, j: int):
        """Crée les coordonnées 3D d'une cellule précise

        Params:
        * face (int): l'indice de la face
        * i (int): son positionnement vertical sur la face (colonne)
        * j (int): son positionnement horizontal sur la face (ligne)"""
        shrink_factor: float = 0.6
        gap = (1 - shrink_factor) / 2
        point_creation_function = self.POINT_3D_PLACEMENT[face_index]
        points = tuple(point_creation_function(i, j, da * shrink_factor + gap, db * shrink_factor + gap)
                       * self.button_side_length for da, db in self.DISPLACEMENT)
        return points
    
    def create_turn_buttons(self):
        """Crée les boutons de rotation pour les faces du cube."""
        def foo(index):
            def goo():
                print(f"Rotation at button {index}")
                self.events_listener.turn_button_pressed = index
            return goo
        triangle_pos = ((0, 0), (0.5, 0.5), (0, 1))
        index = 0
        for m in (-1, 1) :
            inv = 1
            for d in range(3) :
                for face in (0, 5) :
                    show_area = tuple(self.POINT_3D_PLACEMENT[face](-1.5, d, 6 * da, db) * self.button_side_length for da, db in self.DISPLACEMENT)
                    triangle = tuple(self.POINT_3D_PLACEMENT[face](1.5 + 2 * m, d, da * m, db) * self.button_side_length for da, db in triangle_pos)
                    button = HiddenButton(ConvexPolygon3D(triangle, self.renderer, GREEN),
                                        ConvexPolygon3D(show_area, self.renderer, BLACK),
                                        GREEN, 2)
                    button.add_action(foo(index))
                    self.faces[face].add_button(button)
                index += 1
                for face in (0, 5) :
                    if face == 5 :
                        d = 2 -d
                    show_area = tuple(self.POINT_3D_PLACEMENT[face](d, -1.5, db, 6 * da) * self.button_side_length for da, db in self.DISPLACEMENT)
                    triangle = tuple(self.POINT_3D_PLACEMENT[face](d, 1.5 + 2 * m * inv, db, da * m * inv) * self.button_side_length for da, db in triangle_pos)
                    button = HiddenButton(ConvexPolygon3D(triangle, self.renderer, GREEN),
                                        ConvexPolygon3D(show_area, self.renderer, BLACK),
                                        GREEN, 2)
                    button.add_action(foo(index))
                    self.faces[face].add_button(button)
                    inv *= 1
                index += 1
            for d in range(3) :
                for face in (1, 3) :
                    if face == 1 :
                        j = d
                    else :
                        j = 2 - d
                    show_area = tuple(self.POINT_3D_PLACEMENT[face](-1.5, j, 6 * da, db) * self.button_side_length for da, db in self.DISPLACEMENT)
                    triangle = tuple(self.POINT_3D_PLACEMENT[face](1.5 + 2 * m * inv, j, da * m * inv, db) * self.button_side_length for da, db in triangle_pos)
                    button = HiddenButton(ConvexPolygon3D(triangle, self.renderer, GREEN),
                                        ConvexPolygon3D(show_area, self.renderer, BLACK),
                                        GREEN, 2)
                    button.add_action(foo(index))
                    self.faces[face].add_button(button)
                    inv *= -1
                for face in (2, 4) :
                    if face == 4 :
                        j = d
                    else :
                        j = 2 - d
                    show_area = tuple(self.POINT_3D_PLACEMENT[face](j, -1.5, db, 6 * da) * self.button_side_length for da, db in self.DISPLACEMENT)
                    triangle = tuple(self.POINT_3D_PLACEMENT[face](j, 1.5 + 2 * m * inv, db, da * m * inv) * self.button_side_length for da, db in triangle_pos)
                    button = HiddenButton(ConvexPolygon3D(triangle, self.renderer, GREEN),
                                        ConvexPolygon3D(show_area, self.renderer, BLACK),
                                        GREEN, 2)
                    button.add_action(foo(index))
                    self.faces[face].add_button(button)
                    inv *= -1
                index += 1

    def draw_cell(self, screen: SurfaceType, face: int, i: int, j: int):
        """Dessine une croix ou un rond pour une cellule précise

        Params:
        * screen (SurfaceType): la surface Pygame où sera dessiné la croix ou le rond
        * face (int): l'indice de la face
        * i (int): son positionnement vertical sur la face (colonne)
        * j (int): son positionnement horizontal sur la face (ligne)"""
        width: int = SCREEN_HEIGHT // 250
        pion = self.cube.get_pion((face, j, i))
        if pion == 0:
            return
        points = [self.renderer.screen_coordinates(point, True) for point in self.cube_cell_points[face][j][i]]
        if pion == 1:
            pygame.draw.line(screen, RED, points[0], points[2], width)
            pygame.draw.line(screen, RED, points[1], points[3], width)
        elif pion == -1:
            pygame.draw.polygon(screen, BLUE, points, width)

    def draw_face(self, screen: SurfaceType, face_index: int):
        """Dessine une face

        Params:
        * screen (SurfaceType): la surface Pygame où la face sera dessiné
        * face_index (int): l'indice de la face moins 1"""
        face = self.faces[face_index]
        if not face.draw(screen, self.LINE_COLOR, width=1) :
            return False
        for j in range(3):
            for i in range(3):
                self.draw_cell(screen, face_index, i, j)
        return True

    def draw_top_face(self, screen: SurfaceType, mouse: Vector2, click: bool):
        """Dessine la face du dessus du cube

        Params:
        * screen (SurfaceType): la surface Pygame où la face sera dessiné
        * mouse (tuple[int, int]): la position actuelle de la souris
        * click (bool): True si un clic est détecté"""
        if not self.faces[0].visible() :
            return False
        for j, sub in enumerate(self.top_face):
            for i, button in enumerate(sub):
                hovered = button.draw(screen, mouse, click)
                if hovered:
                    self.events_listener.button_hovered = (i, j)
                self.draw_cell(screen, 0, i, j)
        if self.events_listener.button_hovered != (-1, -1):
            i, j = self.events_listener.button_hovered
            button = self.top_face[j][i]
            button.draw(screen, mouse, False)
            self.draw_cell(screen, 0, i, j)
            if click:
                self.events_listener.button_clicked = (i, j)
        self.faces[0].draw_anyway(screen, width=3)
        return True

    def draw(self, screen: SurfaceType, mouse: Vector2, click: bool):
        """Dessine le cube, ses faces, et ses boutons.

        Params:
        * screen (SurfaceType): la surface Pygame où le cube sera dessiné
        * mouse (tuple[int, int]): la position actuelle de la souris
        * click (bool): True si un clic est détecté"""
        self.events_listener.reset()
        visible_faces : list[int] = []
        for face_index in range(5, -1, -1):
            if face_index == 0:
                if self.draw_top_face(screen, mouse, click) :
                    visible_faces.append(face_index)
            else:
                if self.draw_face(screen, face_index) :
                    visible_faces.append(face_index)
        for face_index in visible_faces:
            face = self.faces[face_index]
            if face.proportion_suffisante() :
                for button in face.buttons :
                    button.draw(screen, mouse, click)
        self.conseil.draw(screen, visible_faces)
        return visible_faces

class ToolbarButton(Button):
    '''
    Classe de style des boutons de la barre d'outils
    '''
    def __init__(self, pos, color, infos, border_color, border_width):
        """
        INPUTS
        - pos (tuple) : les points qui définissent le bouton
        - color (tuple) : la couleur du bouton
        - infos (str) : le texte affiché sur le bouton
        - border_color (int) : la couleur de la bordure
        - border_width (int) : la taille de la bordure
        """
        super().__init__(ConvexPolygon(pos, color), border_color, border_width)
        self.text = infos
        self.center = (0, 0)

    def display_text(self):
        """affiche le texte sur le bouton"""
        font = pygame.font.Font(None, 24)
        text = font.render(self.text, 1, (255, 255, 255), None)
        screen.blit(text, self.center)
    def hover(self):
        """change la couleur du bouton quand il est survolé"""
        self.hitbox.color -= (10, 10, 10)


def cinematique_debut_cube(screen: SurfaceType, clock,
                           cube_length: int = SCREEN_HEIGHT * math.pi,
                           camera_distance: float = 10.0,
                           time_length: float = 3.0,
                           number_of_rotations: float = 1.5) -> None | tuple[Camera, Renderer, Cube, CubeUI]:
    """Cinématique de lancement qui fait tourner le cube (c'est joli)"""
    frame_speed = lambda x: (2 * x - x ** 2) * 2 * math.pi * number_of_rotations - 1 * math.pi / 3
    frame_distance = lambda x: lerp2(10 * camera_distance, camera_distance, x)
    camera = Camera(latitude=math.radians(30), longitude=2 * math.pi / 3, distance=camera_distance)
    renderer = Renderer(screen_data=Vector2(SCREEN_WIDTH, SCREEN_HEIGHT), camera=camera)
    cube = Cube()
    cube_ui = CubeUI(cube=cube, renderer=renderer, side_length=cube_length)
    start_time = time.time()
    last_time = time.time()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
        pourcentage_time = (last_time - start_time) / time_length
        if pourcentage_time >= 1:
            camera.longitude = 2 * math.pi / 3
            camera.latitude = math.pi / 6
            camera.reset_position()
            renderer.reset()
            cube_ui.reset_info(renderer)
            break

        camera.longitude = frame_speed(pourcentage_time)
        camera.distance = frame_distance(pourcentage_time)
        camera.reset_position()
        renderer.reset()
        cube_ui.reset_info(renderer)

        screen.fill(BLACK)
        cube_ui.draw(screen, Vector2(pygame.mouse.get_pos()), False)
        pygame.display.flip()

        clock.tick(60)
        last_time = time.time()
    camera.distance = camera_distance

    return camera, renderer, cube, cube_ui

def go_position_initial(nb_frame : int = 120) :
    """fonction du bouton 'affichage base' qui replace le cube dans sa position initiale."""
    if camera.longitude == 2 * math.pi / 3 and camera.latitude == math.pi / 6 :
        return
    longitude_actuelle = cube_ui.renderer.camera.longitude
    latitude_actuelle = cube_ui.renderer.camera.latitude
    longitude_finale = 2 * math.pi / 3
    latitude_finale = math.pi / 6
    if longitude_actuelle > math.pi + longitude_finale :
        step_x = (longitude_finale + 2 * math.pi - longitude_actuelle) / nb_frame
    else :
        step_x = (longitude_finale - longitude_actuelle) / nb_frame
    step_y = (latitude_finale - latitude_actuelle) / nb_frame
    for i in range(nb_frame) :
        if i != nb_frame - 1 :
            coeff = 2 * (nb_frame - i) / nb_frame
            cube_ui.renderer.camera.longitude += step_x * coeff
            cube_ui.renderer.camera.latitude += step_y * coeff
        else :
            cube_ui.renderer.camera.longitude = longitude_finale
            cube_ui.renderer.camera.latitude = latitude_finale
        renderer.reset()
        cube_ui.reset_info(renderer)
        # Fill the screen with black
        screen.fill(BLACK)

        # Draw the cube
        cube_ui.draw(screen, Vector2(mouse_pos), False)
        bouton_reset_pos.draw(screen, Vector2(mouse_pos), False)
        bouton_conseil.draw(screen, Vector2(mouse_pos), False)
        pygame.display.flip()
        clock.tick(60)
    camera.reset_position()
    renderer.reset()
    cube_ui.reset_info(renderer)

def give_advise(agent : Agent, cube : Cube) :
    """fonction du bouton 'conseil' qui affiche les conseils de l'IA au joueur"""
    action = agent.choisir(cube, ia_player * -1, coup_interdit)
    print("Coup conseillé :", action)
    if 0 not in faces or 1 not in faces or not cube_ui.faces[1].proportion_suffisante():
        go_position_initial()
    cube_ui.conseil.activate(action)


ROTATION_TRANSLATOR = (10, 11, 15, 16, 9, 12, 4, 8, 5, 1, 2, 6, 7, 0, 3, 13, 17, 14)

def create_button_area():
    """Créé la barre d'actions"""
    points_toolbar = (Vector2(0, SCREEN_HEIGHT-150),
                    Vector2(SCREEN_WIDTH, SCREEN_HEIGHT-150),
                    Vector2(SCREEN_WIDTH, SCREEN_HEIGHT),
                    Vector2(0, SCREEN_HEIGHT))
    toolbar = ConvexPolygon(points_toolbar, (205, 205, 210))
    return toolbar


def create_shape_from_pos(pos_x, width=200):
    """Créé une forme de base de bouton à partir de la position x (y est toujours le même)."""
    pos_y = SCREEN_HEIGHT
    return (Vector2(pos_x, pos_y-140), Vector2(pos_x+width, pos_y-140), Vector2(pos_x+width, pos_y-10), Vector2(pos_x, pos_y-10))


if __name__ == "__main__":
    running = True

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    clock = pygame.time.Clock()

    lenght = SCREEN_HEIGHT * math.pi
    # Setup
    temp = cinematique_debut_cube(screen, clock, lenght)
    if temp is None:
        sys.exit()
    camera, renderer, cube, cube_ui = temp
    mouse_click = [0, 0]
    prev_mouse_x, prev_mouse_y = pygame.mouse.get_pos()
    player = 1
    ia_player = choice((1, -1))
    coup_interdit = -1
    fini = False
    agent = Agent(True)
    agent.model = load_model(MODEL_PATH)
    saver = GameSaver()

    toolbar = create_button_area()
    # Création du bouton pour revenir à la position initiale
    points = create_shape_from_pos(215)
    bouton_reset_pos = ToolbarButton(points, (0, 0, 255), 'Vue initiale', (255, 255, 255), 1)
    bouton_reset_pos.add_action(go_position_initial)

    # Création du bouton de conseil
    points = create_shape_from_pos(10)
    bouton_conseil = ToolbarButton(points, (0, 255, 0), 'Demander conseil', (255, 255, 255), 1)
    bouton_conseil.add_action(lambda : give_advise(agent, cube))

    # Création du bouton 'restart game'
    point = create_shape_from_pos(420)
    bouton_restart = ToolbarButton(point, (255, 0, 0), 'Restart', (255, 255, 255), 1)
    #bouton_restart.add_action()

    # Création du bouton 'quitter'
    points = create_shape_from_pos(SCREEN_WIDTH - 110, width=100)
    bouton_quitter = ToolbarButton(points, (255, 0, 0), 'Quitter', (255, 255, 255), 1)
    bouton_quitter.running = True
    def quit_game() :
        bouton_quitter.running = False
    bouton_quitter.add_action(quit_game)

    running = True

    while running :
        if not fini and player == ia_player :
            action = agent.choisir(cube_ui.cube, player, coup_interdit)
            cube_ui.cube.jouer(action, player)
            player *= -1
            if action < 18 :
                if action < 9 :
                    coup_interdit = action + 9
                else :
                    coup_interdit = action - 9
            else :
                coup_interdit = -1
            saver.save(cube.get_flatten_state())
            print("step was saved")
            if cube.terminal_state()[0]:
                fini = True
                saver.save_game()
        show_visible_face = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN :
                if event.key == pygame.K_RETURN :
                    show_visible_face = True
                elif event.key == pygame.K_r :
                    cube.reset()
                    fini = False
                    player = 1
                    ia_player = choice((1, -1))
                elif event.key == pygame.K_p :
                    camera.longitude = 0
                    camera.latitude = 0
                    renderer.reset()
                    cube_ui.reset_info(renderer)
                elif event.key == pygame.K_c :
                    cube_ui.cube.aleatoire()
                elif event.key == pygame.K_RIGHT:
                    cube_ui.num += 1
                    cube_ui.num %= 12
                    print(cube_ui.num)
                elif event.key == pygame.K_LEFT:
                    cube_ui.num -= 1
                    cube_ui.num %= 12
                    print(cube_ui.num)
                elif event.key == pygame.K_0 :
                    cube.jouer(2, 1)

        # Mouse detections
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        # Update mouse clicks
        for index in range(2):
            if mouse_buttons[2 * index]:
                mouse_click[index] += 1
            else:
                mouse_click[index] = 0

        # Check if the right mouse button is pressed
        if mouse_click[1] != 0:  # Right click is held down
            current_mouse_x, current_mouse_y = mouse_pos
            delta_x = (prev_mouse_x - current_mouse_x) * camera.orientation
            delta_y =  prev_mouse_y - current_mouse_y
            prev_mouse_x, prev_mouse_y = current_mouse_x, current_mouse_y

            camera.update_camera_from_mouse(delta_x, delta_y)
            renderer.reset()
            cube_ui.reset_info(renderer)
        else:
            prev_mouse_x, prev_mouse_y = mouse_pos
        change = False
        if cube_ui.events_listener.button_clicked != (-1, -1) and not fini :
            i, j = cube_ui.events_listener.button_clicked
            pion_string = "cross" if player == 1 else "circle"
            if cube.get_pion((0, j, i)) != 0:
                print(f"Can't place a {pion_string} there")
            else:
                print(f"A {pion_string} got placed at coordinates {(i, j)}")
                cube.set_pion((0, j, i), player)
                cube_ui.conseil.desactivate()
                player *= -1
                coup_interdit = -1
                change = True
        elif (rotation := cube_ui.events_listener.turn_button_pressed) != -1 and not fini:
            actual_rotation = ROTATION_TRANSLATOR[rotation]
            if actual_rotation == coup_interdit :
                print("Il s'agit d'un coup interdit. L'action a été annulée.")
            else :
                cube_ui.cube.jouer_tourner(actual_rotation)
                cube_ui.conseil.desactivate()
                print(f"Le joueur a décidé de tourner {actual_rotation} (originalement indice {rotation})")
                player *= -1
                if actual_rotation < 18 :
                    if actual_rotation < 9 :
                        coup_interdit = actual_rotation + 9
                    else :
                        coup_interdit = actual_rotation - 9
                change = True
        if change :
            saver.save(cube.get_flatten_state())
            print("step was saved")
            if cube.terminal_state()[0]:
                fini = True
                saver.save_game()

        # Fill the screen with black
        screen.fill(BLACK)

        # Draw the cube
        faces = cube_ui.draw(screen, Vector2(mouse_pos), mouse_click[0] == 1)
        toolbar.draw(screen)
        bouton_reset_pos.draw(screen, Vector2(mouse_pos), mouse_click[0] == 1)
        bouton_conseil.draw(screen, Vector2(mouse_pos), mouse_click[0] == 1)
        bouton_restart.draw(screen, Vector2(mouse_pos), mouse_click[0] == 1)
        bouton_quitter.draw(screen, Vector2(mouse_pos), mouse_click[0] == 1)
        running = bouton_quitter.running
        if show_visible_face:
            print(cube)
            print([index for index in faces])

        # Update the display
        pygame.display.flip()

        clock.tick(60)