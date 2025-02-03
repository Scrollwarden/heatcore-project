from __future__ import annotations
import math
import pygame, sys, os, pyautogui
from random import choice
import time
from pygame import Vector2, SurfaceType, Vector3
from agent import Agent
from tensorflow.keras.models import load_model  # type: ignore
from cube import Cube
from generators import GameSaver

# =============================
# CONSTANTS & UTILITY FUNCTIONS
# =============================
LINE_WIDTH = 3
SCREEN_WIDTH = pyautogui.size().width
SCREEN_HEIGHT = pyautogui.size().height

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


def point_in_triangle_barycentric(point: Vector2, triangle: tuple[Vector2, Vector2, Vector2]) -> bool:
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


# =============================
# CLASS DEFINITIONS
# =============================

class Camera:
    __slots__ = ['latitude', 'longitude', 'distance', 'position', 'orientation']

    def __init__(self, latitude: float, longitude: float, distance: float) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.distance = distance
        self.position = self.calculate_position()

    def reset_position(self):
        self.longitude %= 2 * math.pi
        self.position = self.calculate_position()

    def calculate_position(self) -> Vector3:
        self.orientation = self.calculate_orientation()
        x = self.distance * math.cos(self.latitude) * math.cos(self.longitude)
        y = self.distance * math.sin(self.latitude)
        z = self.distance * math.cos(self.latitude) * math.sin(self.longitude)
        return Vector3(x, y, z)

    def calculate_orientation(self) -> int:
        return 1 if -math.pi / 2 <= self.latitude <= math.pi / 2 else -1

    def update_camera_from_mouse(self, delta_x: float, delta_y: float,
                                 speed_horizontal: float = 0.025 * 0.25,
                                 speed_vertical: float = 0.025 * 0.25) -> None:
        self.longitude += delta_x * speed_horizontal
        self.latitude = (self.latitude - delta_y * speed_vertical + math.pi) % (2 * math.pi) - math.pi
        self.reset_position()

    def get_ij_data(self) -> tuple[Vector2, Vector2, Vector2]:
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
        self.ij_data: tuple[Vector2, Vector2, Vector2] | None = None
        self.screen_data = Vector2(screen_data.x // 2, screen_data.y // 2)
        self.camera = camera
        self.reset()

    def reset(self) -> None:
        self.camera.reset_position()
        self.ij_data = self.camera.get_ij_data()

    def screen_coordinates(self, point: Vector3, to_tuple: bool = False) -> Vector2 | tuple[float, float]:
        ij = sum((point[k] * self.ij_data[k] for k in range(3)), Vector2(0, 0))
        coordinates = self.screen_data + (ij * self.camera.orientation)
        if to_tuple:
            return coordinates.x, coordinates.y
        return coordinates


class Line:
    __slots__ = ['start', 'end', 'color', 'width', 'points_on_screen']

    def __init__(self, point1: Vector3, point2: Vector3, renderer: Renderer, color, width: int = 1):
        self.start = point1
        self.end = point2
        self.color = color
        self.width = width
        self.points_on_screen = None
        self.reset_info(renderer)

    def reset_info(self, renderer: Renderer):
        self.points_on_screen = (renderer.screen_coordinates(self.start),
                                 renderer.screen_coordinates(self.end))

    def draw(self, screen):
        pygame.draw.line(screen, self.color, *self.points_on_screen, width=self.width)


class EventsListener:
    def __init__(self):
        self.button_hovered: tuple[int, int] = (-1, -1)
        self.button_clicked: tuple[int, int] = (-1, -1)
        self.turn_button_pressed: int = -1

    def reset(self):
        self.button_hovered = (-1, -1)
        self.button_clicked = (-1, -1)
        self.turn_button_pressed = -1


class ConvexPolygon:
    __slots__ = ['points', 'minimum_corner', 'maximum_corner', 'color']

    def __init__(self, points: tuple[Vector2, ...], color):
        self.points = points
        self.minimum_corner = Vector2([min(point[k] for point in self.points) for k in range(2)])
        self.maximum_corner = Vector2([max(point[k] for point in self.points) for k in range(2)])
        self.color = color

    def lazy_rectangle_collision_check(self, point: Vector2) -> bool:
        return all(self.minimum_corner[k] <= point[k] <= self.maximum_corner[k] for k in range(2))

    def full_collision_check(self, point: Vector2) -> bool:
        if not self.lazy_rectangle_collision_check(point):
            return False
        for i in range(1, len(self.points) - 1):
            triangle = (self.points[0], self.points[i], self.points[i + 1])
            if point_in_triangle_barycentric(point, triangle):
                return True
        return False

    def draw(self, screen: SurfaceType, color=None, width: int = 0):
        pygame.draw.polygon(screen, color if color else self.color,
                            [(point.x, point.y) for point in self.points],
                            width=width)

    def draw_filled(self, screen: SurfaceType, color=None):
        pygame.draw.polygon(screen, color if color else self.color,
                            [(point.x, point.y) for point in self.points])

    def __repr__(self) -> str:
        return f"<ConvexPolygon{self.points}>"


class ConvexPolygon3D:
    __slots__ = ['points', 'points_screen_coordinates', 'minimum_corner', 'maximum_corner', 'color']

    def __init__(self, points: tuple[Vector3, ...], renderer: Renderer, color):
        self.points = points
        self.points_screen_coordinates: tuple[Vector2, ...] | None = None
        self.minimum_corner: Vector2 | None = None
        self.maximum_corner: Vector2 | None = None
        self.color = color
        self.reset_info(renderer)

    def reset_info(self, renderer: Renderer):
        self.points_screen_coordinates = tuple(renderer.screen_coordinates(point) for point in self.points)
        self.minimum_corner = Vector2([min(point[k] for point in self.points_screen_coordinates) for k in range(2)])
        self.maximum_corner = Vector2([max(point[k] for point in self.points_screen_coordinates) for k in range(2)])

    def lazy_rectangle_collision_check(self, point: Vector2) -> bool:
        return all(self.minimum_corner[k] <= point[k] <= self.maximum_corner[k] for k in range(2))

    def full_collision_check(self, point: Vector2) -> bool:
        if not self.lazy_rectangle_collision_check(point):
            return False
        for i in range(1, len(self.points) - 1):
            triangle = (self.points_screen_coordinates[0],
                        self.points_screen_coordinates[i],
                        self.points_screen_coordinates[i + 1])
            if point_in_triangle_barycentric(point, triangle):
                return True
        return False

    def draw(self, screen: SurfaceType, color=None, width: int = 0):
        pygame.draw.polygon(screen, color if color else self.color,
                            [(point.x, point.y) for point in self.points_screen_coordinates],
                            width=width)

    def draw_filled(self, screen: SurfaceType, color=None):
        pygame.draw.polygon(screen, color if color else self.color,
                            [(point.x, point.y) for point in self.points_screen_coordinates])

    def __repr__(self) -> str:
        return f"<ConvexPolygon3D{self.points}>"


class Button:
    __slots__ = ['hitbox', 'border_color', 'border_width', 'actions', 'running']

    def __init__(self, hitbox: ConvexPolygon3D | ConvexPolygon, border_color, border_width: int):
        self.hitbox = hitbox
        self.border_color = border_color
        self.border_width = border_width
        self.actions = []

    def reset_info(self, renderer: Renderer):
        if isinstance(self.hitbox, ConvexPolygon3D):
            self.hitbox.reset_info(renderer)

    def add_action(self, action):
        self.actions.append(action)

    def draw(self, screen: SurfaceType, mouse: tuple[int, int], click: bool) -> bool:
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
        return f"<Button{self.hitbox}>"


class HiddenButton(Button):
    __slots__ = ['hitbox', 'show_area', 'color', 'border_width', 'actions']

    def __init__(self, hitbox: ConvexPolygon3D, show_area: ConvexPolygon3D, color, border_width):
        super().__init__(hitbox, color, border_width)
        self.show_area = show_area

    def reset_info(self, renderer: Renderer):
        super().reset_info(renderer)
        self.show_area.reset_info(renderer)

    def draw(self, screen: SurfaceType, mouse: tuple[int, int], click: bool) -> tuple[bool, bool]:
        if not self.show_area.full_collision_check(mouse):
            return False, False
        return True, super().draw(screen, mouse, click)

    def __repr__(self) -> str:
        return f"<HiddenButton({self.hitbox}, {self.show_area})>"


class Face:
    DANS_PORTION = ((lambda camera: abs(camera.longitude - math.pi * 3 / 2) <= math.pi / 4,
                     lambda camera: abs(camera.longitude - math.pi / 2) <= math.pi / 4),
                    (lambda camera: abs(camera.longitude - math.pi) < math.pi / 4,
                     lambda camera: math.pi > abs(camera.longitude - math.pi) > math.pi * 3 / 4),
                    (lambda camera: abs(camera.longitude - math.pi / 2) <= math.pi / 4,
                     lambda camera: abs(camera.longitude - math.pi * 3 / 2) <= math.pi / 4),
                    (lambda camera: math.pi > abs(camera.longitude - math.pi) > math.pi * 3 / 4,
                     lambda camera: abs(camera.longitude - math.pi) < math.pi / 4))

    def __init__(self, polygone: ConvexPolygon3D, num: int, renderer: Renderer) -> None:
        self.polygone = polygone
        self.num = num
        self.is_top = num == 0
        self.renderer = renderer
        self.lines: tuple[Line] = ()
        self.buttons: list[HiddenButton] = []
        camera = self.renderer.camera
        if self.num == 1:
            self.fonction = lambda: (abs(camera.longitude - math.pi / 2) <= math.pi / 2) == (
                        abs(camera.latitude) <= math.pi / 2)
        elif self.num == 2:
            self.fonction = lambda: (abs(camera.longitude - math.pi) >= math.pi / 2) == (
                        abs(camera.latitude) <= math.pi / 2)
        elif self.num == 3:
            self.fonction = lambda: (abs(camera.longitude - math.pi / 2) >= math.pi / 2) == (
                        abs(camera.latitude) <= math.pi / 2)
        elif self.num == 4:
            self.fonction = lambda: (abs(camera.longitude - math.pi) <= math.pi / 2) == (
                        abs(camera.latitude) <= math.pi / 2)
        elif self.num == 5:
            self.fonction = lambda: camera.latitude < 0
        else:
            self.fonction = lambda: camera.latitude >= 0

    def proportion_suffisante(self):
        if self.num in (0, 5):
            return True
        if not self.visible():
            return False
        camera = self.renderer.camera
        avant = abs(camera.latitude) <= math.pi / 2
        return self.DANS_PORTION[self.num - 1][avant](camera)

    def add_button(self, button: HiddenButton) -> None:
        self.buttons.append(button)

    def set_lines(self, lines: tuple[Line]) -> None:
        self.lines = lines

    def visible(self) -> bool:
        return self.fonction()

    def draw_anyway(self, screen: SurfaceType, color=None, width: int = 0) -> None:
        if not self.is_top:
            self.polygone.draw_filled(screen)
            self.polygone.draw(screen, color, width)
            for line in self.lines:
                line.draw(screen)
        else:
            self.polygone.draw(screen, color, width)

    def draw(self, screen: SurfaceType, color=None, width: int = 0) -> bool:
        if self.visible():
            self.draw_anyway(screen, color, width)
            return True
        return False

    def reset_info(self) -> None:
        self.polygone.reset_info(self.renderer)
        for button in self.buttons:
            button.reset_info(self.renderer)
        if not self.is_top:
            for line in self.lines:
                line.reset_info(self.renderer)


class Conseil:
    BOUTONS_FACE_1 = (4, 5, 8, 13, 14, 17)

    def __init__(self, boutons: list[Button]):
        self.active = False
        self.boutons = boutons
        self.action = 0

    def is_active(self):
        return self.active

    def activate(self, action: int):
        self.active = True
        self.action = action

    def desactivate(self):
        self.active = False

    def draw_i(self, i: int):
        self.boutons[i].hitbox.draw(screen, RED)

    def draw(self, screen, faces_visibles: list[int]):
        if not self.is_active():
            return
        if self.action < 18:
            face_bouton = 1 if self.action in self.BOUTONS_FACE_1 else 0
            if face_bouton in faces_visibles:
                self.boutons[self.action].hitbox.draw(screen, RED)
        else:
            if 0 in faces_visibles:
                self.boutons[self.action].hitbox.draw(screen, RED, width=3)


class CubeUI:
    DISPLACEMENT = ((0, 0), (1, 0), (1, 1), (0, 1))
    POINT_3D_PLACEMENT = (
        lambda i, j, da, db: Vector3(i - 1.5 + da, -1.5, 1.5 - j - db),  # face 0
        lambda i, j, da, db: Vector3(i - 1.5 + da, j - 1.5 + db, -1.5),  # face 1
        lambda i, j, da, db: Vector3(-1.5, 1.5 - i - da, 1.5 - j - db),  # face 2
        lambda i, j, da, db: Vector3(i - 1.5 + da, 1.5 - j - db, 1.5),  # face 3
        lambda i, j, da, db: Vector3(1.5, i - 1.5 + da, 1.5 - j - db),  # face 4
        lambda i, j, da, db: Vector3(1.5 - i - da, 1.5, 1.5 - j - db),  # face 5
    )
    LINE_COLOR = WHITE
    FACE_COLOR = DARK_GREY
    TOP_FACE_COLOR = MIDDLE_GREY

    def __init__(self, cube: Cube, renderer: Renderer, side_length: float):
        self.cube = cube
        self.events_listener = EventsListener()
        self.renderer = renderer
        self.button_side_length = side_length / 3

        self.top_face_center = Vector3(0, 1.5, 0)
        self.top_face_normal = Vector3(0, 1, 0)
        self.top_face = [[None for _ in range(3)] for _ in range(3)]
        self.create_top_face()
        self.faces: list[Face] = []
        self.create_lines_and_faces()

        self.cube_cell_points = None
        self.create_cube_cell_points()

        self.create_turn_buttons()
        self.create_conseil()

    def create_conseil(self):
        liste_boutons = []
        liste_boutons.append(self.faces[0].buttons[10])
        liste_boutons.append(self.faces[0].buttons[6])
        liste_boutons.append(self.faces[0].buttons[7])
        liste_boutons.append(self.faces[0].buttons[11])
        liste_boutons.append(self.faces[1].buttons[0])
        liste_boutons.append(self.faces[1].buttons[2])
        liste_boutons.append(self.faces[0].buttons[8])
        liste_boutons.append(self.faces[0].buttons[9])
        liste_boutons.append(self.faces[1].buttons[1])
        liste_boutons.append(self.faces[0].buttons[4])
        liste_boutons.append(self.faces[0].buttons[0])
        liste_boutons.append(self.faces[0].buttons[1])
        liste_boutons.append(self.faces[0].buttons[5])
        liste_boutons.append(self.faces[1].buttons[3])
        liste_boutons.append(self.faces[1].buttons[5])
        liste_boutons.append(self.faces[0].buttons[2])
        liste_boutons.append(self.faces[0].buttons[3])
        liste_boutons.append(self.faces[1].buttons[4])
        for i in range(3):
            liste_boutons.extend(self.top_face[i])
        self.conseil = Conseil(liste_boutons)

    def reset_info(self):
        for sub in self.top_face:
            for button in sub:
                button.reset_info(self.renderer)
        for face in self.faces:
            face.reset_info()

    def create_top_face(self):
        def foo(x, y):
            def goo():
                print(f"Button ({x}, {y}) pressed!")
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
        lines_pos = (
            ((1, 0), (1, 3)),
            ((2, 0), (2, 3)),
            ((0, 1), (3, 1)),
            ((0, 2), (3, 2))
        )
        faces_pos = ((0, 0), (3, 0), (3, 3), (0, 3))
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
                                      self.renderer, self.LINE_COLOR, 1) for p1, p2 in lines_pos))
            self.faces.append(face)

    def create_cube_cell_points(self):
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
        shrink_factor: float = 0.6
        gap = (1 - shrink_factor) / 2
        point_creation_function = self.POINT_3D_PLACEMENT[face_index]
        points = tuple(point_creation_function(i, j, da * shrink_factor + gap, db * shrink_factor + gap)
                       * self.button_side_length for da, db in self.DISPLACEMENT)
        return points

    def create_turn_buttons(self):
        def foo(index):
            def goo():
                print(f"Rotation at button {index}")
                self.events_listener.turn_button_pressed = index

            return goo

        triangle_pos = ((0, 0), (0.5, 0.5), (0, 1))
        index = 0
        for m in (-1, 1):
            inv = 1
            for d in range(3):
                for face in (0, 5):
                    show_area = tuple(
                        self.POINT_3D_PLACEMENT[face](-1.5, d, 6 * da, db) * self.button_side_length for da, db in
                        self.DISPLACEMENT)
                    triangle = tuple(
                        self.POINT_3D_PLACEMENT[face](1.5 + 2 * m, d, da * m, db) * self.button_side_length for da, db
                        in triangle_pos)
                    button = HiddenButton(ConvexPolygon3D(triangle, self.renderer, GREEN),
                                          ConvexPolygon3D(show_area, self.renderer, BLACK),
                                          GREEN, 2)
                    button.add_action(foo(index))
                    self.faces[face].add_button(button)
                index += 1
                for face in (0, 5):
                    if face == 5:
                        d = 2 - d
                    show_area = tuple(
                        self.POINT_3D_PLACEMENT[face](d, -1.5, db, 6 * da) * self.button_side_length for da, db in
                        self.DISPLACEMENT)
                    triangle = tuple(
                        self.POINT_3D_PLACEMENT[face](d, 1.5 + 2 * m * inv, db, da * m * inv) * self.button_side_length
                        for da, db in triangle_pos)
                    button = HiddenButton(ConvexPolygon3D(triangle, self.renderer, GREEN),
                                          ConvexPolygon3D(show_area, self.renderer, BLACK),
                                          GREEN, 2)
                    button.add_action(foo(index))
                    self.faces[face].add_button(button)
                    inv *= 1
                index += 1
            for d in range(3):
                for face in (1, 3):
                    if face == 1:
                        j = d
                    else:
                        j = 2 - d
                    show_area = tuple(
                        self.POINT_3D_PLACEMENT[face](-1.5, j, 6 * da, db) * self.button_side_length for da, db in
                        self.DISPLACEMENT)
                    triangle = tuple(
                        self.POINT_3D_PLACEMENT[face](1.5 + 2 * m * inv, j, da * m * inv, db) * self.button_side_length
                        for da, db in triangle_pos)
                    button = HiddenButton(ConvexPolygon3D(triangle, self.renderer, GREEN),
                                          ConvexPolygon3D(show_area, self.renderer, BLACK),
                                          GREEN, 2)
                    button.add_action(foo(index))
                    self.faces[face].add_button(button)
                    inv *= -1
                for face in (2, 4):
                    if face == 4:
                        j = d
                    else:
                        j = 2 - d
                    show_area = tuple(
                        self.POINT_3D_PLACEMENT[face](j, -1.5, db, 6 * da) * self.button_side_length for da, db in
                        self.DISPLACEMENT)
                    triangle = tuple(
                        self.POINT_3D_PLACEMENT[face](j, 1.5 + 2 * m * inv, db, da * m * inv) * self.button_side_length
                        for da, db in triangle_pos)
                    button = HiddenButton(ConvexPolygon3D(triangle, self.renderer, GREEN),
                                          ConvexPolygon3D(show_area, self.renderer, BLACK),
                                          GREEN, 2)
                    button.add_action(foo(index))
                    self.faces[face].add_button(button)
                    inv *= -1
                index += 1

    def draw_cell(self, screen: SurfaceType, face: int, i: int, j: int):
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
        face = self.faces[face_index]
        if not face.draw(screen, self.LINE_COLOR, width=1):
            return False
        for j in range(3):
            for i in range(3):
                self.draw_cell(screen, face_index, i, j)
        return True

    def draw_top_face(self, screen: SurfaceType, mouse: Vector2, click: bool):
        if not self.faces[0].visible():
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
        self.events_listener.reset()
        visible_faces: list[int] = []
        for face_index in range(5, -1, -1):
            if face_index == 0:
                if self.draw_top_face(screen, mouse, click):
                    visible_faces.append(face_index)
            else:
                if self.draw_face(screen, face_index):
                    visible_faces.append(face_index)
        for face_index in visible_faces:
            face = self.faces[face_index]
            if face.proportion_suffisante():
                for button in face.buttons:
                    button.draw(screen, mouse, click)
        self.conseil.draw(screen, visible_faces)
        return visible_faces


class ToolbarButton(Button):
    def __init__(self, pos, color, infos, border_color, border_width):
        super().__init__(ConvexPolygon(pos, color), border_color, border_width)
        self.text = infos
        self.center = (0, 0)

    def display_text(self):
        font = pygame.font.Font(None, 24)
        text = font.render(self.text, 1, (255, 255, 255), None)
        screen.blit(text, self.center)

    def hover(self):
        self.hitbox.color = tuple(max(0, c - 10) for c in self.hitbox.color)


# =============================
# END OF CLASS DEFINITIONS
# =============================

ROTATION_TRANSLATOR = (10, 11, 15, 16, 9, 12, 4, 8, 5, 1, 2, 6, 7, 0, 3, 13, 17, 14)


def create_button_area():
    points_toolbar = (Vector2(0, SCREEN_HEIGHT - 150),
                      Vector2(SCREEN_WIDTH, SCREEN_HEIGHT - 150),
                      Vector2(SCREEN_WIDTH, SCREEN_HEIGHT),
                      Vector2(0, SCREEN_HEIGHT))
    toolbar = ConvexPolygon(points_toolbar, (205, 205, 210))
    return toolbar


def create_shape_from_pos(pos_x, width=200):
    pos_y = SCREEN_HEIGHT
    return (Vector2(pos_x, pos_y - 140), Vector2(pos_x + width, pos_y - 140),
            Vector2(pos_x + width, pos_y - 10), Vector2(pos_x, pos_y - 10))


def cinematique_debut_cube(screen: SurfaceType, clock,
                           cube_length: int = SCREEN_HEIGHT * math.pi,
                           camera_distance: float = 10.0,
                           time_length: float = 3.0,
                           number_of_rotations: float = 1.5) -> None | tuple[Camera, Renderer, Cube, CubeUI]:
    start_time = time.time()
    last_time = time.time()
    camera = Camera(latitude=math.radians(30), longitude=2 * math.pi / 3, distance=camera_distance)
    renderer = Renderer(screen_data=Vector2(SCREEN_WIDTH, SCREEN_HEIGHT), camera=camera)
    cube = Cube()
    cube_ui = CubeUI(cube=cube, renderer=renderer, side_length=cube_length)
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
            cube_ui.reset_info()
            break
        camera.longitude = (2 * pourcentage_time - pourcentage_time ** 2) * 2 * math.pi * number_of_rotations - (
                    math.pi / 3)
        camera.distance = (10 * camera_distance - (10 * camera_distance - camera_distance) * (
                    2 * pourcentage_time - pourcentage_time ** 2))
        camera.reset_position()
        renderer.reset()
        cube_ui.reset_info()
        screen.fill(BLACK)
        cube_ui.draw(screen, Vector2(pygame.mouse.get_pos()), False)
        pygame.display.flip()
        clock.tick(60)
        last_time = time.time()
    camera.distance = camera_distance
    return camera, renderer, cube, cube_ui


def go_position_initial(nb_frame: int = 120):
    if camera.longitude == 2 * math.pi / 3 and camera.latitude == math.pi / 6:
        return
    longitude_actuelle = cube_ui.renderer.camera.longitude
    latitude_actuelle = cube_ui.renderer.camera.latitude
    longitude_finale = 2 * math.pi / 3
    latitude_finale = math.pi / 6
    if longitude_actuelle > math.pi + longitude_finale:
        step_x = (longitude_finale + 2 * math.pi - longitude_actuelle) / nb_frame
    else:
        step_x = (longitude_finale - longitude_actuelle) / nb_frame
    step_y = (latitude_finale - latitude_actuelle) / nb_frame
    for i in range(nb_frame):
        if i != nb_frame - 1:
            coeff = 2 * (nb_frame - i) / nb_frame
            cube_ui.renderer.camera.longitude += step_x * coeff
            cube_ui.renderer.camera.latitude += step_y * coeff
        else:
            cube_ui.renderer.camera.longitude = longitude_finale
            cube_ui.renderer.camera.latitude = latitude_finale
        renderer.reset()
        cube_ui.reset_info()
        screen.fill(BLACK)
        cube_ui.draw(screen, Vector2(pygame.mouse.get_pos()), False)
        pygame.display.flip()
        clock.tick(60)
    camera.reset_position()
    renderer.reset()
    cube_ui.reset_info()


def give_advise(agent: Agent, cube: Cube):
    action = agent.choisir(cube, ia_player * -1, coup_interdit)
    print("Hint advised:", action)
    if cube_ui.conseil:
        cube_ui.conseil.activate(action)


# =============================
# MAIN PROGRAM
# =============================
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    lenght = SCREEN_HEIGHT * math.pi
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
    agent.model = load_model(
        os.path.join(os.path.abspath(__file__).rstrip("cube_ui.py"), f"models/generation1/model1.h5"))
    saver = GameSaver()

    # ---------------------------
    # UI3 Integration
    # ---------------------------
    # Import the new HUD classes from hud_elements.py
    from new_engine import hud_elements


    def reset_view_action():
        go_position_initial()


    def reset_game_action():
        cube.reset()
        print("Game reset!")


    def hint_action():
        give_advise(agent, cube)


    def close_ui_action():
        nonlocal_ui_flags["ui3_active"] = False
        print("Closing HUD (UI3) and returning to UI1.")


    def open_ui3_1_action():
        nonlocal_ui_flags["ui3_active"] = False
        nonlocal_ui_flags["ui3_1"] = hud_elements.UI3_1(screen, on_next=lambda: reopen_ui3())
        print("Opening UI3-1.")


    def reopen_ui3():
        nonlocal_ui_flags["ui3_active"] = True
        nonlocal_ui_flags["ui3_1"] = None
        print("Returning from UI3-1 to HUD (UI3).")


    nonlocal_ui_flags = {"ui3_active": True, "ui3_1": None}
    ui3 = hud_elements.UI3(screen, reset_view_action, reset_game_action, hint_action, close_ui_action, open_ui3_1_action)
    nonlocal_ui_flags["ui3_1"] = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Process UI3 events if active.
            if nonlocal_ui_flags["ui3_active"]:
                ui3.handle_event(event)
            # Process UI3_1 events if active.
            if nonlocal_ui_flags["ui3_1"] and nonlocal_ui_flags["ui3_1"].active:
                nonlocal_ui_flags["ui3_1"].handle_event(event)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    cube.reset()
                    fini = False
                    player = 1
                    ia_player = choice((1, -1))
                elif event.key == pygame.K_c:
                    cube.aleatoire()
                elif event.key == pygame.K_RIGHT:
                    cube_ui.num = (cube_ui.num + 1) % 12
                    print(cube_ui.num)
                elif event.key == pygame.K_LEFT:
                    cube_ui.num = (cube_ui.num - 1) % 12
                    print(cube_ui.num)
                elif event.key == pygame.K_0:
                    cube.jouer(2, 1)
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        for index in range(2):
            if mouse_buttons[2 * index]:
                mouse_click[index] += 1
            else:
                mouse_click[index] = 0
        if mouse_click[1] != 0:
            current_mouse_x, current_mouse_y = mouse_pos
            delta_x = (prev_mouse_x - current_mouse_x) * camera.orientation
            delta_y = prev_mouse_y - current_mouse_y
            prev_mouse_x, prev_mouse_y = current_mouse_x, current_mouse_y
            camera.update_camera_from_mouse(delta_x, delta_y)
            renderer.reset()
            cube_ui.reset_info()
        else:
            prev_mouse_x, prev_mouse_y = mouse_pos
        change = False
        if cube_ui.events_listener.button_clicked != (-1, -1) and not fini:
            i, j = cube_ui.events_listener.button_clicked
            pion_string = "cross" if player == 1 else "circle"
            if cube.get_pion((0, j, i)) != 0:
                print(f"Can't place a {pion_string} there")
            else:
                print(f"A {pion_string} got placed at {(i, j)}")
                cube.set_pion((0, j, i), player)
                cube_ui.conseil.desactivate()
                player *= -1
                coup_interdit = -1
                change = True
        elif (rotation := cube_ui.events_listener.turn_button_pressed) != -1 and not fini:
            actual_rotation = ROTATION_TRANSLATOR[rotation]
            if actual_rotation == coup_interdit:
                print("Move forbidden; action canceled.")
            else:
                cube_ui.cube.jouer_tourner(actual_rotation)
                cube_ui.conseil.desactivate()
                print(f"Rotation {actual_rotation} executed")
                player *= -1
                if actual_rotation < 18:
                    if actual_rotation < 9:
                        coup_interdit = actual_rotation + 9
                    else:
                        coup_interdit = actual_rotation - 9
                change = True
        if change:
            saver.save(cube.get_flatten_state())
            print("Step saved")
            if cube.terminal_state()[0]:
                fini = True
                saver.save_game()
        screen.fill(BLACK)
        faces = cube_ui.draw(screen, Vector2(mouse_pos), mouse_buttons[0] == 1)
        if nonlocal_ui_flags["ui3_active"]:
            ui3.draw()
        if nonlocal_ui_flags["ui3_1"] and nonlocal_ui_flags["ui3_1"].active:
            nonlocal_ui_flags["ui3_1"].draw()
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
