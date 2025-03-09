import glm
import pygame as pg
import numpy as np
import enum

from new_engine.options import FPS, CHUNK_SCALE, HEIGHT_SCALE, CHUNK_SIZE, NUM_OCTAVES

CAMERA_ZOOM_SCALE = 0.5
ROLL_INTENSITY = 50.0



ROLL_FRICTION = 0.95
MAX_ROTATION_SPEED = 1.0
HOVER_HEIGHT = 0.2 * HEIGHT_SCALE * CHUNK_SCALE


def flatten(vector):
    return glm.vec3(vector.x, 0, vector.z)

class FollowTerrainPlayer:
    MAX_SPEED = 0.03 * CHUNK_SCALE # How many chunks per second
    MIN_SPEED = - 0.5 * MAX_SPEED
    MAX_ROTATION_SPEED = 60.0 / FPS # How many degrees per second

    # acceleration = speed / (t * FPS) <=> it takes t seconds to reach speed velocity
    FORWARD_ACCELERATION = MAX_SPEED / (1 * FPS)
    BACKWARD_ACCELERATION = MIN_SPEED / (1 * FPS)
    ANGULAR_ACCELERATION = MAX_ROTATION_SPEED / (1 * FPS)

    MOVEMENT_FRICTION = 0.98
    ROTATION_FRICTION = 0.97

    MAX_ROLL = 60.0 # How much you roll to the side

    def __init__(self, app, position=glm.vec3(0.0, 1.0, 0.0)):
        self.app = app
        self.camera = app.planet.camera
        self.camera_zoom = 0.2
        self.position = glm.vec3(position)
        
        # Movement physics
        self.velocity = 0.0
        self.angular_velocity = 0.0
        
        # Orientation
        self.rotation = 0.0
        self.forward = glm.vec3(0, 0, -1)
        self.up = glm.vec3(0, 1, 0)
        self.right = glm.cross(self.forward, self.up)
        
        # Model matrix
        self.m_model = glm.mat4(1.0)
        self.mesh = app.meshes["spaceship"]
    
    def handle_inputs(self):
        """Handles key inputs and updates acceleration values."""
        acceleration = 0.0
        angular_velocity = 0.0

        keys = pg.key.get_pressed()
        if keys[pg.K_z]:
            acceleration += self.FORWARD_ACCELERATION
        if keys[pg.K_s]:
            acceleration += self.BACKWARD_ACCELERATION
        if keys[pg.K_d]:
            angular_velocity += 0.003
        if keys[pg.K_q]:
            angular_velocity -= 0.003

        self.velocity += acceleration * self.app.delta_time
        self.angular_velocity += angular_velocity * self.app.delta_time
    
    def apply_friction(self):
        """Applies friction to gradually slow down movement and rotation."""
        self.velocity *= self.MOVEMENT_FRICTION
        self.angular_velocity *= self.ROTATION_FRICTION
    
    def clamp_velocities(self):
        """Ensures velocity and angular velocity remain within limits."""
        self.velocity = glm.clamp(self.velocity, self.MIN_SPEED, self.MAX_SPEED)
        self.angular_velocity = glm.clamp(self.angular_velocity, -self.MAX_ROTATION_SPEED, self.MAX_ROTATION_SPEED)
    
    def update_vectors(self):
        """Updates the forward, up, and right vectors based on terrain normal."""
        self.rotation += self.angular_velocity
        angle_cos, angle_sin = glm.cos(glm.radians(self.rotation)), glm.sin(glm.radians(self.rotation))
        self.forward = glm.vec3(angle_cos, 0, angle_sin)
        self.right = glm.vec3(angle_sin, 0, - angle_cos)
        
        # Sample terrain height at different positions to get a smooth normal
        vec_forward = glm.normalize(self.forward) * 0.05 * CHUNK_SCALE * CHUNK_SIZE
        vec_right = glm.normalize(self.right) * 0.05 * CHUNK_SCALE * CHUNK_SIZE
        terrain_height = self.app.planet.get_perlin_height(self.position, 2)
        forward_height = self.app.planet.get_perlin_height(self.position + vec_forward, 2)
        right_height = self.app.planet.get_perlin_height(self.position + vec_right, 2)
        terrain_normal = - glm.normalize(glm.cross(
            glm.vec3(vec_right.x, right_height - terrain_height, vec_right.z),
            glm.vec3(vec_forward.x, forward_height - terrain_height, vec_forward.z)
        ))
        
        if terrain_height < 0:
            terrain_height = 0
            terrain_normal = glm.vec3(0, 1, 0)
        self.up = glm.mix(self.up, terrain_normal, 0.02)
        self.forward.y = - glm.dot(self.forward, self.up) / self.up.y
        self.forward = glm.normalize(self.forward)
        self.position += self.forward * self.velocity
        self.position.y = glm.mix(self.position.y, terrain_height + HOVER_HEIGHT, 0.02)
        
        if self.app.delta_time:
            roll_angle = glm.radians(self.angular_velocity * ROLL_INTENSITY / self.app.delta_time)
        else:
            roll_angle = 0
        rolled_normal = glm.rotate(self.up, roll_angle, self.forward)
        
        self.up = glm.normalize(self.up)
        self.right = glm.normalize(glm.cross(self.forward, rolled_normal))

    def update_camera(self):
        """Smoothly updates the camera position to follow the player with zoom and slight delay."""
        self.camera_zoom = glm.clamp(self.camera_zoom, 0.05, 2.0)
        pitch_offset = glm.radians((2.05 - self.camera_zoom) * 10)
        camera_displacement = - self.forward + glm.tan(pitch_offset) * self.up
        camera_position_vector = camera_displacement * self.camera_zoom * CAMERA_ZOOM_SCALE
        camera_position = self.position + camera_position_vector

        """num_step = 10
        current_power = 1.0
        camera_terrain_height = self.app.planet.get_perlin_height(camera_position, 2) + 0.01 * HEIGHT_SCALE
        in_base = glm.length2(flatten(camera_position), flatten(self.app.planet.starting_base.position)) < CHUNK_SCALE
        in_walls = camera_position.y < camera_terrain_height
        if in_base or in_walls:
            for i in range(10):
                current_power *= 0.5
                if glm.length2(flatten(camera_position), flatten(self.app.planet.starting_base.position)) < CHUNK_SCALE:
                    camera_position -= camera_position_vector * current_power
                elif camera_position.y < self.app.planet.get_perlin_height(camera_position, 2) + 0.01 * HEIGHT_SCALE:
                    camera_position += camera_position_vector * current_power
                num_step -= 1"""

        self.camera.position = camera_position
        self.camera.forward = self.position + 0.02 * self.up - self.camera.position
        self.camera.forward = glm.normalize(glm.vec3(self.camera.forward.x, 0, self.camera.forward.z))
        self.camera.up = glm.vec3(0, 1, 0)
        
        mouse_clicks = pg.mouse.get_pressed()
        self.camera.right_click = mouse_clicks[2]
        
    def update_model_matrix(self):
        """Updates the model matrix for rendering with the correct orientation."""
        translation = glm.translate(glm.mat4(1.0), self.position)

        rotation = glm.mat4(
            glm.vec4(self.right, 0.0),
            glm.vec4(self.up, 0.0),
            glm.vec4(- self.forward, 0.0),
            glm.vec4(0, 0, 0, 1)
        )

        self.m_model = translation * rotation

    def update(self):
        self.handle_inputs()
        self.apply_friction()
        self.clamp_velocities()
        self.update_vectors()
        self.update_camera()

        self.update_model_matrix()
        self.mesh.shader_program['m_model'].write(self.m_model)
    
    def render(self):
        self.mesh.render()
