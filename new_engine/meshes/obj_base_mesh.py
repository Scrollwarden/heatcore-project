from new_engine.meshes.base_mesh import BaseMesh
from new_engine.shader_program import open_shaders
from new_engine.meshes.load_objects import load_vertex_data_obj

class ObjMesh(BaseMesh):
    def __init__(self, app, shader_name):
        super().__init__()
        self.app = app
        self.context = self.app.context
        self.shader_program = open_shaders(self.app, shader_name)

        self.vbo_format = '3f 3f 3f'
        self.attrs = ('in_position', 'in_normal', 'in_color')

        self.vertex_data = None
    
    def init_shader(self): ...
    
    def init_vertex_data(self): ...
    
    def load_object(self, file_path, scale, rotation):
        self.vertex_data = load_vertex_data_obj(file_path, scale, rotation)

    def update_shader(self):
        self.shader_program['m_view'].write(self.app.camera.view_matrix)
        self.shader_program['camPos'].write(self.app.camera.position)
        self.shader_program['m_model'].write(self.app.player.m_model)
    
    def render(self):
        self.update_shader()
        self.vao.render()
