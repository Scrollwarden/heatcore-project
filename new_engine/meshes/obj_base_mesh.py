from new_engine.meshes.base_mesh import BaseMesh
from new_engine.shader_program import open_shaders
from new_engine.meshes.load_objects import load_vertex_data_obj
import glm

"""
class ObjMesh(BaseMesh):
    def __init__(self, app, shader_name):
        super().__init__()
        self.app = app
        self.context = self.app.context
        self.shader_program = open_shaders(self.app, shader_name)

        self.vbo_format = '3f 3f 3f'
        self.attrs = ('in_position', 'in_normal', 'in_color')

        self.vertex_data = None
    
    def load_object(self, file_path, scale, rotation):
        self.vertex_data = load_vertex_data_obj(file_path, scale, rotation)

    def update(self):
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
        self.shader_program['m_view'].write(self.app.camera.view_matrix)
        self.shader_program['camPos'].write(self.app.camera.position)
        self.shader_program['m_model'].write(self.app.player.m_model)


class DefaultObjMesh(ObjMesh):
    def __init__(self, app, object_name, 
                 position = (0, 0, 0), rotation = glm.mat4(), scale = 1.0):
        super().__init__(app, 'obj')
        self.position = glm.vec3(position)
        self.rotation = glm.mat4(rotation)
        self.scale = scale
        
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
        self.load_object(f"3D data/model obj/{self.object_name}", self.scale, self.rotation)
"""


class GameObjMesh(BaseMesh):
    """Mesh of objects loaded with .obj and .mtl
    Do not init in a thread worker ! It causes problem with OpenGL context"""
    def __init__(self, app, object_name, shader_name,
                 scale = 1.0, obj_transformation = glm.mat4()):
        super().__init__()
        self.app = app
        self.context = app.context
        self.shader_program = open_shaders(app, shader_name)
        
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
        self.shader_program['light.position'].write(self.app.planet.light.position)
        self.shader_program['light.Ia'].write(self.app.planet.light.Ia)
        self.shader_program['light.Id'].write(self.app.planet.light.Id)
        self.shader_program['light.Is'].write(self.app.planet.light.Is)

        self.shader_program['m_proj'].write(self.app.planet.camera.m_proj)
        self.shader_program['m_view'].write(self.app.planet.camera.view_matrix)
        self.shader_program['camPos'].write(self.app.planet.camera.position)
    
    def render(self):
        self.vao.render()

    def __repr__(self):
        load_string = ", NoVertices" if self.vertex_data is None else ""
        context_string = ", NoContext" if self.vao is None else ""
        return f"GameObjMesh<{self.name}{load_string}{context_string}>"