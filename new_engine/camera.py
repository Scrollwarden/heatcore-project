import glm
import pygame as pg

FOV = 50
NEAR = 0.1
FAR = 1000
SPEED = 0.01
SENSITIVITY = 0.05

class Camera:
    def __init__(self, app, position=(0, 0, 4), yaw=-90, pitch=0):
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
        self.m_view = self.get_view_matrix()
        self.view_matrix = self.get_view_matrix()

    def rotate(self):
        mouse_dx, mouse_dy = pg.mouse.get_rel()
        self.yaw += mouse_dx * SENSITIVITY
        self.pitch -= mouse_dy * SENSITIVITY
        self.pitch = max(-89, min(89, self.pitch))
        # Recenter the mouse
        screen_width, screen_height = pg.display.get_surface().get_size()
        pg.mouse.set_pos(screen_width // 2, screen_height // 2)

    def update_camera_vectors(self):
        yaw, pitch = glm.radians(self.yaw), glm.radians(self.pitch)

        self.forward.x = glm.cos(yaw) * glm.cos(pitch)
        self.forward.y = glm.sin(pitch)
        self.forward.z = glm.sin(yaw) * glm.cos(pitch)
        self.forward = glm.normalize(self.forward)

        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))

        self.movement_forward.x = glm.cos(yaw)
        self.movement_forward.y = 0
        self.movement_forward.z = glm.sin(yaw)
        self.movement_forward = glm.normalize(self.movement_forward)
        self.movement_right = glm.normalize(glm.cross(self.movement_forward, glm.vec3(0, 1, 0)))

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

