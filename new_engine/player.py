import glm
import pygame as pg

from new_engine.meshes.ship_mesh import ShipMesh
from new_engine.options import CHUNK_SCALE, HEIGHT_SCALE

FORWARD_FRICTION = 0.98
YAW_FRICTION = 0.97
ROLL_FRICTION = 0.95
YAW_ACCELERATION = 0.0001
MAX_YAW_SPEED = 0.001
FORWARD_ACCELERATION = 0.001 * CHUNK_SCALE
BACKWARD_ACCELERATION = 0.5 * FORWARD_ACCELERATION
ROLL_ACCELERATION = 0.001
MAX_ROLL_SPEED = 5.0
MAX_SPEED = 0.01 * CHUNK_SCALE
MIN_SPEED = - 0.5 * MAX_SPEED
CAMERA_ZOOM_SCALE = 0.5
CAMERA_SMOOTHNESS = 0.1

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
        print(self.roll, self.roll_velocity, self.roll_acceleration)

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

        print(f"Velocity: {self.velocity}")
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
        """Updates forward, right, and up vectors based on movement."""
        dt = self.app.delta_time
        rotation = glm.angleAxis(self.angular_velocity * dt, glm.vec3(0, 1, 0))
        self.forward = glm.normalize(glm.vec3(rotation * glm.vec4(self.forward, 0)))

        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))

        terrain_height = self.app.scene.get_height(self.position)
        target_height = terrain_height + HEIGHT_SCALE * 0.05
        self.position.y = glm.mix(self.position.y, target_height, 0.1)

        self.position += self.forward * self.velocity

    def update_camera(self):
        """Smoothly updates the camera position to follow the player with zoom and slight delay."""
        self.camera_zoom = glm.clamp(self.camera_zoom, 0.05, 3.0)
        self.pitch_offset = - (3.05 - self.camera_zoom) * 10

        target_position = self.position - (glm.tan(
            glm.radians(self.pitch_offset)) * self.up + self.forward) * self.camera_zoom * CAMERA_ZOOM_SCALE
        print(target_position)
        self.camera.position = glm.mix(self.camera.position, target_position, CAMERA_SMOOTHNESS)

        look_at_target = glm.mix(self.camera.position + self.camera.forward, self.position, CAMERA_SMOOTHNESS)
        self.camera.forward = glm.normalize(look_at_target - self.camera.position)

    def update_model_matrix(self):
        """Updates the model matrix for rendering."""
        translation = glm.translate(glm.mat4(1.0), self.position)
        look_at_matrix = glm.lookAt(glm.vec3(0.0), self.forward, self.up)

        self.m_model = translation * look_at_matrix

    def update(self):
        """Calls all update functions in order."""
        self.update_inputs()
        self.update_friction()
        self.clamp_velocities()
        self.update_vectors()
        self.update_camera()
        self.update_model_matrix()
