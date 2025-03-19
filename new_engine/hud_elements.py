import sys
# from intel_arti.cube_v2.cube import Cube
# from intel_arti.cube_v2.cube_ui import Renderer, Camera, CubeUI
import os, math
import pygame as pg
import glm

from new_engine.options import SCREEN_WIDTH, FOV

# from tensorflow.keras.models import load_model
# from intel_arti.cube_v2.agent import Agent



DEFAULT_CONTROLS = {
    "Strafe Left": pg.K_q,
    "Forward": pg.K_z,
    "Strafe Right": pg.K_d,
    "Backward": pg.K_s,
    "Toggle Menu": pg.K_ESCAPE,
    "Reset Planet": pg.K_r
}

HARDSET_CONTROLS = {
    "Zoom": "Molette (scroll)",
    "Focus": "Clique Droit"
}

MENU_BACKGROUND_ICON = pg.image.load("txt/background_logo.png")
MENU_INGAME_BACKGROUND_ICON = pg.image.load("txt/dark_background_logo.png")

class CompassBar:
    def __init__(self, screen, x, y, length, color=(255, 255, 255), thickness=5):
        self.screen = screen
        self.x = x
        self.y = y
        self.length = length
        self.color = color
        self.thickness = thickness

    def draw(self):
        start_pos = (self.x - self.length // 2, self.y)
        end_pos = (self.x + self.length // 2, self.y)
        pg.draw.line(self.screen, self.color, start_pos, end_pos, self.thickness)

class CompassMarker:
    def __init__(self, screen, compass_bar_y, compass_bar_length,
                 color=(255, 255, 255), size=10, thickness=5, image_path=None):
        self.screen = screen
        self.compass_bar_y = compass_bar_y
        self.compass_factor = compass_bar_length / SCREEN_WIDTH
        self.color = color
        self.size = size
        self.thickness = thickness
        self.image = pg.image.load(image_path) if image_path is not None else None
        self.image_offset_y = 20

    def get_point(self, camera): ...

    def draw(self, camera):
        clip_pos = camera.m_proj * camera.view_matrix * self.get_point(camera)
        if clip_pos.w <= 0:
            return # Point is behind the camera or on the sides
        ndc_x = clip_pos.x / clip_pos.w
        if abs(ndc_x) >= self.compass_factor:
            return # Point is outside the compass bar
        x_coord = (ndc_x + 1) / 2 * SCREEN_WIDTH

        # Draw the actual marker
        start_pos = (x_coord, self.compass_bar_y - self.size // 2)
        end_pos = (x_coord, self.compass_bar_y + self.size // 2)
        pg.draw.line(self.screen, self.color, start_pos, end_pos, self.thickness)

        if self.image is not None:
            image_x = x_coord - self.image.get_width() // 2
            image_y = self.compass_bar_y + self.image_offset_y
            self.screen.blit(self.image, (image_x, image_y))

class HeatcoreMarker(CompassMarker):
    def __init__(self, screen, heatcore, compass_bar_y, compass_bar_length,
                 color=(255, 255, 255), size=10, thickness=5, image_path=None):
        super().__init__(screen, compass_bar_y, compass_bar_length, color, size, thickness, image_path)
        self.heatcore = heatcore

    def get_point(self, camera):
        return self.heatcore.m_model * glm.vec4(0, 0, 0, 1.0)

class PolarMarker(CompassMarker):
    def __init__(self, screen, position, compass_bar_y, compass_bar_length,
                 color=(255, 255, 255), size=10, thickness=5, image_path=None):
        super().__init__(screen, compass_bar_y, compass_bar_length, color, size, thickness, image_path)
        self.position = glm.vec4(position, 1.0)

    def get_point(self, camera):
        return glm.vec4(camera.position, 0) + self.position

class HeatcoreBar:
    def __init__(self, screen, x, y, width, height, heatcore_number = 3):
        self.screen = screen
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.heatcore_count = 0
        self.sections = heatcore_number
        self.colors = {
            "inactive": (50, 50, 50),
            "active": (255, 165, 0),
            "full_base": (255, 165, 0),
            "full_target": (255, 255, 0),
        }
        self.pulsation_speed = 7

    def set_heatcore_count(self, count):
        self.heatcore_count = max(0, min(count, self.sections))

    def add_heatcore_count(self, num = 1):
        self.heatcore_count += num

    def draw(self):
        section_spacing = 5  # Space between bars
        bar_height = (self.height - (self.sections - 1) * section_spacing) // self.sections

        for i in range(self.sections):
            color = self.colors["active"] if i < self.heatcore_count else self.colors["inactive"]
            self._draw_section(i, color, bar_height, section_spacing)

    def _draw_section(self, index, color, bar_height, section_spacing):
        rect_x = self.x
        rect_y = self.y + self.height - ((index + 1) * (bar_height + section_spacing))
        rect_width = self.width
        rect_height = bar_height

        border_radius = 10
        pg.draw.rect(self.screen, color, (rect_x, rect_y, rect_width, rect_height), border_radius=border_radius)


class UI1:
    def __init__(self, app, screen):
        self.app = app
        self.screen = screen
        self.active = True

        self.compass_bar_x = screen.get_width() // 2
        self.compass_bar_y = 50
        self.compass_bar_length = 1000
        self.compass_bar = CompassBar(screen, self.compass_bar_x, self.compass_bar_y, self.compass_bar_length)

        marker_data = [
            {"position": glm.vec3(1, 0, 0), "color": (255, 0, 0), "size": 15, "thickness": 4},    # North
            {"position": glm.vec3(-1, 0, 0), "color": (0, 255, 0), "size": 15, "thickness": 4},  # South
            {"position": glm.vec3(0, 0, 1), "color": (0, 0, 255), "size": 15, "thickness": 4},   # East
            {"position": glm.vec3(0, 0, -1), "color": (255, 255, 0), "size": 15, "thickness": 4},  # West
        ]
        self.polar_markers = [
            PolarMarker(
                screen,
                data["position"],
                self.compass_bar_y,
                self.compass_bar_length,
                color=data.get("color", (255, 255, 255)),
                size=data.get("size", 10),
                thickness=data.get("thickness", 5),
            )
            for data in marker_data
        ]
        self.heatcore_markers = {}
        self.ancient_strcture_marker = None

        height = 200
        width = 10
        x = screen.get_width() - (width + 50)
        y = screen.get_height() - (height + 50)
        self.heatcore_bar = HeatcoreBar(screen, x, y, width, height)
    
    def update(self):
        heatcore_keys = set(self.app.planet.heatcores.keys())
        marker_keys = set(self.heatcore_markers.keys())
        keys_to_remove = marker_keys.difference(heatcore_keys)
        keys_to_add = heatcore_keys.difference(marker_keys)
        for key in keys_to_remove:
            del self.heatcore_markers[key]
        for key in keys_to_add:
            self.heatcore_markers[key] = HeatcoreMarker(
                self.screen, self.app.planet.heatcores[key], 
                self.compass_bar_y, self.compass_bar_length,
                (0, 0, 0), 15, 8
            )
        
        self.heatcore_bar.set_heatcore_count(self.app.planet.num_heatcores - len(self.heatcore_markers))
        
        ancient_structure = self.app.planet.ancient_structure
        self.ancient_strcture_marker = HeatcoreMarker(
            self.screen, ancient_structure, self.compass_bar_y, self.compass_bar_length,
            (255, 0, 255), 20, 12
        )
        

    def draw(self, camera):
        """yaw and fov in radians please"""
        self.update()
        self.compass_bar.draw()

        for polar_marker in self.polar_markers:
            polar_marker.draw(camera)
        for heatcore_marker in self.heatcore_markers.values():
            heatcore_marker.draw(camera)

        if self.ancient_strcture_marker is not None:
            self.ancient_strcture_marker.draw(camera)

        self.heatcore_bar.draw()

class UI2:
    def __init__(self, app, screen):
        self.app = app
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.active = False
        self.first_time = True # True on the first time showed, controlling background image
        self.first_time_overlay_icon = pg.transform.scale(MENU_BACKGROUND_ICON, (self.height, self.height))
        self.first_time_overlay_background = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.first_time_overlay_background.fill((200, 200, 200, 250))
        self.overlay_icon = pg.transform.scale(MENU_INGAME_BACKGROUND_ICON, (self.height, self.height))
        self.overlay_background = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.overlay_background.fill((20, 20, 20, 100))

        self.play_button_rect = pg.Rect(self.width//7, (self.height - 100) // 3, 250, 50)
        self.controls_button_rect = pg.Rect(self.play_button_rect.left, self.play_button_rect.bottom + 20, 250, 50)
        self.save_button_rect = pg.Rect(self.play_button_rect.left, self.controls_button_rect.bottom + 20, 250, 50)
        self.close_button_rect = pg.Rect(self.play_button_rect.left, self.save_button_rect.bottom + 40, 250, 50)

        self.font = pg.font.SysFont("Arial", 24)
        self.title_font = pg.font.SysFont("Arial", 48)
        self.subtitle_font = pg.font.SysFont("Arial", 32)

        self.controls_requested = False

    def draw_text_with_outline(self, text, font, text_color, center, outline_color=(0, 0, 0), outline_offset=2):
        base_text = font.render(text, True, text_color)
        text_rect = base_text.get_rect(center=center)
        for dx in range(-outline_offset, outline_offset + 1):
            for dy in range(-outline_offset, outline_offset + 1):
                if dx != 0 or dy != 0:
                    outline = font.render(text, True, outline_color)
                    outline_rect = outline.get_rect(center=(center[0] + dx, center[1] + dy))
                    self.screen.blit(outline, outline_rect)
        self.screen.blit(base_text, text_rect)

    def draw_low_poly_button(self, rect, text_hover_color, text):
        x, y, w, h = rect
        points = [
            (x-500, y),
            (x-500, y+h),
            (x+w, y+h),
            (x+w, y)
        ]
        button_rect = pg.draw.polygon(self.screen, pg.Color(0, 0, 0, 120), points)
        if button_rect.collidepoint(pg.mouse.get_pos()):
            btn_text = self.font.render(text, True, text_hover_color)
        else:
            btn_text = self.font.render(text, True, (255, 255, 255))
        btn_text_rect = btn_text.get_rect(center=rect.center)
        self.screen.blit(btn_text, btn_text_rect)

    def draw(self):
        self.screen.blit(self.first_time_overlay_background if self.first_time else self.overlay_background, (0, 0))
        self.screen.blit(self.first_time_overlay_icon if self.first_time else self.overlay_icon, (self.width-self.overlay_icon.get_size()[0], 0))
        image_text = pg.image.load("txt/title_logo.png")
        self.screen.blit(image_text, ((self.width-image_text.get_size()[0])//2, 60))
        self.draw_text_with_outline("frozen worlds", self.subtitle_font, (180, 180, 255),
                                    (self.width // 2, 160), outline_color=(0, 0, 0), outline_offset=1)

        clair = 70 # la couleur est celle du logo, rendue plus claire par soucis de visibilité
        color_buttons = (53+clair, 15+clair, 30+clair)
        self.draw_low_poly_button(self.close_button_rect, color_buttons, "Fermer")
        self.draw_low_poly_button(self.play_button_rect, color_buttons, "Jouer")
        self.draw_low_poly_button(self.controls_button_rect, color_buttons, "Contrôles")
        self.draw_low_poly_button(self.save_button_rect, color_buttons, "Sauvegarder")

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if self.close_button_rect.collidepoint(mouse_pos):
                print("Close button clicked: Ending the game.")
                self.app.quit_game()
            elif self.play_button_rect.collidepoint(mouse_pos):
                print("Play button clicked!")
                self.active = False
                pg.mouse.set_visible(False)
                pg.mouse.set_pos(self.width//2, self.height//2)
            elif self.controls_button_rect.collidepoint(mouse_pos):
                print("Controls button clicked: Accessing Control Settings.")
                self.active = False
                self.controls_requested = True
                pg.mouse.set_visible(True)

class UI2_1:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.active = False  # Whether this submenu is currently shown.
        self.first_time = False # True on the first time showed, controlling background image
        self.first_time_overlay_icon = pg.transform.scale(MENU_BACKGROUND_ICON, (self.height, self.height))
        self.first_time_overlay_background = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.first_time_overlay_background.fill((200, 200, 200, 250))
        self.overlay_icon = pg.transform.scale(MENU_INGAME_BACKGROUND_ICON, (self.height, self.height))
        self.overlay_background = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.overlay_background.fill((20, 20, 20, 100))

        self.title_font = pg.font.SysFont("Arial", 48)
        self.font = pg.font.SysFont("Arial", 24)

        self.bindings = DEFAULT_CONTROLS.copy()

        self.control_buttons = {}
        start_y = 150
        spacing = 60
        button_width = 100
        button_height = 40
        for i, action in enumerate(self.bindings.keys()):
            x = (self.width // 7) + 240
            y = start_y + i * spacing
            self.control_buttons[action] = pg.Rect(x, y, button_width, button_height)

        self.back_button_rect = pg.Rect(self.width//2 - 100, self.height - 250, 150, 50)

        self.awaiting_binding = None

        self.return_to_ui2 = False

    def draw(self):
        self.screen.blit(self.first_time_overlay_background if self.first_time else self.overlay_background, (0, 0))
        self.screen.blit(self.first_time_overlay_icon if self.first_time else self.overlay_icon, (self.width-self.overlay_icon.get_size()[0], 0))

        title_text = self.title_font.render("Contrôles", True, (53, 15, 30))
        title_rect = title_text.get_rect(center=(self.width // 2, 60))
        self.screen.blit(title_text, title_rect)

        start_y = 150
        spacing = 60
        for i, (action, key) in enumerate(self.bindings.items()):
            label_text = self.font.render(action + ":", True, (255, 255, 255))
            label_points = label_text.get_rect(midleft=(self.width//7, start_y + i * spacing + 20))
            points = [
                (label_points.left-6, label_points.bottom+6),
                (label_points.left-6, label_points.top-6),
                (label_points.right+6, label_points.top-6),
                (label_points.right+6, label_points.bottom+6),
                ]
            label_rect = pg.draw.polygon(self.screen, pg.Color(0, 0, 0, 120), points)
            self.screen.blit(label_text, label_rect)
            button_rect = self.control_buttons[action]
            color = (255, 165, 0) if self.awaiting_binding == action else (0, 200, 0)
            pg.draw.rect(self.screen, color, button_rect)
            key_name = pg.key.name(key).upper()
            key_text = self.font.render(key_name, True, (255, 255, 255))
            key_rect = key_text.get_rect(center=button_rect.center)
            self.screen.blit(key_text, key_rect)

        pg.draw.rect(self.screen, pg.Color(200, 0, 0, 120), self.back_button_rect)
        back_text = self.font.render("Retour", True, (255, 255, 255))
        back_rect = back_text.get_rect(center=self.back_button_rect.center)
        self.screen.blit(back_text, back_rect)

    def handle_event(self, event):

        if self.awaiting_binding is not None:
            if event.type == pg.KEYDOWN:
                self.bindings[self.awaiting_binding] = event.key
                DEFAULT_CONTROLS[self.awaiting_binding] = event.key
                print(f"Rebound {self.awaiting_binding} to {pg.key.name(event.key).upper()}")
                self.awaiting_binding = None
            return

        if event.type == pg.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            for action, rect in self.control_buttons.items():
                if rect.collidepoint(mouse_pos):
                    self.awaiting_binding = action
                    print(f"Awaiting new key for {action}...")
                    return
            if self.back_button_rect.collidepoint(mouse_pos):
                print("Back button clicked: Returning to main menu (UI2).")
                self.active = False
                self.return_to_ui2 = True


class MenuIntroUI:
    '''
    L'écran sur lesquel défile le dialogue d'introduction au début du jeu
    '''
    def __init__(self, screen):
        self.screen = screen
        self.text_intro = "txt/text_intro.txt"

    def handle_event(self, event):
        """
        Gère les interactions (bouton skip dialogue et scrolling du texte)
        """

    def raw(self):
        """affiche l'écran"""

class UI3:
    def __init__(self, screen):
        self.screen = screen  # The UI surface passed from the GraphicsEngine.
        self.width, self.height = self.screen.get_size()
        self.active = True

        # Define a centered square game area (leaving space at the bottom for buttons).
        button_area_height = 100
        game_size = min(self.width, self.height - button_area_height)
        self.game_rect = pg.Rect(
            (self.width - game_size) // 2,
            (self.height - button_area_height - game_size) // 2,
            game_size,
            game_size
        )
        self.game_surface = pg.Surface((self.game_rect.width, self.game_rect.height))

        # Create cube game objects.
        self.camera = Camera(latitude=math.radians(30),
                             longitude=2 * math.pi / 3,
                             distance=10.0)
        self.renderer = Renderer(self.camera, screen_data=pg.math.Vector2(self.game_rect.width, self.game_rect.height))
        self.cube = Cube()
        self.cube_ui = CubeUI(self.cube, self.renderer, side_length=self.game_rect.height * math.pi)

        # Define overlay buttons (positioned along the bottom).
        button_width = 150
        button_height = 50
        bmargin = 20
        self.buttons = {
            'reset_view': pg.Rect(bmargin, self.height - button_height - bmargin, button_width, button_height),
            'reset_game': pg.Rect(bmargin * 2 + button_width, self.height - button_height - bmargin, button_width, button_height),
            'hint': pg.Rect(bmargin * 3 + button_width * 2, self.height - button_height - bmargin, button_width, button_height),
            'return': pg.Rect(self.width - button_width - bmargin, self.height - button_height - bmargin, button_width, button_height)
        }
        self.button_color = (0, 128, 255)
        self.button_border_color = (255, 255, 255)
        self.hints_remaining = 5

        # Flags for UI3 exit and mouse click.
        self.exit_ui3 = False
        self.mouse_clicked = False

        # --- Cube AI Integration ---
        # Set up turn management: assume human is 1 and AI is -1.
        self.current_player = 1  # Human player's turn initially.
        self.ai_player = -1      # AI player.
        self.coup_interdit = -1  # A move that is temporarily forbidden.
        self.fini = False        # Game over flag.

        # Create the AI agent and load the model.
        self.agent = Agent(True)
        NUM_MODEL = 1
        GENERATION = 1
        MODEL_PATH = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "models", f"generation{GENERATION}", f"model{NUM_MODEL}.h5"
        )
        try:
            self.agent.model = load_model(MODEL_PATH)
            print(f"Model loaded successfully from {MODEL_PATH}")
        except FileNotFoundError as e:
            print(f"Error: Model file not found at {MODEL_PATH}. Please verify that the file exists.")
            self.agent.model = None  # Disable AI functionality if the model is missing.

    def handle_event(self, event):
        """Handle events for both the cube game and the overlay buttons."""
        if event.type == pg.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            # Check if any overlay button is clicked.
            for name, rect in self.buttons.items():
                if rect.collidepoint(mouse_pos):
                    if name == 'reset_view':
                        self.reset_view()
                    elif name == 'reset_game':
                        self.reset_game()
                    elif name == 'hint':
                        self.use_hint()
                    elif name == 'return':
                        self.exit_ui3 = True
                    return  # Consume the event if a button was clicked.
            # If no overlay button was clicked, check for a left-click in the game area.
            if event.button == 1 and self.game_rect.collidepoint(mouse_pos):
                self.mouse_clicked = True

        if event.type == pg.MOUSEMOTION:
            if self.game_rect.collidepoint(event.pos):
                # Update the cube camera if the right mouse button is held.
                if event.buttons[2]:
                    rel = event.rel
                    self.camera.update_camera_from_mouse(delta_x=rel[0], delta_y=rel[1])

    def reset_view(self):
        """Reset the cube camera view to its initial parameters."""
        self.camera.longitude = 2 * math.pi / 3
        self.camera.latitude = math.pi / 6
        self.camera.reset_position()
        self.renderer.reset()
        self.cube_ui.reset_info()
        print("Reset view button pressed.")

    def reset_game(self):
        """Restart the cube game with a new cube."""
        self.cube = Cube()
        self.cube_ui = CubeUI(self.cube, self.renderer, side_length=self.game_rect.height * math.pi)
        # Reset turn management.
        self.current_player = 1
        self.coup_interdit = -1
        self.fini = False
        print("Reset game button pressed.")

    def use_hint(self):
        """Consume one hint (if available) and print a message."""
        if self.hints_remaining > 0:
            print("Hint used!")
            self.hints_remaining -= 1
        else:
            print("No hints remaining.")

    def update(self, dt):
        """
        Update dynamic elements of the cube game.
        Processes human moves (via cell clicks) and, if it's the AI's turn,
        makes the AI choose and play a move.
        """
        # ----- Process Human Move -----
        if self.cube_ui.events_listener.button_clicked != (-1, -1):
            i, j = self.cube_ui.events_listener.button_clicked
            current_value = self.cube_ui.cube.get_pion((0, j, i))
            print(f"Before placing, cell (0, {j}, {i}) value: {current_value}")
            if current_value != 0:
                print(f"Cell ({i}, {j}) already occupied")
            else:
                print(f"Placing human piece at ({i}, {j})")
                self.cube_ui.cube.set_pion((0, j, i), self.current_player)
            self.cube_ui.events_listener.button_clicked = (-1, -1)
            self.cube_ui.reset_info()
            self.current_player *= -1

        # ----- Process AI Move -----
        if self.current_player == self.ai_player and not self.fini:
            action = self.agent.choisir(self.cube, self.current_player, self.coup_interdit)
            if action is not None:
                print(f"AI chose action: {action}")
                if action < 9:
                    # Placement move on the top face.
                    i = action % 3  # Column index
                    j = action // 3  # Row index
                    if self.cube.get_pion((0, j, i)) == 0:
                        print(f"Placing AI piece at ({i}, {j})")
                        self.cube.set_pion((0, j, i), self.current_player)
                    else:
                        print(f"AI move: cell ({i}, {j}) already occupied.")
                    self.coup_interdit = action + 9
                elif action < 18:
                    # Rotation move.
                    self.cube.jouer(action, self.current_player)
                    self.coup_interdit = action - 9
                else:
                    self.coup_interdit = -1
                print(f"AI played action {action}, coup_interdit: {self.coup_interdit}")
                self.current_player *= -1
                self.cube_ui.reset_info()

    def draw(self):
        """Draw the cube game interface and overlay buttons onto the UI surface."""
        # Fill the entire UI surface with a fully opaque black background.
        self.screen.fill((0, 0, 0, 255))

        # Draw the cube game within the defined game area.
        self.game_surface.fill((0, 0, 0))
        # Get the mouse position relative to the game area.
        local_mouse = pg.math.Vector2(pg.mouse.get_pos()[0] - self.game_rect.x,
                                      pg.mouse.get_pos()[1] - self.game_rect.y)
        # Pass the click flag to cube_ui.draw.
        self.cube_ui.draw(self.game_surface, local_mouse, self.mouse_clicked)
        # Reset the click flag after processing.
        self.mouse_clicked = False
        # Blit the game surface onto the UI surface.
        self.screen.blit(self.game_surface, self.game_rect.topleft)

        # Draw the overlay buttons.
        font = pg.font.SysFont("Arial", 20)
        for name, rect in self.buttons.items():
            pg.draw.rect(self.screen, self.button_color, rect)
            pg.draw.rect(self.screen, self.button_border_color, rect, 2)
            if name == 'reset_view':
                text = "Reset View"
            elif name == 'reset_game':
                text = "Reset Game"
            elif name == 'hint':
                text = f"Hint ({self.hints_remaining})"
            elif name == 'return':
                text = "Return"
            text_surf = font.render(text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=rect.center)
            self.screen.blit(text_surf, text_rect)
