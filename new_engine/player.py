import glm
import pygame as pg
from new_engine.meshes.ship_mesh import ShipMesh
from new_engine.options import CHUNK_SCALE

FORWARD_FRICTION = 0.98
YAW_FRICTION = 0.97
YAW_ACCELERATION = 0.00005
MAX_YAW_SPEED = 0.08
FORWARD_ACCELERATION = 0.000003 * CHUNK_SCALE
BACKWARD_ACCELERATION = 0.5 * FORWARD_ACCELERATION
MAX_SPEED = 0.003 * CHUNK_SCALE
MIN_SPEED = - 0.5 * MAX_SPEED

def same_sign(a, b):
    return a * b >= 0

class Player:
    def __init__(self, app):
        self.app = app
        self.camera = app.camera
        self.position = glm.vec3(0, 0.5, 0)
        
        self.forward_velocity = 0.0
        self.yaw_velocity = 0.0
        self.forward_acceleration = 0.0
        self.yaw_acceleration = 0.0
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
        
        keys = pg.key.get_pressed()
        if keys[pg.K_z]:
            self.forward_acceleration += FORWARD_ACCELERATION * self.app.delta_time
            self.forward_key_pressed = True
        if keys[pg.K_s]:
            self.forward_acceleration -= BACKWARD_ACCELERATION * self.app.delta_time
            self.forward_key_pressed = True
        if keys[pg.K_d]:
            self.yaw_acceleration -= YAW_ACCELERATION * self.app.delta_time
            self.yaw_key_pressed = True
        if keys[pg.K_q]:
            self.yaw_acceleration += YAW_ACCELERATION * self.app.delta_time
            self.yaw_key_pressed = True
        if keys[pg.K_a]:
            self.pitch_offset -= 1
        if keys[pg.K_e]:
            self.pitch_offset += 1
    
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
        
        self.yaw += self.yaw_velocity * self.app.delta_time
        self.position += self.forward_movement * self.forward_velocity * self.app.delta_time
    
    def update_model_matrix(self):
        self.pitch = glm.clamp(self.pitch, -89.0, 89.0)
        self.roll = glm.clamp(self.roll, -180.0, 180.0)
        self.roll = self.yaw_velocity / max(0.001, self.app.delta_time)
        
        rotation = glm.mat4(1.0)
        rotation = glm.rotate(rotation, glm.radians(self.yaw), glm.vec3(0, 1, 0))
        self.forward_movement = glm.normalize(glm.vec3(rotation * glm.vec4(0, 0, -1, 0)))
        rotation = glm.rotate(rotation, glm.radians(self.pitch), glm.vec3(1, 0, 0))
        rotation = glm.rotate(rotation, glm.radians(self.roll), glm.vec3(0, 0, 1))
        
        self.forward = glm.normalize(glm.vec3(rotation * glm.vec4(0, 0, -1, 0)))
        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))
        
        # Apply an additional 90° rotation correction before translation
        correction_rotation = glm.rotate(glm.mat4(1.0), glm.radians(90), glm.vec3(0, 1, 0))
        rotation = correction_rotation * rotation

        self.m_model = glm.translate(glm.mat4(1.0), self.position) * rotation
    
    def update_camera(self):
        self.camera.position = self.position - self.forward - glm.sin(glm.radians(self.pitch_offset)) * self.up
        
        self.camera.yaw = self.yaw
        self.camera.pitch = self.pitch + self.pitch_offset
    
    def update(self):
        self.update_inputs()
        self.update_movement()
        self.update_model_matrix()
        self.update_camera()

    def render(self):
        self.mesh.render()