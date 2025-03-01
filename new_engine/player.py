import glm
import pygame as pg
import numpy as np
import enum

from new_engine.meshes.ship_mesh import ShipMesh
from new_engine.options import CHUNK_SCALE, HEIGHT_SCALE, CHUNK_SIZE

FORWARD_FRICTION = 0.98
YAW_FRICTION = 0.97
ROLL_FRICTION = 0.95
YAW_ACCELERATION = 0.0001
MAX_YAW_SPEED = 0.001
FORWARD_ACCELERATION = 0.001 * CHUNK_SCALE
BACKWARD_ACCELERATION = 0.2 * FORWARD_ACCELERATION
ROLL_ACCELERATION = 0.001
MAX_ROLL_SPEED = 5.0
MAX_SPEED = 0.03 * CHUNK_SCALE
MIN_SPEED = - 0.5 * MAX_SPEED
CAMERA_ZOOM_SCALE = 0.5
CAMERA_SMOOTHNESS = 0.3
PITCH_SMOOTHNESS = 0.02

# Apply vertical velocity based on height difference
GRAVITY = 0.05  # Controls how fast the ship falls
BOUNCE_FORCE = 0.005  # Pushes the ship up when too low
DAMPING = 0.9  # Damping factor to avoid oscillations

def same_sign(a, b):
    return a * b >= 0

def transform(value, min_value, max_value, transform_function):
    x = (value - min_value) / (max_value - min_value)
    h = transform_function(x)
    return glm.lerp(min_value, max_value, h)

def sin_out_transform(value, min_value, max_value):
    return transform(value, min_value, max_value, lambda x: glm.sin(glm.radians(90 * x)))

def sin_in_transform(value, min_value, max_value):
    x = (value - min_value) / (max_value - min_value)
    h = glm.sin(glm.radians(90 * x - 90)) + 1
    return glm.lerp(min_value, max_value, h)

def sin_in_out_transform(value, min_value, max_value):
    x = (value - min_value) / (max_value - min_value)
    h = 0.5 * (glm.sin(glm.radians(180 * x - 90)) + 1)
    return glm.lerp(min_value, max_value, h)

def square_in_transform(value, min_value, max_value):
    x = (value - min_value) / (max_value - min_value)
    h = x ** 2
    return glm.lerp(min_value, max_value, h)

def nightmarish_function(value):
    return value ** 3 / (MAX_SPEED ** 2)



class Player:
    def __init__(self, app):
        self.app = app
        self.camera = app.camera
        self.camera_zoom = 1.0
        self.position = glm.vec3(5, 0.5, 5)

        # Physics attributes
        self.forward_acceleration = 0.0
        self.forward_velocity = 0.0

        self.yaw_acceleration = 0.0
        self.yaw_velocity = 0.0

        self.roll_acceleration = 0.0
        self.roll_velocity = 0.0

        self.pitch_offset = 0.0

        self.yaw_key_pressed = False
        self.forward_key_pressed = False
        
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        
        self.forward = glm.vec3(0, 0, -1)
        self.right = glm.vec3(1, 0, 0)
        self.up = glm.vec3(0, 1, 0)
        self.forward_movement = glm.vec3(0, 0, -1)
        
        self.m_model = glm.mat4(1.0)
        
        self.mesh = ShipMesh(app)
    
    def update_inputs(self):
        self.yaw_key_pressed = False
        self.forward_key_pressed = False
        self.forward_acceleration = 0.0
        self.yaw_acceleration = 0.0
        self.roll_acceleration = 0.0

        keys = pg.key.get_pressed()
        if keys[pg.K_d]:
            self.yaw_acceleration -= YAW_ACCELERATION
            self.yaw_key_pressed = True
        if keys[pg.K_q]:
            self.yaw_acceleration += YAW_ACCELERATION
            self.yaw_key_pressed = True
        if keys[pg.K_z]:
            self.forward_acceleration += FORWARD_ACCELERATION
            self.roll_acceleration *= 0.75
            self.forward_key_pressed = True
        if keys[pg.K_s]:
            self.forward_acceleration -= BACKWARD_ACCELERATION
            self.roll_acceleration *= 1.5
            self.forward_key_pressed = True


    def update_movement(self):
        if not self.yaw_key_pressed or not same_sign(self.yaw_velocity, self.yaw_acceleration):
            self.yaw_velocity *= YAW_FRICTION
            if abs(self.yaw_velocity) < 1e-5:
                self.yaw_velocity = 0.0
        
        if not self.forward_key_pressed or not same_sign(self.forward_velocity, self.forward_acceleration):
            self.forward_velocity *= FORWARD_FRICTION
            if abs(self.forward_velocity) < 1e-5:
                self.forward_velocity = 0.0

        
        self.yaw_velocity = glm.clamp(self.yaw_velocity + self.yaw_acceleration, 
                                      - MAX_YAW_SPEED, MAX_YAW_SPEED)
        self.forward_velocity = glm.clamp(self.forward_velocity + self.forward_acceleration,
                                          MIN_SPEED, MAX_SPEED)
        self.roll_velocity = glm.clamp(self.roll_velocity + self.roll_acceleration,
                                       - MAX_ROLL_SPEED, MAX_ROLL_SPEED)
        self.yaw += self.yaw_velocity * self.app.delta_time
        self.position += self.forward_movement * self.forward_velocity * self.app.delta_time
        self.roll += self.roll_velocity * self.app.delta_time
    
    def update_model_matrix(self):
        self.pitch = glm.clamp(self.pitch, -89.0, 89.0)
        self.roll = glm.clamp(self.yaw_velocity * 700, -70.0, 70.0)
        ship_roll = sin_in_out_transform(self.roll, -70.0, 70.0)

        # Correction matrix because the ship is sideways
        rotation = glm.mat4(1.0)
        rotation = glm.rotate(rotation, glm.radians(self.yaw), glm.vec3(0, 1, 0))
        self.forward_movement = glm.normalize(glm.vec3(rotation * glm.vec4(0, 0, -1, 0)))
        rotation = glm.rotate(rotation, glm.radians(self.pitch), glm.vec3(1, 0, 0))
        rotation = glm.rotate(rotation, glm.radians(ship_roll), glm.vec3(0, 0, 1))
        
        self.forward = glm.normalize(glm.vec3(rotation * glm.vec4(0, 0, -1, 0)))
        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))


        self.m_model = glm.translate(glm.mat4(1.0), self.position) * rotation
    
    def update_camera(self):
        self.camera_zoom = glm.clamp(self.camera_zoom, 0.05, 3.0)
        self.pitch_offset = - (3.05 - self.camera_zoom) * 10
        self.camera.position = self.position - (glm.tan(glm.radians(self.pitch_offset)) * self.up + self.forward) * self.camera_zoom * CAMERA_ZOOM_SCALE
        
        self.camera.yaw = self.yaw
        self.camera.pitch = self.pitch + self.pitch_offset
    
    def update(self):
        self.update_inputs()
        self.update_movement()
        self.update_model_matrix()
        self.update_camera()

    def render(self):
        self.mesh.render()



class PlayerFollow:
    def __init__(self, app):
        self.app = app
        self.camera = app.camera
        self.camera_zoom = 0.2
        self.position = glm.vec3(0.0, 1.0, 0.0)
        self.velocity = 0.0
        self.angular_velocity = 0.0
        self.vertical_velocity = 0.0

        self.forward = glm.vec3(0.0, 0.0, -1.0)
        self.right = glm.vec3(1.0, 0.0, 0.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)

        self.yaw_key_pressed = False
        self.forward_key_pressed = False

        self.m_model = glm.mat4(1.0)
        self.mesh = ShipMesh(app)

    def smooth_accel(self, input_value, factor=3.0):
        """Applies an ease-in/ease-out acceleration curve."""
        dt = self.app.delta_time
        return input_value * (1 - glm.exp(-factor * dt))

    def update_inputs(self):
        """Handles key inputs and updates acceleration values."""
        self.forward_key_pressed = False
        self.yaw_key_pressed = False

        acceleration = 0.0
        angular_acceleration = 0.0

        keys = pg.key.get_pressed()
        if keys[pg.K_z]:
            acceleration += FORWARD_ACCELERATION
            self.forward_key_pressed = True
        if keys[pg.K_s]:
            acceleration -= BACKWARD_ACCELERATION
            self.forward_key_pressed = True
        if keys[pg.K_d]:
            angular_acceleration -= YAW_ACCELERATION
            self.yaw_key_pressed = True
        if keys[pg.K_q]:
            angular_acceleration += YAW_ACCELERATION
            self.yaw_key_pressed = True

        self.velocity += self.smooth_accel(acceleration)
        self.angular_velocity += self.smooth_accel(angular_acceleration)

    def update_friction(self):
        """Applies friction over time to gradually reduce velocity."""
        dt = self.app.delta_time

        if not self.forward_key_pressed:
            self.velocity *= glm.exp(-FORWARD_FRICTION * dt)
            if abs(self.velocity) < 1e-5:
                self.velocity = 0.0
        if not self.yaw_key_pressed:
            self.angular_velocity *= glm.exp(-YAW_FRICTION * dt)
            if abs(self.angular_velocity) < 1e-5:
                self.angular_velocity = 0.0

    def clamp_velocities(self):
        """Clamps velocity and angular velocity to defined limits."""
        self.velocity = glm.clamp(self.velocity, 0.0, MAX_SPEED)
        self.angular_velocity = glm.clamp(self.angular_velocity, -MAX_YAW_SPEED, MAX_YAW_SPEED)
        self.camera_zoom = glm.clamp(self.camera_zoom, 0.05, 3.0)

    def update_vectors(self):
        """Updates forward, right, and up vectors based on movement, keeping forward parallel to terrain."""
        dt = self.app.delta_time
        rotation = glm.angleAxis(self.angular_velocity * dt, glm.vec3(0, 1, 0))
        self.forward = glm.normalize(glm.vec3(rotation * glm.vec4(self.forward, 0.0)))

        # Sample terrain height at different positions to get a smooth normal
        vec_forward = glm.normalize(self.forward) * 0.05 * CHUNK_SCALE * CHUNK_SIZE
        vec_right = glm.normalize(self.right) * 0.05 * CHUNK_SCALE * CHUNK_SIZE
        h_center = self.app.chunk_manager.get_perlin_height(self.position, 2)
        h_forward = self.app.chunk_manager.get_perlin_height(self.position + vec_forward, 2)
        h_right = self.app.chunk_manager.get_perlin_height(self.position + vec_right, 2)
        terrain_normal = glm.normalize(glm.cross(
            glm.vec3(vec_right.x, h_right - h_center, vec_right.z),
            glm.vec3(vec_forward.x, h_forward - h_center, vec_forward.z)
        ))

        # Adjust up vector
        self.up = glm.normalize(glm.mix(self.up, terrain_normal, PITCH_SMOOTHNESS))
        adjusted_forward = glm.normalize(self.forward - glm.dot(self.forward, self.up) * self.up)
        self.forward = glm.normalize(glm.mix(self.forward, adjusted_forward, PITCH_SMOOTHNESS))

        # Roll the ship
        roll_angle = glm.clamp(- 20.0 * self.angular_velocity, -glm.radians(25), glm.radians(25))
        roll_rotation = glm.angleAxis(roll_angle, self.forward)
        self.up = glm.normalize(glm.vec3(roll_rotation * glm.vec4(self.up, 0.0)))
        if self.up.y < 0.3:
            self.up = glm.normalize(glm.vec3(self.up.x, 0.3, self.up.z))
        self.right = glm.normalize(glm.cross(self.forward, self.up))

        # Update height of ship
        target_height = h_center + HEIGHT_SCALE * 0.01
        #self.position.y = glm.mix(self.position.y, target_height, PITCH_SMOOTHNESS)
        height_diff = self.position.y - target_height
        if height_diff < 0.0:  # Too low, push up
            force_amount = abs(height_diff)
            self.vertical_velocity += BOUNCE_FORCE * (force_amount ** 3 + 3 * force_amount)
        elif height_diff > 0.03 * HEIGHT_SCALE:  # Too high, push down
            force_amount = abs(height_diff if height_diff > HEIGHT_SCALE * 0.4 else 0)
            self.vertical_velocity -= GRAVITY * force_amount
        self.vertical_velocity *= DAMPING

        self.position.y += self.vertical_velocity
        self.position += self.forward * self.velocity

    def update_camera(self):
        """Smoothly updates the camera position to follow the player with zoom and slight delay."""
        self.camera_zoom = glm.clamp(self.camera_zoom, 0.05, 3.0)
        pitch_offset = - (3.05 - self.camera_zoom) * 10

        camera_forward = glm.normalize(glm.vec3(self.forward.x, 0.0, self.forward.z))
        target_position = self.position - (glm.tan(
            glm.radians(pitch_offset)) * self.up + camera_forward) * self.camera_zoom * CAMERA_ZOOM_SCALE
        self.camera.position = glm.mix(self.camera.position, target_position, CAMERA_SMOOTHNESS)

        look_at_target = glm.mix(self.camera.position + self.camera.forward, self.position, CAMERA_SMOOTHNESS)
        self.camera.forward = glm.normalize(look_at_target - self.camera.position)

    def update_model_matrix(self):
        """Updates the model matrix for rendering with the correct orientation."""
        translation = glm.translate(glm.mat4(1.0), self.position)

        # Construct rotation matrix using right, up, and forward vectors
        rotation = glm.mat4(
            glm.vec4(self.right, 0.0),  # X-axis
            glm.vec4(self.up, 0.0),  # Y-axis
            glm.vec4(-self.forward, 0.0),  # Z-axis (negated to fix the flipped model issue)
            glm.vec4(0, 0, 0, 1)  # Homogeneous coordinate
        )

        self.m_model = translation * rotation

    def update(self):
        """Calls all update functions in order."""
        self.update_inputs()
        self.update_friction()
        self.clamp_velocities()
        self.update_vectors()
        self.update_camera()
        self.update_model_matrix()

class PlayerNoChangeInHeight:
    def __init__(self, app, position = glm.vec3(0.0, 1.0, 0.0)):
        self.app = app
        self.camera = app.camera
        self.camera_zoom = 0.2
        self.position = glm.vec3(position)
        self.velocity = 0.0
        self.yaw = 0.0

        self.forward = glm.vec3(0.0, 0.0, -1.0)
        self.right = glm.vec3(1.0, 0.0, 0.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)

        self.yaw_key_pressed = False
        self.forward_key_pressed = False

        self.m_model = glm.mat4(1.0)
        self.mesh = ShipMesh(app)

    def smooth_accel(self, input_value, factor=3.0):
        """Applies an ease-in/ease-out acceleration curve."""
        dt = self.app.delta_time
        return input_value * (1 - glm.exp(-factor * dt))

    def update_inputs(self):
        """Handles key inputs and updates acceleration values."""
        self.forward_key_pressed = False
        self.yaw_key_pressed = False

        acceleration = 0.0
        angular_velocity = 0.0

        keys = pg.key.get_pressed()
        if keys[pg.K_z]:
            acceleration += FORWARD_ACCELERATION
            self.forward_key_pressed = True
        if keys[pg.K_s]:
            acceleration -= BACKWARD_ACCELERATION
            self.forward_key_pressed = True
        if keys[pg.K_d]:
            angular_velocity -= YAW_ACCELERATION
            self.yaw_key_pressed = True
        if keys[pg.K_q]:
            angular_velocity += YAW_ACCELERATION
            self.yaw_key_pressed = True

        self.velocity += self.smooth_accel(acceleration)
        self.yaw += self.smooth_accel(angular_velocity)

    def update_friction(self):
        """Applies friction over time to gradually reduce velocity."""
        dt = self.app.delta_time

        if not self.forward_key_pressed:
            self.velocity *= glm.exp(-FORWARD_FRICTION * dt)
            if abs(self.velocity) < 1e-5:
                self.velocity = 0.0
        if not self.yaw_key_pressed:
            self.yaw *= glm.exp(-0.002 * dt)
            if abs(self.yaw) < 1e-5:
                self.yaw = 0.0

    def clamp_velocities(self):
        """Clamps velocity and angular velocity to defined limits."""
        self.velocity = glm.clamp(self.velocity, 0.0, MAX_SPEED)
        self.yaw = glm.clamp(self.yaw, -MAX_YAW_SPEED, MAX_YAW_SPEED)
        self.camera_zoom = glm.clamp(self.camera_zoom, 0.05, 3.0)

    def update_vectors(self):
        dt = self.app.delta_time

        # Rotate forward vector for yaw
        rotation = glm.angleAxis(self.yaw * dt, glm.vec3(0, 1, 0))
        self.forward = glm.normalize(glm.vec3(rotation * glm.vec4(self.forward, 0.0)))

        # Roll the ship with yaw
        roll_angle = glm.clamp(- 200 * self.yaw, -glm.radians(60), glm.radians(60))
        roll_rotation = glm.angleAxis(roll_angle, self.forward)
        self.up = glm.normalize(glm.vec3(roll_rotation * glm.vec4(0.0, 1.0, 0.0, 0.0)))
        self.right = glm.normalize(glm.cross(self.forward, self.up))

        # Update position
        self.position += self.forward * self.velocity
        self.position.y = self.app.chunk_manager.get_perlin_height(self.position, 2) + HEIGHT_SCALE * 0.02

    def update_camera(self):
        """Smoothly updates the camera position to follow the player with zoom and slight delay."""
        self.camera_zoom = glm.clamp(self.camera_zoom, 0.05, 2.0)
        pitch_offset = glm.radians((self.camera_zoom - 2.05) * 10)
        camera_displacement = glm.tan(pitch_offset) * self.up + self.forward
        target_position = self.position - camera_displacement * self.camera_zoom * CAMERA_ZOOM_SCALE
        if self.yaw_key_pressed and not self.forward_key_pressed:
            self.camera.position = glm.mix(self.camera.position, target_position, 0.01)
        else:
            self.camera.position = glm.mix(self.camera.position, target_position, 0.04)

        look_at_target = glm.mix(self.camera.position + self.camera.forward, self.position, CAMERA_SMOOTHNESS)
        self.camera.forward = glm.normalize(look_at_target - self.camera.position)

    def update_model_matrix(self):
        """Updates the model matrix for rendering with the correct orientation."""
        translation = glm.translate(glm.mat4(1.0), self.position)

        # Construct rotation matrix using right, up, and forward vectors
        rotation = glm.mat4(
            glm.vec4(self.right, 0.0),  # X-axis
            glm.vec4(self.up, 0.0),  # Y-axis
            glm.vec4(- self.forward, 0.0),  # Z-axis (negated to fix the flipped model issue)
            glm.vec4(0, 0, 0, 1)  # Homogeneous coordinate
        )

        self.m_model = translation * rotation

    def update(self):
        self.update_inputs()
        self.update_friction()
        self.clamp_velocities()
        self.update_vectors()
        self.update_camera()
        self.update_model_matrix()

    def render(self):
        self.mesh.render()


class SatisfyingPlayer:
    def __init__(self, app, position=glm.vec3(0.0, 1.0, 0.0)):
        self.app = app
        self.camera = app.camera
        self.camera_zoom = 0.2
        self.position = glm.vec3(position)
        
        # Movement physics
        self.velocity = glm.vec3(0.0)
        self.angular_velocity = glm.vec3(0.0)
        
        # Orientation
        self.rotations = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self.forward = glm.vec3(0, 0, -1)
        self.up = glm.vec3(0, 1, 0)
        self.right = glm.cross(self.forward, self.up)
        
        # Model matrix
        self.m_model = glm.mat4(1.0)
        self.mesh = ShipMesh(app)

    def render(self):
        self.mesh.render()

MOVEMENT_FRICTION = 0.98
ROTATION_FRICTION = 0.97
ROLL_FRICTION = 0.95
MAX_ROTATION_SPEED = 1.0
HOVER_HEIGHT = 0.2 * HEIGHT_SCALE * CHUNK_SCALE
ROLL_INTENSITY = 50.0


class FollowTerrainPlayer:
    FORWARD_ACCELERATION = 0.001 * CHUNK_SCALE
    BACKWARD_ACCELERATION = 0.5 * FORWARD_ACCELERATION
    
    def __init__(self, app, position=glm.vec3(0.0, 1.0, 0.0)):
        self.app = app
        self.camera = app.camera
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
        self.mesh = ShipMesh(app)
        self.mesh.init_shader()
        self.mesh.init_vertex_data()
        self.mesh.init_context()
    
    def update(self):
        self.handle_inputs()
        self.apply_friction()
        self.clamp_velocities()
        self.update_vectors()
        self.update_camera()
        self.update_model_matrix()
    
    def handle_inputs(self):
        """Handles key inputs and updates acceleration values."""
        acceleration = 0.0
        angular_velocity = 0.0

        keys = pg.key.get_pressed()
        if keys[pg.K_z]:
            acceleration += self.FORWARD_ACCELERATION
        if keys[pg.K_s]:
            acceleration -= self.BACKWARD_ACCELERATION
        if keys[pg.K_d]:
            angular_velocity += 0.003
        if keys[pg.K_q]:
            angular_velocity -= 0.003

        self.velocity += acceleration * self.app.delta_time
        self.angular_velocity += angular_velocity * self.app.delta_time
    
    def apply_friction(self):
        """Applies friction to gradually slow down movement and rotation."""
        self.velocity *= MOVEMENT_FRICTION
        self.angular_velocity *= ROTATION_FRICTION
    
    def clamp_velocities(self):
        """Ensures velocity and angular velocity remain within limits."""
        self.velocity = glm.clamp(self.velocity, -MAX_SPEED, MAX_SPEED)
        self.angular_velocity = glm.clamp(self.angular_velocity, -MAX_ROTATION_SPEED, MAX_ROTATION_SPEED)
    
    def update_vectors(self):
        """Updates the forward, up, and right vectors based on terrain normal."""
        self.rotation += self.angular_velocity
        angle_cos, angle_sin = glm.cos(glm.radians(self.rotation)), glm.sin(glm.radians(self.rotation))
        self.forward = glm.vec3(angle_cos, 0, angle_sin)
        self.right = glm.vec3(angle_sin, 0, - angle_cos)
        
        # Sample terrain height at different positions to get a smooth normal
        vec_forward = glm.normalize(self.forward) * 0.05 * CHUNK_SCALE * CHUNK_SIZE
        vec_right = glm.normalize(self.right) * 0.05 * CHUNK_SCALE * CHUNK_SIZE
        terrain_height = self.app.chunk_manager.get_perlin_height(self.position, 2)
        forward_height = self.app.chunk_manager.get_perlin_height(self.position + vec_forward, 2)
        right_height = self.app.chunk_manager.get_perlin_height(self.position + vec_right, 2)
        terrain_normal = - glm.normalize(glm.cross(
            glm.vec3(vec_right.x, right_height - terrain_height, vec_right.z),
            glm.vec3(vec_forward.x, forward_height - terrain_height, vec_forward.z)
        ))
        
        if terrain_height < 0:
            terrain_height = 0
            terrain_normal = glm.vec3(0, 1, 0)
        self.up = glm.mix(self.up, terrain_normal, 0.01)
        self.forward.y = - glm.dot(self.forward, self.up) / self.up.y
        self.forward = glm.normalize(self.forward)
        self.position += self.forward * self.velocity
        self.position.y = glm.mix(self.position.y, terrain_height + HOVER_HEIGHT, 0.01)
        
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
        pitch_offset = glm.radians((self.camera_zoom - 2.05) * 10)
        camera_displacement = glm.tan(pitch_offset) * self.up + self.forward
        self.camera.position = self.position - camera_displacement * self.camera_zoom * CAMERA_ZOOM_SCALE

        self.camera.forward = glm.normalize(self.position + 0.02 * self.up - self.camera.position)
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
    
    def render(self):
        self.mesh.render()
