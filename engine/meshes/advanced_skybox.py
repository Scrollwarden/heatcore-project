import glm
import numpy as np
import pygame as pg
from engine.meshes.base_mesh import BaseMesh
from engine.shader_program import open_shaders


class AdvancedSkyBoxMesh(BaseMesh):
    """Mesh of advanced skybox
    Do not init in a thread worker ! It causes problem with OpenGL context"""
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.context = app.context
        self.vbo_format = "3f"
        self.attrs = ["in_position"]

        self.texture_path = "skybox1"
        self.texture = None
        self.init_texture_cube()

        self.init_vertex_data()
        self.init_shader()
        self.init_context()

    def init_shader(self):
        self.shader_program = open_shaders(self.app, "advanced_skybox")
        # self.shader_program['u_texture_skybox'] = 0
        # self.texture.use(location=0)

    def init_vertex_data(self):
        z = 0.9999 # Clipping space
        self.vertex_data = np.array([(-1, -1, z), (3, -1, z), (-1, 3, z)], dtype='f4')

    def init_texture_cube(self, ext='png'):
        faces = ['right', 'left', 'top', 'bottom'] + ['front', 'back'][::-1]
        # textures = [pg.image.load(dir_path + f'{face}.{ext}').convert() for face in faces]
        textures = []
        for face in faces:
            texture = pg.image.load(f"engine/textures/{self.texture_path}/{face}.{ext}").convert()
            if face in ['right', 'left', 'front', 'back']:
                texture = pg.transform.flip(texture, flip_x=True, flip_y=False)
            else:
                texture = pg.transform.flip(texture, flip_x=False, flip_y=True)
            textures.append(texture)

        size = textures[0].get_size()
        self.texture = self.context.texture_cube(size=size, components=3, data=None)

        for i in range(6):
            texture_data = pg.image.tostring(textures[i], 'RGB')
            self.texture.write(face=i, data=texture_data)

    def update(self):
        self.shader_program['u_sun_dir'].write(self.app.planet.light.direction)
        m_view = glm.mat4(glm.mat3(self.app.planet.camera.view_matrix))
        self.shader_program['m_invProjView'].write(glm.inverse(self.app.planet.camera.m_proj * m_view))
