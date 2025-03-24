import glm
import numpy as np
import threading, queue
import struct
import time
import math
import pygame as pg

from new_engine.donjon import Donjon
from new_engine.light import Light
from new_engine.camera import CameraAlt, CameraFollow
from new_engine.objects.advanced_skybox import AdvancedSkyBoxObject
from new_engine.player import FollowTerrainPlayer

from new_engine.objects.starting_base import StartingBase
from new_engine.objects.heatcore import HeatCore
from new_engine.objects.ancient_structure import AncientStructure
from new_engine.objects.popup import PopUp

from new_engine.chunk_jittery_test import ChunkTerrain, ColorParams, PointsHeightParams, SplineHeightParams, PerlinGenerator, BIOME_POINTS
from new_engine.meshes.chunk_mesh import ChunkMesh, DelaunayChunkMesh, TextureDelaunayChunkMesh, CHUNK_SIZE, LG2_CS
from new_engine.options import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, CHUNK_SCALE, HEIGHT_SCALE, INV_NOISE_SCALE, NUM_OCTAVES, \
    THREADS_LIMIT, TASKS_PER_FRAME
from new_engine.shader_program import open_shaders


def flatten(vector: glm.vec3) -> glm.vec3:
    """Flatten a given 3d vector (remove y composant)

    Args:
        vector (glm.vec3): 3d vector

    Returns:
        glm.vec3: flatten 3d vector
    """
    return glm.vec3(vector.x, 0, vector.z)

class Planet:
    """Class for a planet"""
    
    def __init__(self, app, saved_data):
        """Class constructor

        Args:
            app (GraphicsEngine): the graphic engine object
            saved_data (tuple): data used to load the planet (saved data or just the level)
        """
        self.saved_data = saved_data
        self.load_from_data = len(saved_data) == 6
        if self.load_from_data:
            level, seed = saved_data[:2]
        else:
            level = saved_data[0]
            seed = np.random.randint(0, 1000)
        
        self.level = level
        self.radius = 8
        self.radius_squared = self.radius ** 2
        self.app = app
        self.exit = False
        
        self.light = None
        self.camera = None
        self.player = None

        self.biome = sorted(list(BIOME_POINTS.keys()))[hash(seed) % len(BIOME_POINTS)]
        self.height_params = SplineHeightParams(self.biome, HEIGHT_SCALE)
        self.color_params = ColorParams(self.biome)
        self.seed = seed
        self.noise = PerlinGenerator(self.height_params, self.color_params,
                                     seed=self.seed, scale=100 / INV_NOISE_SCALE, octaves=NUM_OCTAVES)
        # self.chunk_shader = open_shaders(self.app, 'chunk_texture')
        self.chunk_shader = open_shaders(self.app, 'chunk')
        self.shadow_map = open_shaders(self.app, 'shadow_map')
        # self.texture = app.textures["test"]
        # self.depth_texture = self.app.textures["depth_texture"]
        # self.depth_fbo = self.app.context.framebuffer(depth_attachment=self.depth_texture)
        self.init_shaders()

        self.skybox = None
        self.starting_base = None
        self.ancient_structure = None
        self.donjon = None
        self.heatcores = {}
        self.num_heatcores = 2 + self.level
        self.popup = None
        self.new_popup("Vous êtes atterris", 3)
        self.can_enter = False

        self.result_queue = queue.Queue()
        self.threads = []
        self.threads_limit = THREADS_LIMIT
        self.semaphore = threading.Semaphore(self.threads_limit)

        self.chunk_meshes = {}
        self.chunks_loading = set()
        self.chunks_to_load_dic = {}
        self.chunks_to_load_set = set()
        self.tasks_per_frame = TASKS_PER_FRAME

    def load_attributes(self):
        """Load attributes dependant of planet being present in the main app"""
        self.app.get_time()
        self.light = Light(self.app, 360)
        self.camera = CameraFollow(self.app)
        self.player = FollowTerrainPlayer(self.app)
        if self.load_from_data:
            self.player.position = self.saved_data[2]
            self.player.forward = self.saved_data[3]
        self.load_objects()
    
    def load_objects(self):
        """Load all objects of generation"""
        # Skybox
        self.skybox = AdvancedSkyBoxObject(self.app, self.app.meshes["advanced_skybox"])

        # Starting base
        position = glm.vec3(0, 0, 0)
        position = self.avoid_cliffs(position, NUM_OCTAVES)
        position.y = max(0, position.y) + 0.02 * HEIGHT_SCALE
        self.starting_base = StartingBase(self.app, self.app.meshes["starting_base"], position)

        # Ancient structure
        rng = np.random.default_rng(self.seed)
        angle = rng.uniform(0, 360)
        radius = rng.uniform(1, 2)
        position = radius * glm.vec3(np.cos(np.radians(angle)), 0.0, np.sin(np.radians(angle)))
        position = self.avoid_water(position, NUM_OCTAVES)
        self.ancient_structure = AncientStructure(self.app, self.app.meshes["ancient_structure"], position)
        if self.load_from_data:
            self.ancient_structure.won = self.saved_data[5]

        # Heatcores
        angles = [rng.uniform(0, 360) for _ in range(self.num_heatcores)]
        radiuses = [rng.uniform(5, 10) for _ in range(self.num_heatcores)]
        
        # Make them spread
        min_diff = 40 / (self.num_heatcores - 1)
        for _ in range(3):
            for i in range(self.num_heatcores):
                next_idx = (i + 1) % self.num_heatcores
                diff = (angles[i] - angles[next_idx] % 360) - 180
                
                if diff < min_diff:
                    shift = (min_diff - diff) / 2
                    angles[i] -= shift
                    angles[next_idx] += shift
        
        for i in range(self.num_heatcores):
            if self.load_from_data and i not in self.saved_data[4]:
                continue
            position = radiuses[i] * glm.vec3(np.cos(np.radians(angles[i])), 0.0, np.sin(np.radians(angles[i])))
            
            position = self.avoid_water(position, NUM_OCTAVES)
            position.y += 0.005 * HEIGHT_SCALE
            print(f"Heatcore {i} at position: {position}")
            heatcore = HeatCore(self.app, self.app.meshes["heatcore"], position)
            
            self.heatcores[i] = heatcore
    
    def init_shaders(self):
        """Initialize the chunk shader"""
        colors_256 = np.zeros((256, 3), dtype=np.float32)
        colors_256[:len(self.color_params.colors)] = self.color_params.colors
        colors_256 *= 1 / 255
        self.chunk_shader['colors'].write(colors_256.tobytes())
        # self.texture.use(location=1)
        # self.chunk_shader["textureSampler"].value = 1

    def generate_chunk_worker(self, coord, detail):
        """Worker function for generating chunks and rendering
        
        Args:
            coord (tuple[int, int]): chunk coordinates as integers
            detail (float): the amount of detail for the given chunk"""
        chunk = ChunkTerrain(self.noise, coord[0], coord[1], CHUNK_SCALE)
        chunk_mesh = DelaunayChunkMesh(self.app, chunk)
        chunk_mesh.update_detail(detail)
        self.result_queue.put((coord, chunk_mesh))
    
    def generate_chunks(self):
        """Update chunks and load new ones"""
        player_position = self.player.position.xz / (CHUNK_SIZE * CHUNK_SCALE)
        player_chunk_coord = glm.vec2(glm.floor(player_position.x), glm.floor(player_position.y))
        keys_to_delete = [chunk_coord for chunk_coord in self.chunk_meshes.keys()
                          if glm.length2(player_position - chunk_coord - 0.5) > self.radius_squared]
        for key in keys_to_delete:
            del self.chunk_meshes[key]

        for i in range(-self.radius, self.radius + 1):
            for j in range(-self.radius, self.radius + 1):
                chunk_position = player_chunk_coord + (i, j)
                distance_sq = glm.length2(player_position - chunk_position - 0.5)
                if distance_sq > self.radius_squared:
                    continue # Don't load chunks too far away

                chunk_coord = tuple(chunk_position)
                if chunk_coord in self.chunks_loading:
                    continue # Don't reload a chunk being loaded loaded

                detail = distance_sq / self.radius_squared
                if chunk_coord in self.chunk_meshes:
                    chunk_detail = int(LG2_CS * self.chunk_meshes[chunk_coord].detail)
                    if chunk_detail == int(LG2_CS * detail):
                        continue # Don't load a chunk with same detail
                self.chunks_to_load_dic[chunk_coord] = detail
                self.chunks_to_load_set.add(chunk_coord)

    def handle_event(self, event):
        if event.type == pg.MOUSEWHEEL:
            self.player.camera_zoom *= 0.97 ** event.y

        if event.type == pg.KEYDOWN and event.key == self.app.controls["Interact"]:
            print(not self.ancient_structure.won,
                  glm.length2(self.player.position.xz - self.ancient_structure.position.xz) <= 4 * CHUNK_SCALE,
                  glm.length2(self.player.position.xz - self.starting_base.position.xz) <= 4 * CHUNK_SCALE)
            if not self.ancient_structure.won and \
               glm.length2(self.player.position.xz - self.ancient_structure.position.xz) <= 4 * CHUNK_SCALE:
                self.app.play_song("a cube of enigma.mp3")
                donjon = Donjon(self.app, self.level)
                donjon.run()
                self.ancient_structure.won = donjon.hud_game.won
                self.light.time += donjon.time_taken / 5
                donjon.destroy()
            elif glm.length2(self.player.position.xz - self.starting_base.position.xz) <= 4 * CHUNK_SCALE:
                self.exit = True

    def update_chunks(self):
        """Distribute chunk generation tasks across multiple frames"""
        #print(f"Chunks to load: {self.chunks_to_load_dic}")
        tasks_this_frame = 0
        keys_used = []

        if tasks_this_frame < self.tasks_per_frame and len(self.threads) < self.threads_limit:
            for coord in self.chunks_to_load_dic.keys():
                self.chunks_to_load_set.remove(coord)
                t = threading.Thread(
                    target=self.generate_chunk_worker,
                    args=(coord, self.chunks_to_load_dic[coord])
                )
                t.start()
                self.threads.append(t)
                self.chunks_loading.add(coord)
                keys_used.append(coord)
                tasks_this_frame += 1

                if tasks_this_frame >= self.tasks_per_frame or len(self.threads) >= self.threads_limit:
                    break
        for key in keys_used:
            del self.chunks_to_load_dic[key]

        self.threads = [t for t in self.threads if t.is_alive()]

        temp = set()
        while not self.result_queue.empty():
            coord, chunk_mesh = self.result_queue.get()
            if chunk_mesh.detail is not None:
                chunk_mesh.init_context()
            self.chunk_meshes[coord] = chunk_mesh
            #print(f"Attempting to remove {coord} from {self.chunks_loading}")
            self.chunks_loading.remove(coord)
            temp.add(coord)

        #print(f"Chunks loading: {self.chunks_loading}")
        #print(f"Chunks that finished loading: {temp}")
    
    def update_shader(self):
        """Update the chunk shader"""
        # Light
        self.chunk_shader['light.direction'].write(self.light.direction)
        self.chunk_shader['light.Ia'].write(self.light.Ia)
        self.chunk_shader['light.Id'].write(self.light.Id)
        self.chunk_shader['light.Is'].write(self.light.Is)

        # MVP + camera
        self.chunk_shader['m_view'].write(self.camera.view_matrix)
        self.chunk_shader['m_proj'].write(self.camera.m_proj)
        self.chunk_shader['camPos'].write(self.camera.position)

        # Time
        self.chunk_shader['time'].write(struct.pack('f', self.app.time))

    def update(self):
        """Update all components needed to be updated each frame"""
        # Long aaah line
        if not (self.app.hud.hud_buttons.active or self.app.hud.hud_menu.active):
            if not (self.app.hud.hud_intro.active or self.app.hud.hud_credits.active):
                self.light.update()
            self.player.update()
            self.camera.update()

            keys_to_delete = set()
            for index, heatcore in self.heatcores.items():
                if glm.length2(heatcore.position.xz - self.player.position.xz) <= CHUNK_SCALE:
                    print("Heatcore taken !")
                    keys_to_delete.add(index)
            for index in keys_to_delete:
                del self.heatcores[index]

            if glm.length2(self.player.position.xz - self.ancient_structure.position.xz) <= 4 * CHUNK_SCALE:
                popup_text = "??? [Interact]"
                if self.popup.text != popup_text:
                    self.new_popup(popup_text, 3)
            elif glm.length2(self.player.position.xz - self.starting_base.position.xz) <= 4 * CHUNK_SCALE:
                popup_text = "Décoller vers une autre planète [Interact]" if self.app.hud.hud_game.heatcore_bar.heatcore_count <= 8 else "Rentrer à la maison [Interact]"
                if self.popup.text != popup_text:
                    self.new_popup(popup_text, 3)
            else:
                self.empty_popup()



        self.generate_chunks()
        self.update_chunks()
        self.update_shader()

    def new_popup(self, text, wait_time, size=SCREEN_WIDTH // 2, font_size=40, y=100,
                  fade_in=0.5, fade_out=0.5, center_text=True, border_radius=10, border_width=10):
        self.popup = PopUp(self.app, text, size, font_size, y,
                           fade_in, wait_time, fade_out, center_text, border_radius, border_width)

    def empty_popup(self):
        self.new_popup("easter egg 69420", 0, fade_in=0, fade_out=0)

    def render(self):
        """Render all chunks within the active radius"""
        self.update()
        player_position = self.camera.position / (CHUNK_SIZE * CHUNK_SCALE)

        for (i, j) in self.chunk_meshes.keys():
            chunk_mesh = self.chunk_meshes[(i, j)]
            if chunk_mesh.detail is None:
                continue
            distance_sq = (player_position.x - i - 0.5) ** 2 + (player_position.z - j - 0.5) ** 2
            chunk_mesh.update_model_matrix(glm.sqrt(distance_sq))
            chunk_mesh.render()

        # Object
        self.skybox.render()
        self.ancient_structure.render()
        self.starting_base.render()
        for heatcore in self.heatcores.values():
            heatcore.render()
        self.player.render()
        self.popup.render()

    def destroy(self):
        """Clean up resources (garbage collector)"""
        self.semaphore.acquire()
        for t in self.threads:
            t.join()

        [mesh.destroy() for mesh in self.chunk_meshes.values()]
        self.chunk_shader.release()

    def get_perlin_height(self, position: glm.vec3, octaves: int = 1):
        """Generate the height of a position in 3d (y component can be anything)

        Args:
            position (glm.vec3): the 3d vector of the vertex
            octaves (int, optional): number of octaves for the height calculation. Defaults to 1.

        Returns:
            float: height of the position
        """
        sample_x, sample_y = np.array(position.xz / CHUNK_SCALE)
        noise_value = self.noise.noise_value(sample_x, sample_y, octaves=octaves)
        height_value = self.noise.height_params.height_from_noise(noise_value)
        return height_value * CHUNK_SCALE

    def get_normal(self, position: glm.vec3, octaves: int = 1, get_height: bool = False):
        """Generate the normal vector for a given position in 3d (y component can be anything)

        Args:
            position (glm.vec3): the 3d vector of the vertex
            octaves (int, optional): number of octaves for height calculations. Defaults to 1.
            get_height (bool, optional): returns height of the position as well. Defaults to False.

        Returns:
            glm.vec3 | tuple[float, glm.vec3]: the normal vector of the position
                or with it the position height (if get_height is True)
        """
        epsilon = 0.1 * CHUNK_SCALE 
        height_center = self.get_perlin_height(position, octaves)
        height_x = self.get_perlin_height(position + glm.vec3(epsilon, 0, 0), octaves)
        height_z = self.get_perlin_height(position + glm.vec3(0, 0, epsilon), octaves)
        
        dx = glm.vec3(epsilon, height_x - height_center, 0)
        dz = glm.vec3(0, height_z - height_center, epsilon)
        normal = glm.normalize(glm.cross(dz, dx))
        
        if get_height:
            return height_center, normal
        return normal

    MAX_ITERATIONS = 100  # Prevent infinite loops
    MIN_MOVEMENT = 0.001  # Threshold for minimal movement
    FORCED_STEP = 0.1 * CHUNK_SCALE  # Small step to escape if stuck
    RANDOM_STEP = 0.1 * CHUNK_SCALE

    def avoid_water(self, position: glm.vec3, octaves: int = 1):
        """Wiggle around a point until it is not underwater anymore

        Args:
            position (glm.vec3): the starting position
            octaves (int, optional): number of octaves used for normal calculations. Defaults to 1.

        Returns:
            glm.vec3: the final position of the point
        """
        i = 0
        height, terrain_normal = self.get_normal(position, octaves, True)
        prev_height = height  # Store previous height to detect local maxima
        local_max_count = 0  # Counter to track local max occurrences
        rng = np.random.default_rng(abs(hash(tuple(position))))

        while height < 0.01 * HEIGHT_SCALE and i < self.MAX_ITERATIONS:
            print(f"Iteration {i}")
            print(f"  Position {position} with height {height}")
            movement = flatten(terrain_normal)
            movement_length = glm.length(movement)

            if movement_length < self.MIN_MOVEMENT:
                print("    Minimal movement detected, forcing displacement.")
                movement = glm.normalize(glm.cross(terrain_normal, glm.vec3(0, 1, 0))) * self.FORCED_STEP * i

            position -= movement
            new_height, terrain_normal = self.get_normal(position, octaves, True)
            print(f"  Movement {movement} with new height {new_height}")
            print(f"  New normal {terrain_normal}")

            # Detect local maximum (if height doesn't really change)
            if abs(new_height - prev_height) <= 0.05 * HEIGHT_SCALE:
                local_max_count += 1
            else:
                local_max_count = 0  # Reset if we find an increasing height

            if local_max_count > 3:  # If we're stuck for multiple steps
                print("    Local maximum detected, moving randomly.")
                random_direction = glm.vec3(rng.uniform(-1, 1), 0, rng.uniform(-1, 1))
                random_direction = glm.normalize(random_direction) * self.RANDOM_STEP * i # Increase step by iteration
                position += random_direction  # Move randomly to escape

                # Reset height tracking
                local_max_count = 0

            prev_height = new_height  # Update previous height
            height = new_height  # Update current height

            i += 1
            print(f"Loop condition: {height} < {0.01 * HEIGHT_SCALE} and {i} < {self.MAX_ITERATIONS}")
            print(f"  -> {height < 0.01 * HEIGHT_SCALE and i < self.MAX_ITERATIONS}")
            print()

        print(f"Total iterations for avoiding water: {i}")
        return flatten(position) + glm.vec3(0, height, 0)

    def avoid_cliffs(self, position: glm.vec3, octaves: int = 1):
        """Wiggle around a point until it is not on a cliff anymore

        Args:
            position (glm.vec3): the starting position
            octaves (int, optional): number of octaves used for normal calculations. Defaults to 1.

        Returns:
            glm.vec3: resulting point of the wiggling around
        """
        i = 0
        height, terrain_normal = self.get_normal(position, octaves, True)
        terrain_normal.y = 0
        while terrain_normal.y > glm.sin(glm.radians(30)):
            print(f"Iteration {i}")
            print(f"  Position {position} with normal {terrain_normal}")
            position -= flatten(terrain_normal)
            height, terrain_normal = self.get_normal(position, octaves, True)
            i += 1
            print(f"  New normal {terrain_normal}")
            print(f"Loop condition: {terrain_normal.y} > {glm.sin(glm.radians(30))}")
            print(f"  -> {terrain_normal.y > glm.sin(glm.radians(30))}")
            print()
        print(f"Iteration of avoiding cliff: {i}")
        return flatten(position) + glm.vec3(0, height, 0)

    def cinematique_entree(self):
        """Cinematic of entrance to the world (not here yet)"""
        running = True
        popup = PopUp(self.app, "Décollage vers une nouvelle planète...", SCREEN_WIDTH // 1.5, 50, SCREEN_HEIGHT // 3, 0.5, 1000, 0.5, True, 50, 50)
        while running:
            self.app.context.clear(color=(0, 0, 0))
            self.generate_chunks()
            self.update_chunks()
            if len(self.chunks_to_load_set) == 0 and len(self.chunks_loading) == 0:
                running = False

            popup.render()

            pg.display.flip()
            self.app.clock.tick(FPS)
        popup.destroy()