from engine.meshes.base_mesh import BaseMesh
from engine.shader_program import open_shaders
from engine.meshes.load_objects import load_vertex_data_obj
import glm


class GameObjMesh(BaseMesh):
    """Mesh of objects loaded with .obj and .mtl
    Do not init in a thread worker ! It causes problem with OpenGL context"""
    def __init__(self, app, object_name, shader_name,
                 scale = 1.0, obj_transformation = glm.mat4()):
        super().__init__()
        self.app = app
        self.context = app.context
        self.shader_program = open_shaders(app, shader_name)
        # self.shadow_shader_program = self.app.planet.shadow_map
        
        self.name = object_name
        self.scale = scale
        self.obj_transformation = obj_transformation
        
        self.vbo_format = '3f 3f 3f'
        self.attrs = ('in_position', 'in_normal', 'in_color')

        self.init_vertex_data()
        self.init_context()
        # No need to init shader as it's updated in self.update()
    
    def init_vertex_data(self):
        self.vertex_data = load_vertex_data_obj(f"3D data/model obj/{self.name}",
                                                self.scale, self.obj_transformation)
    
    def update(self):
        self.shader_program['light.direction'].write(self.app.planet.light.direction)
        self.shader_program['light.Ia'].write(self.app.planet.light.Ia)
        self.shader_program['light.Id'].write(self.app.planet.light.Id)
        self.shader_program['light.Is'].write(self.app.planet.light.Is)

        self.shader_program['m_proj'].write(self.app.planet.camera.m_proj)
        self.shader_program['m_view'].write(self.app.planet.camera.view_matrix)
        self.shader_program['camPos'].write(self.app.planet.camera.position)
        
        # self.shadow_shader_program['m_proj'].write(self.app.planet.camera.m_proj)
        # self.shadow_shader_program['m_view_light'].write(self.app.planet.light.view_matrix)
    
    def render(self):
        self.vao.render()

    def __repr__(self):
        load_string = ", NoVertices" if self.vertex_data is None else ""
        context_string = ", NoContext" if self.vao is None else ""
        return f"GameObjMesh<{self.name}{load_string}{context_string}>"