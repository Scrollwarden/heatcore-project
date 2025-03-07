import glm
import numpy as np
import threading, queue
import struct
import time
import math
import pygame as pg

from new_engine.light import Light
from new_engine.camera import CameraAlt, CameraFollow
from new_engine.player import Player, PlayerFollow, PlayerNoChangeInHeight, SatisfyingPlayer, FollowTerrainPlayer

from new_engine.meshes.obj_base_mesh import DefaultObjMesh, GameObjMesh
from new_engine.objects.starting_base import StartingBase
from new_engine.objects.heatcore import HeatCore

from new_engine.chunk_jittery_test import ChunkTerrain, ColorParams, PointsHeightParams, SplineHeightParams, PerlinGenerator
from new_engine.meshes.chunk_mesh import ChunkMesh, DelaunayChunkMesh, CHUNK_SIZE, LG2_CS
from new_engine.options import FPS, CHUNK_SCALE, HEIGHT_SCALE, INV_NOISE_SCALE, NUM_OCTAVES, THREADS_LIMIT, TASKS_PER_FRAME
from new_engine.shader_program import open_shaders


def in_triangle(point, triangle):
    a, b, c = np.array([np.array([p[0], p[2]]) for p in triangle])
    p = np.array([point[0], point[2]])

    # Compute vectors
    v0 = c - a
    v1 = b - a
    v2 = p - a

    # Compute dot products
    dot00 = np.dot(v0, v0)
    dot01 = np.dot(v0, v1)
    dot02 = np.dot(v0, v2)
    dot11 = np.dot(v1, v1)
    dot12 = np.dot(v1, v2)

    # Compute barycentric coordinates
    denom = dot00 * dot11 - dot01 * dot01
    if denom == 0:  # Degenerate triangle
        return False

    u = (dot11 * dot02 - dot01 * dot12) / denom
    v = (dot00 * dot12 - dot01 * dot02) / denom

    # Check if point is inside the triangle
    return (u >= 0) and (v >= 0) and (u + v <= 1)

def flatten(vector: glm.vec3):
    return glm.vec3(vector.x, 0, vector.z)

class Planet:
    def __init__(self, app):
        self.radius = 10
        self.radius_squared = self.radius ** 2
        self.app = app
        
        self.light = Light()

        points = ((0.0, -0.2), (0.4, 0.0), (0.45, 0.1), (0.5, 0.2), (0.6, 0.26), (1.0, 1.0))
        self.height_params = SplineHeightParams(points, HEIGHT_SCALE)
        self.color_params = ColorParams()
        self.seed = 2
        self.noise = PerlinGenerator(self.height_params, self.color_params,
                                     seed=self.seed, scale=100 / INV_NOISE_SCALE, octaves=NUM_OCTAVES)
        self.chunk_shader = open_shaders(self.app, 'chunk')
        self.init_shader()

        self.objects = []
        self.num_heatcores = 3
        self.load_objects()

        self.result_queue = queue.Queue()
        self.threads = []
        self.threads_limit = THREADS_LIMIT
        self.semaphore = threading.Semaphore(self.threads_limit)

        self.chunk_meshes = {}
        self.chunks_loading = set()
        self.chunks_to_load_dic = {}
        self.chunks_to_load_set = set()
        self.tasks_per_frame = TASKS_PER_FRAME
    
    def load_objects(self):
        # Starting base
        position = glm.vec3(0, 0, 0)
        position = self.avoid_cliffs(position)
        position.y = max(0, position.y) + 0.02 * HEIGHT_SCALE
        starting_base = StartingBase(self.app, self.app.meshes["starting_base"], position)
        self.objects.append(starting_base)
        
        rng = np.random.default_rng(self.seed)
        for i in range(self.num_heatcores):
            radius = rng.uniform(1, 2)
            angle = rng.uniform(0, 360)
            position = radius * glm.vec3(np.cos(np.radians(angle)), 0.0, np.sin(np.radians(angle)))
            
            position = self.avoid_water(position)
            position.y += 0.005 * HEIGHT_SCALE
            print(f"Heatcore {i} at position: {position}")
            heatcore = HeatCore(self.app, self.app.meshes["heatcore"], position)
            
            self.objects.append(heatcore)
        
    
    def init_shader(self):
        # light
        self.chunk_shader['light.position'].write(self.app.light.position)
        self.chunk_shader['light.Ia'].write(self.app.light.Ia)
        self.chunk_shader['light.Id'].write(self.app.light.Id)
        self.chunk_shader['light.Is'].write(self.app.light.Is)
        # mvp
        colors_256 = np.zeros((256, 3), dtype=np.float32)
        colors_256[:len(self.color_params.colors)] = self.color_params.colors
        colors_256 *= 1 / 255
        self.chunk_shader['colors'].write(colors_256.tobytes())
        self.chunk_shader['m_proj'].write(self.app.camera.m_proj)
        self.chunk_shader['m_model'].write(glm.mat4())

    def generate_chunk_worker(self, coord, detail):
        """Worker function for generating chunks and rendering."""
        chunk = ChunkTerrain(self.noise, coord[0], coord[1], CHUNK_SCALE)
        chunk_mesh = DelaunayChunkMesh(self.app, chunk)
        chunk_mesh.update_detail(detail)
        self.result_queue.put((coord, chunk_mesh))
    
    def generate_chunks(self):
        """Update chunks and load new ones."""
        player_position = self.app.player.position.xz / (CHUNK_SIZE * CHUNK_SCALE)
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

    def update_chunks(self):
        """Distribute chunk generation tasks across multiple frames."""
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
        self.chunk_shader['m_proj'].write(self.app.camera.m_proj)
        self.chunk_shader['m_view'].write(self.app.camera.view_matrix)
        self.chunk_shader['camPos'].write(self.app.camera.position)
        self.chunk_shader['time'].write(struct.pack('f', self.app.time))

    def update(self):
        self.player.update()
        self.camera.update()
        
        self.generate_chunks()
        self.update_chunks()
        self.update_shader()

    def render(self):
        """Render all chunks within the active radius."""
        self.update()
        player_position = self.app.camera.position / (CHUNK_SIZE * CHUNK_SCALE)

        for (i, j) in self.chunk_meshes.keys():
            chunk_mesh = self.chunk_meshes[(i, j)]
            if chunk_mesh.detail is None:
                continue
            distance_sq = (player_position.x - i - 0.5) ** 2 + (player_position.z - j - 0.5) ** 2
            chunk_mesh.update_model_matrix(glm.sqrt(distance_sq))
            chunk_mesh.render()
        
        for obj in self.objects:
            print(type(obj))
            print(obj.position)
            obj.render()
        
        self.player.mesh.render()

    def destroy(self):
        """Clean up resources."""
        self.semaphore.acquire()
        for t in self.threads:
            t.join()

        [mesh.destroy() for mesh in self.chunk_meshes.values()]
        self.chunk_shader.release()

    def get_perlin_height(self, position: glm.vec3, octaves: int = 1):
        sample_x, sample_y = np.array(position.xz / CHUNK_SCALE)
        noise_value = self.noise.noise_value(sample_x, sample_y, octaves=octaves)
        height_value = self.noise.height_params.height_from_noise(noise_value)
        return height_value * CHUNK_SCALE

    def get_normal(self, position: glm.vec3, octaves: int = 1, get_height: bool = False):
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

    def avoid_water(self, position: glm.vec3):
        i = 0
        height, terrain_normal = self.get_normal(position, 1, True)
        while height < 0.01 * HEIGHT_SCALE:
            position -= flatten(terrain_normal)
            height, terrain_normal = self.get_normal(position, 1, True)
            i += 1
            print()
            print(f"Iteration {i}")
            print(f"Position {position} with height {height}")
            print(f"Normal: {terrain_normal}")
            print(f"While loop condition: {height} < {0.01 * HEIGHT_SCALE}")
        print(f"Iteration of avoiding water: {i}")
        return flatten(position) + glm.vec3(0, height, 0)
    
    def avoid_cliffs(self, position: glm.vec3):
        i = 0
        height, terrain_normal = self.get_normal(position, 1, True)
        terrain_normal = flatten(terrain_normal)
        while terrain_normal.y < glm.sin(glm.radians(75)):
            position -= flatten(terrain_normal)
            height, terrain_normal = self.get_normal(position, 1, True)
            i += 1
            print()
            print(f"Iteration {i}")
            print(f"Position {position} with height {height}")
            print(f"Normal: {terrain_normal}")
            print(f"While loop condition: {terrain_normal.y} < {glm.sin(glm.radians(75))}")
        print(f"Iteration of avoiding cliff: {i}")
        return flatten(position) + glm.vec3(0, height, 0)
    
    def cinematique_entree(self):
        running = True
        while running:
            self.generate_chunks()
            self.update_chunks()
            if len(self.chunks_to_load_set) == 0 and len(self.chunks_loading) == 0:
                running = False
            
            pg.display.flip()
            self.app.clock.tick(FPS)
        self.load_objects()
        
        self.player = Pl
        pass