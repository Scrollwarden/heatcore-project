import glm
import pygame as pg

FOV = 50
NEAR = 0.01
FAR = 100
SPEED = 0.001
SENSITIVITY = 0.05

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
        pg.mouse.set_pos((800, 450))
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

class Light:
    def __init__(self, position=(0, 5.0, 0), color=(1, 1, 1)):
        self.position = glm.vec3(position)
        self.color = glm.vec3(color)
        self.direction = glm.vec3(0)
        # intensities
        self.Ia = 1.0 * self.color  # ambient
        self.Id = 0.9 * self.color  # diffuse
        self.Is = 1.0 * self.color  # specular
        # view matrix
        self.m_view_light = self.get_view_matrix()

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.direction, glm.vec3(0, 1, 0))