import glm
import math
import pygame as pg
from engine.options import SCREEN_WIDTH, SCREEN_HEIGHT, FOV, ZOOMED_FOV, NEAR, FAR, SPEED, SENSITIVITY

class Camera:
    def __init__(self, app, position=(0.1, 0.07, 0.1), yaw=0, pitch=-20):
        self.app = app
        self.aspect_ratio = app.window_size[0] / app.window_size[1]
        self.position = glm.vec3(position)
        self.up = glm.vec3(0, 1, 0)
        self.right = glm.vec3(1, 0, 0)
        self.forward = glm.vec3(0, 0, -1)
        self.movement_forward = glm.vec3(0, 0, -1)
        self.movement_right = glm.vec3(1, 0, 0)
        self.movement_up = glm.vec3(0, 1, 0)
        self.yaw = yaw
        self.pitch = pitch

        self.context = app.context
        self.m_proj = self.get_projection_matrix()
        self.view_matrix = self.get_view_matrix()

    def rotate(self):
        mouse_dx, mouse_dy = pg.mouse.get_rel()
        self.yaw += mouse_dx * SENSITIVITY
        self.pitch -= mouse_dy * SENSITIVITY
        self.pitch = max(-89, min(89, self.pitch))
        # Recenter the mouse
        #screen_width, screen_height = pg.display.get_surface().get_size()
        #pg.mouse.set_pos(screen_width // 2, screen_height // 2)

    def update_camera_vectors(self):
        yaw, pitch = glm.radians(self.yaw), glm.radians(self.pitch)

        self.forward.x = glm.cos(yaw) * glm.cos(pitch)
        self.forward.y = glm.sin(pitch)
        self.forward.z = glm.sin(yaw) * glm.cos(pitch)
        self.forward = glm.normalize(self.forward)

        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))

        self.movement_forward = glm.vec3(glm.cos(yaw), 0, glm.sin(yaw))
        self.movement_right = glm.vec3(-glm.sin(yaw), 0, glm.cos(yaw))

    def update(self):
        self.move()
        self.rotate()
        self.update_camera_vectors()
        self.view_matrix = self.get_view_matrix()

    def move(self):
        velocity = SPEED * self.app.delta_time
        keys = pg.key.get_pressed()
        if keys[pg.K_z]:
            self.position += self.movement_forward * velocity
        if keys[pg.K_s]:
            self.position -= self.movement_forward * velocity
        if keys[pg.K_d]:
            self.position += self.movement_right * velocity
        if keys[pg.K_q]:
            self.position -= self.movement_right * velocity
        if keys[pg.K_a]:
            self.position += self.movement_up * velocity
        if keys[pg.K_e]:
            self.position -= self.movement_up * velocity

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.position + self.forward, self.up)

    def get_projection_matrix(self):
        return glm.perspective(glm.radians(FOV), self.aspect_ratio, NEAR, FAR)


class CameraAlt:
    def __init__(self):
        self.position = glm.vec3(0, 0, 0)
        
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        
        self.forward = glm.vec3(0, 0, -1)
        self.right = glm.vec3(1, 0, 0)
        self.up = glm.vec3(0, 1, 0)
        
        self.m_proj = glm.perspective(glm.radians(FOV), SCREEN_WIDTH / SCREEN_HEIGHT, NEAR, FAR)
        self.view_matrix = glm.mat4(1.0)
    
    def update(self):
        # Clamp angles
        self.pitch = glm.clamp(self.pitch, -89.0, 89.0)
        self.roll = glm.clamp(self.roll, -180.0, 180.0)
        
        rotation = glm.mat4(1.0)
        rotation = glm.rotate(rotation, glm.radians(self.yaw), glm.vec3(0, 1, 0))
        rotation = glm.rotate(rotation, glm.radians(self.pitch), glm.vec3(1, 0, 0))
        rotation = glm.rotate(rotation, glm.radians(self.roll), glm.vec3(0, 0, 1))
        
        self.forward = glm.normalize(glm.vec3(rotation * glm.vec4(0, 0, -1, 0)))
        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))
        
        self.view_matrix = glm.lookAt(self.position, self.position + self.forward, self.up)


def sigmoid_function(x, a):
    """Can be used for clamp
    Smooth odd function (f(-x) = -f(x)) that has a derivative of 1 at 0 (f'(0) = 1)
    when x -> infty then f(x, a) -> a and f(-x, a) -> -a (parity of f)"""
    q = glm.exp(- 2 * x / a)
    denom = 2 / (1 + q)
    return a * (denom - 1)


MOUSE_SENSITIVITY = 0.1

class CameraFollow:
    """Class for the camera"""
    
    def __init__(self, app):
        """Class constructor

        Args:
            app (GraphicsEngine): the graphic engine class
        """
        self.app = app
        self.position = glm.vec3(0.0, 3.0, 0.0)
        self.fov = FOV
        self.right_click = False

        self.forward = glm.vec3(0, 0, -1)
        self.right = glm.vec3(1, 0, 0)
        self.up = glm.vec3(0, 1, 0)

        self.yaw = 0.0
        self.pitch = 0.0
        self.max_yaw = 120.0

        self.view_matrix = glm.mat4(1.0)
        self.m_proj = None
        self.update_perspective()
    
    def update_perspective(self):
        """Update the 4d perspective matrix for frustum clipping"""
        fov_target = ZOOMED_FOV if self.right_click else FOV
        self.fov = glm.mix(self.fov, fov_target, 0.25)
        self.m_proj = glm.perspective(glm.radians(self.fov), SCREEN_WIDTH / SCREEN_HEIGHT, NEAR, FAR)

    def update_mouse_look(self):
        """Update camera movement from mouse movement"""
        x, y = pg.mouse.get_pos()
        pg.mouse.set_pos((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        dx, dy = x - SCREEN_WIDTH // 2, y - SCREEN_HEIGHT // 2
        
        sensitivity = (0.1 if self.right_click else 1.0) * MOUSE_SENSITIVITY
        
        self.yaw = glm.clamp(self.yaw - dx * sensitivity, - self.max_yaw, self.max_yaw)
        self.pitch = glm.clamp(self.pitch - dy * sensitivity, - 89.0, 89.0)

    def update(self):
        """Update every bits for each frame"""
        self.update_perspective()
        self.update_mouse_look()
        
        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))
        
        yaw_rad = glm.radians(self.yaw)
        pitch_rad = glm.radians(self.pitch)
        rotated_forward = glm.rotate(glm.mat4(1.0), pitch_rad, self.right) * glm.vec4(self.forward, 1.0)
        rotated_forward = glm.rotate(glm.mat4(1.0), yaw_rad, self.up) * rotated_forward
        self.forward = glm.vec3(rotated_forward)
        
        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))

        self.view_matrix = glm.lookAt(self.position, self.position + self.forward + 0.1 * self.up, self.up)

