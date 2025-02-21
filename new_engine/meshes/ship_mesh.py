import glm
from new_engine.meshes.obj_base_mesh import ObjMesh
from new_engine.options import PLAYER_SCALE

SHIP_FILE_PATH = "3D data/model obj/spaceship_player"

class ShipMesh(ObjMesh):
    """Ship mesh for rendering"""

    def __init__(self, app):
        super().__init__(app, 'ship')
        self.init_shader()
        self.init_vertex_data()
        self.init_context()
    
    def init_shader(self):
        # light
        self.shader_program['light.position'].write(self.app.light.position)
        self.shader_program['light.Ia'].write(self.app.light.Ia)
        self.shader_program['light.Id'].write(self.app.light.Id)
        self.shader_program['light.Is'].write(self.app.light.Is)
        # mvp
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
    
    def init_vertex_data(self):
        rotation = glm.rotate(glm.mat4(1.0), glm.radians(90), glm.vec3(0, 1, 0))
        self.load_object(SHIP_FILE_PATH, PLAYER_SCALE, rotation)
        print(self.vertex_data)
