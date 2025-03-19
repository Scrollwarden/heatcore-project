from base_mesh import BaseMesh
from shader_program import ShaderProgram
from load_objects import load_vertex_data_obj
import os
import glm

ABS_PATH = os.path.dirname(os.path.abspath(__file__))

class ObjMesh(BaseMesh):
    def __init__(self, app, shader_name):
        super().__init__()
        self.app = app
        self.context = self.app.context
        self.shader_object = ShaderProgram(app, shader_name)
        self.shader_program = self.shader_object.get_program()

        self.vbo_format = '3f 3f 3f'
        self.attrs = ('in_position', 'in_normal', 'in_color')

        self.vertex_data = None
    
    def init_shader(self): ...
    
    def init_vertex_data(self): ...
    
    def load_object(self, file_path, scale = 1.0, rotation = glm.mat4()):
        self.vertex_data = load_vertex_data_obj(file_path, scale, rotation)

    def update_shader(self):
        self.shader_program['m_view'].write(self.app.camera.view_matrix)
        self.shader_program['camPos'].write(self.app.camera.position)
    
    def render(self):
        self.update_shader()
        self.vao.render()


class DefaultObjMesh(ObjMesh):
    def __init__(self, app, object_name):
        super().__init__(app, 'shader')
        self.object_name = object_name
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
        self.load_object(os.path.join(ABS_PATH, "..", "..", "3D data", "model obj", self.object_name))