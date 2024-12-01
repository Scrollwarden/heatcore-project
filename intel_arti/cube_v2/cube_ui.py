import pygame, sys
from pygame import Vector2, SurfaceType, Vector3
from cube import Cube
import math

LINE_WIDTH = 3
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500
ZOOM = 3

# Colors
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 220, 0)
BLUE = (0, 128, 255)
ORANGE = (255, 128, 0)
YELLOW = (255, 255, 0)
GREY = (200, 200, 200)
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

# Barycentric approach
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
    inv_denom = 1 / (dot00 * dot11 - dot01 * dot01)
    u = (dot11 * dot02 - dot01 * dot12) * inv_denom
    v = (dot00 * dot12 - dot01 * dot02) * inv_denom
    return u >= 0 and v >= 0 and (u + v) <= 1

class Camera:
    def __init__(self, latitude: float, longitude: float, distance: float) -> None:
        """
        Initializes the camera rotating around the origin.
        :param latitude: The latitude angle in radians (vertical rotation).
        :param longitude: The longitude angle in radians (horizontal rotation).
        :param distance: The distance from the origin.
        """
        self.latitude = latitude
        self.longitude = longitude
        self.distance = distance
        self.position = self.calculate_position()

    def reset_position(self):
        self.longitude %= 2 * math.pi
        self.position = self.calculate_position()

    def calculate_position(self) -> Vector3:
        """
        Calculates the camera's position based on latitude, longitude, and distance.
        :return: A Vector3 representing the camera's position.
        """
        x = self.distance * math.cos(self.latitude) * math.cos(self.longitude)
        y = self.distance * math.sin(self.latitude)
        z = self.distance * math.cos(self.latitude) * math.sin(self.longitude)
        return Vector3(x, y, z)

    def update_camera_from_mouse(self, delta_x, delta_y, speed_horizontal=0.05, speed_vertical=0.05):
        # Update longitude based on horizontal mouse movement
        self.longitude += delta_x * speed_horizontal
        # Update latitude based on vertical mouse movement, limiting the range
        self.latitude = min(math.pi / 2, max(-math.pi / 2, self.latitude - delta_y * speed_vertical))
        self.reset_position()

    def get_ij_data(self) -> tuple[Vector2, Vector2, Vector2]:
        """
        Calculates the screen coordinates of the world points (1, 0, 0), (0, 1, 0), (0, 0, 1)
        as seen by the camera.
        :return: A tuple of Vector2 representing the screen coordinates.
        """
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

            x_proj = relative_point.dot(right)
            y_proj = relative_point.dot(up)

            transformed_points.append(Vector2(x_proj, y_proj))

        return tuple(transformed_points)


class Renderer:
    __slots__ = ['ij_data', 'screen_data', 'camera']

    def __init__(self, camera: Camera, screen_data: Vector2) -> None:
        """
        Initializes the Renderer.
        :param screen_data: The screen resolution as a Vector2.
        :param camera: The Camera object.
        """
        self.ij_data: tuple[Vector2, Vector2, Vector2] | None = None
        self.screen_data = Vector2(screen_data.x // 2, screen_data.y // 2)
        self.camera = camera
        self.reset()

    def reset(self) -> None:
        """
        Updates the `ij_data` based on the camera's current orientation.
        :param camera: The Camera object.
        """
        self.camera.reset_position()
        self.ij_data = self.camera.get_ij_data()

    def screen_coordinates(self, point: Vector3, to_tuple: bool = False) -> Vector2 | tuple[float, float]:
        """
        Projects a 3D point onto the screen considering the camera's orientation.
        :param point: A 3D point in world space as a Vector3.
        :param to_tuple: Whether to return the coordinates as a tuple.
        :return: The screen-space coordinates as a Vector2 or tuple.
        """
        ij = sum((point[k] * self.ij_data[k] for k in range(3)), Vector2(0, 0))
        coordinates = self.screen_data + ZOOM * ij
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

    def lazy_rectangle_collision_check(self, point: Vector2):
        return all(self.minimum_corner[k] <= point[k] <= self.maximum_corner[k] for k in range(2))

    def full_collision_check(self, point: Vector2):
        if not self.lazy_rectangle_collision_check(point):
            return False
        for i in range(1, len(self.points) - 1):
            triangle = (self.points_screen_coordinates[0],
                        self.points_screen_coordinates[i],
                        self.points_screen_coordinates[i + 1])
            if point_in_triangle_barycentric(point, triangle):
                return True
        return False

    def draw(self, screen: SurfaceType, color = None, width = 0):
        pygame.draw.polygon(screen, color if color else self.color,
                            [(point.x, point.y) for point in self.points_screen_coordinates],
                            width=width)

    def draw_filled(self, screen: SurfaceType, color = None):
        pygame.draw.polygon(screen, color if color else self.color,
                            [(point.x, point.y) for point in self.points_screen_coordinates])

class Button:
    __slots__ = ['hitbox', 'border_color', 'border_width', 'actions']

    def __init__(self, hitbox: ConvexPolygon3D, border_color, border_width):
        self.hitbox = hitbox
        self.border_color = border_color
        self.border_width = border_width
        self.actions = []

    def reset_info(self, renderer: Renderer):
        self.hitbox.reset_info(renderer)

    def add_action(self, action):
        self.actions.append(action)

    def draw(self, screen, mouse, click: bool):
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


class HiddenButton(Button):
    __slots__ = ['hitbox', 'show_area', 'color', 'border_width', 'actions']

    def __init__(self, hitbox: ConvexPolygon3D, show_area: ConvexPolygon3D, color, border_width):
        super().__init__(hitbox, color, border_width)
        self.show_area = show_area

    def draw(self, screen, mouse, click):
        if not self.show_area.full_collision_check(mouse):
            return
        super().draw(screen, mouse, click)

class EventsListener:
    def __init__(self):
        self.button_coordinates: tuple[int, int] = (-1, -1)
        self.button_hovered: bool = False
        self.button_clicked: bool = False

    def reset(self):
        self.button_coordinates = (-1, -1)
        self.button_hovered = False
        self.button_clicked = False

class CubeUI:
    DISPLACEMENT = ((0, 0), (1, 0), (1, 1), (0, 1))
    POINT_3D_PLACEMENT = (
        lambda i, j, da, db: Vector3(i - 1.5 + da,        - 1.5, 0.5 - j + db), # face 0
        lambda i, j, da, db: Vector3(i - 1.5 + da, 0.5 - j + db,        - 1.5), # face 1
        lambda i, j, da, db: Vector3(         1.5, i - 1.5 - da, 0.5 - j + db), # face 2
        lambda i, j, da, db: Vector3(i - 1.5 + da, j - 1.5 - db,          1.5), # face 3
        lambda i, j, da, db: Vector3(         1.5, 0.5 - i + da, 0.5 - j + db), # face 4
        lambda i, j, da, db: Vector3(1.5 - i - da,          1.5, 0.5 - j + db), # face 5
    )
    LINE_COLOR = WHITE
    FACE_COLOR = DARK_GREY

    def __init__(self, cube: Cube, renderer: Renderer, side_length: float):
        self.cube = cube
        self.events_listener = EventsListener()
        self.renderer = renderer
        self.button_side_length = side_length / 3

        self.top_face_center = Vector3(0, 1.5, 0)
        self.top_face_normal = Vector3(0, 1, 0)
        self.top_face = [[None for _ in range(3)] for _ in range(3)]
        self.top_face_creation()
        self.lines = []
        self.faces = []
        self.lines_and_faces()

        self.cube_cell_points = None
        self.reset_cube_cell_points()

        self.turn_buttons = []
        self.reset_turn_buttons()

    def reset_info(self, renderer: Renderer):
        for sub in self.top_face:
            for button in sub:
                button.reset_info(renderer)
        for face_lines in self.lines:
            for line in face_lines:
                line.reset_info(renderer)
        for face in self.faces:
            face.reset_info(renderer)

    def top_face_creation(self):
        """Créer tous les boutons qui composent la face du dessus, ce qui veut dire là où le joueur peut placer un pion"""
        def foo(x, y):
            def goo():
                print(f"Button ({x}, {y}) pressed !")
            return goo
        for j in range(3):
            for i in range(3):
                points = tuple(Vector3(i - 1.5 + da, -1.5, 0.5 - j + db) * self.button_side_length
                               for da, db in self.DISPLACEMENT)
                polygon = ConvexPolygon3D(points, self.renderer, self.FACE_COLOR)
                button = Button(polygon, self.LINE_COLOR, 1)
                button.add_action(foo(i, j))
                self.top_face[j][i] = button

    def lines_and_faces(self):
        """Créer tous les objets 3D pour afficher le cube"""
        # Fonction qui renvoie un coin en 3D de chaque face
        point_creation_functions = (
            #lambda i, j: Vector3(  i, -1.5,    j) * self.button_side_length, # face 0
            lambda i, j: Vector3(   i,    j,  1.5) * self.button_side_length, # face 1
            lambda i, j: Vector3(-1.5,    i,    j) * self.button_side_length, # face 2
            lambda i, j: Vector3(   i,    j, -1.5) * self.button_side_length, # face 3
            lambda i, j: Vector3( 1.5,    i,    j) * self.button_side_length, # face 4
            lambda i, j: Vector3(   i,  1.5,    j) * self.button_side_length, # face 5
        )
        # Positions des lignes par rapport à la face
        lines_pos = ((-1.5, -1.5, 1.5, -1.5), (1.5, -1.5, 1.5, 1.5), (1.5, 1.5, -1.5, 1.5), (-1.5, 1.5, -1.5, -1.5),
                     (-0.5, -1.5, -0.5, 1.5), (0.5, -1.5, 0.5, 1.5), (-1.5, -0.5, 1.5, -0.5), (-1.5, 0.5, 1.5, 0.5))
        # Positions des coins dans chaque face
        faces_pos = ((-1.5, -1.5), (1.5, -1.5), (1.5, 1.5), (-1.5, 1.5))
        for point_creation_function in point_creation_functions:
            self.lines.append(tuple(Line(point_creation_function(i, j), point_creation_function(m, n),
                                         self.renderer, self.LINE_COLOR, 1) for i, j, m, n in lines_pos)) # Ajouts des lignes
            points = tuple(point_creation_function(i, j) for i, j in faces_pos)
            self.faces.append(ConvexPolygon3D(points, self.renderer, self.FACE_COLOR)) # Ajouts des faces

    def reset_cube_cell_points(self):
        self.cube_cell_points = []
        for face in range(6):
            face_cells_points = []
            for j in range(3):
                column_cells_points = []
                for i in range(3):
                    column_cells_points.append(self.cell_points(face, i, j))
                face_cells_points.append(tuple(column_cells_points))
            self.cube_cell_points.append(tuple(face_cells_points))
        self.cube_cell_points = tuple(self.cube_cell_points)

    def cell_points(self, face_index: int, i: int, j: int):
        shrink_factor: float = 0.6
        gap = (1 - shrink_factor) / 2
        point_creation_function = self.POINT_3D_PLACEMENT[face_index]
        points = tuple(point_creation_function(i, j, da * shrink_factor + gap, db * shrink_factor + gap)
                       * self.button_side_length for da, db in self.DISPLACEMENT)
        print(face_index, i, j, points)
        return points

    def reset_turn_buttons(self):
        def foo(index):
            def goo():
                print(f"Rotation at button {index}")
            return goo
        triangle_pos = ((0, 0), (0.5, 0.5), (0, 1))
        index = 0
        top_face_creation = self.POINT_3D_PLACEMENT[0]
        for m in (-1, 1):
            for j in range(3):
                show_area = tuple(top_face_creation(2 * m, j, 4 * da, db) for da, db in self.DISPLACEMENT)
                triangle = tuple(top_face_creation(2 * m, j, da, db) for da, db in triangle_pos)
                button = HiddenButton(ConvexPolygon3D(triangle, self.renderer, GREEN),
                                      ConvexPolygon3D(show_area, self.renderer, BLACK),
                                      GREEN, 2)
                button.add_action(foo(index))
                self.turn_buttons.append(button)
                index += 1

    def draw_cell(self, screen: SurfaceType, face: int, i: int, j: int):
        width: int = 2
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
        lines = self.lines[face_index]
        face.draw(screen)
        for line in lines:
            line.draw(screen)
        for j in range(3):
            for i in range(3):
                self.draw_cell(screen, face_index + 1, i, j)

    def draw_top_face(self, screen: SurfaceType, mouse: Vector2, click: bool):
        for j, sub in enumerate(self.top_face):
            for i, button in enumerate(sub):
                hovered = button.draw(screen, mouse, click)
                if hovered:
                    self.events_listener.button_hovered = True
                    self.events_listener.button_coordinates = (i, j)
                self.draw_cell(screen, 0, i, j)
        if self.events_listener.button_hovered:
            i, j = self.events_listener.button_coordinates
            button = self.top_face[j][i]
            button.draw(screen, mouse, False)
            self.draw_cell(screen, 0, i, j)
            if click:
                self.events_listener.button_clicked = True

    def face_visible(self, face_index: int):
        if face_index == 0:
            return abs(self.renderer.camera.longitude - math.pi / 2) > math.pi / 2
        elif face_index == 1:
            return abs(self.renderer.camera.longitude - math.pi) > math.pi / 2
        elif face_index == 2:
            return abs(self.renderer.camera.longitude - math.pi / 2) < math.pi / 2
        elif face_index == 3:
            return abs(self.renderer.camera.longitude - math.pi) < math.pi / 2
        elif face_index == 4:
            return self.renderer.camera.latitude < 0

    def top_face_visible(self):
        return self.renderer.camera.latitude > 0

    def draw(self, screen: SurfaceType, mouse: Vector2, click: bool):
        """
        Draws the entire cube, including top face and visible faces.
        :param screen: The Pygame surface to draw on.
        :param mouse: The current mouse position as a Vector2.
        :param click: Whether the mouse is clicked.
        """
        self.events_listener.reset()
        visible_faces = [index for index in range(5) if self.face_visible(index)] + ([-1] if self.top_face_visible() else []) # -1 for top face
        # Sort faces by depth (distance to camera)
        visible_faces
        for face_index in visible_faces:
            if face_index == -1:
                self.draw_top_face(screen, mouse, click)
            else:
                self.draw_face(screen, face_index)



if __name__ == "__main__":

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # Setup
    camera = Camera(latitude=math.radians(45), longitude=math.radians(30), distance=10)
    renderer = Renderer(screen_data=Vector2(800, 600), camera=camera)
    cube = Cube()
    cube_ui = CubeUI(cube, renderer, 50)
    mouse_click = [0, 0]
    prev_mouse_x, prev_mouse_y = pygame.mouse.get_pos()
    player = 1

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

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
            delta_x = current_mouse_x - prev_mouse_x
            delta_y = current_mouse_y - prev_mouse_y
            prev_mouse_x, prev_mouse_y = current_mouse_x, current_mouse_y

            camera.update_camera_from_mouse(delta_x, delta_y)
            renderer.reset()
            cube_ui.reset_info(renderer)
        else:
            prev_mouse_x, prev_mouse_y = mouse_pos

        if cube_ui.events_listener.button_clicked:
            i, j = cube_ui.events_listener.button_coordinates
            pion_string = "cross" if player == 1 else "circle"
            if cube.get_pion((0, j, i)) != 0:
                print(f"Can't place a {pion_string} there")
            else:
                print(f"A {pion_string} got placed at coordinates {(i, j)}")
                cube.set_pion((0, j, i), player)
                player *= -1

        # Fill the screen with black
        screen.fill(BLACK)

        # Draw the cube
        cube_ui.draw(screen, Vector2(mouse_pos), mouse_click[0] == 1)


        # Update the display
        pygame.display.flip()

        clock.tick(60)
