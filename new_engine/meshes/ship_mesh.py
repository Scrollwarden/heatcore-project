import numpy as np
import glm
from new_engine.meshes.base_mesh import BaseMesh
from new_engine.shader_program import open_shaders
from new_engine.options import PLAYER_SCALE

SHIP_FILE_PATH = "3D data/obj/spaceship_player"

class ShipMesh(BaseMesh):
    """Ship mesh for rendering

    """

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.context = self.app.context
        self.shader_program = open_shaders(self.app, 'ship')

        self.vbo_format = '3f 3f 3f'
        self.attrs = ('in_position', 'in_normal', 'in_color')

        self.vertex_data = None
    
    def init_shader(self):
        # light
        # self.shader_program['light.position'].write(self.app.light.position)
        self.shader_program['light.Ia'].write(self.app.light.Ia)
        self.shader_program['light.Id'].write(self.app.light.Id)
        self.shader_program['light.Is'].write(self.app.light.Is)
        # mvp
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
    
    def init_vertex_data(self):
        rotation = glm.rotate(glm.mat4(1.0), glm.radians(90), glm.vec3(0, 1, 0))
        self.vertex_data = load_obj_with_colors(f"{SHIP_FILE_PATH}.obj", f"{SHIP_FILE_PATH}.mtl",
                                                PLAYER_SCALE, rotation)

    def update_shader(self):
        self.shader_program['m_view'].write(self.app.camera.view_matrix)
        self.shader_program['camPos'].write(self.app.camera.position)
        self.shader_program['m_model'].write(self.app.player.m_model)
    
    def render(self):
        self.update_shader()
        self.vao.render()




def load_mtl_colors(mtl_path):
    """Parse the .mtl file to extract material colors."""
    materials = {}
    current_material = None

    with open(mtl_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if not parts:
                continue

            if parts[0] == "newmtl":
                current_material = parts[1]
                materials[current_material] = {"Kd": [1.0, 1.0, 1.0]}  # Default white

            elif parts[0] == "Kd" and current_material:
                materials[current_material]["Kd"] = list(map(float, parts[1:4]))

    return materials


def load_obj_with_colors(obj_path, mtl_path, scale = 1.0, transform_matrix = glm.mat4(1.0)):
    """Load an .obj file and assign colors from its corresponding .mtl file."""
    vertices = []
    normals = []
    faces = []
    face_materials = []
    
    # Step 1: Load materials
    # materials = load_mtl_colors(mtl_path)

    current_material = None
    with open(obj_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if not parts:
                continue

            if parts[0] == "v":  # Vertex position
                vertices.append(list(map(float, parts[1:4])))

            elif parts[0] == "vn":  # Vertex normal
                normals.append(list(map(float, parts[1:4])))

            elif parts[0] == "usemtl":  # Assign material to next faces
                current_material = parts[1]

            
            elif parts[0] == "f":  # Face definition
                face_indices = [int(p.split('/')[0]) - 1 for p in parts[1:]]
                normal_indices = [int(p.split('/')[2]) - 1 if len(p.split('/')) > 2 else None for p in parts[1:]]
                faces.append((face_indices, normal_indices))
                face_materials.append(current_material)  # Store material for this face

    vertices = np.array(vertices, dtype=np.float32)
    normals = np.array(normals, dtype=np.float32)  # Ensure normals are in the correct format
    output = []

    # Step 2: Process faces
    for i, (face, normal_indices) in enumerate(faces):
        if len(face) != 3:
            continue
        v0, v1, v2 = vertices[face]  # Extract 3 vertices of the face
        
        # Compute normal using cross product
        normal = np.cross(v1 - v0, v2 - v0)
        if (norm := np.linalg.norm(normal)) == 0:
            continue
        computed_normal, _, _ = normals[normal_indices]
        normal /= norm  # Normalize
        for i in range(3):
            if computed_normal[i] - normal[i] >= 0.001:
                print(computed_normal, normal)
                break
        
        
        # Get material color
        material_name = face_materials[i]
        color = [1.0, 1.0, 1.0] # materials.get(material_name, {"Kd": [1.0, 1.0, 1.0]})["Kd"]

        transformed_normal = list(glm.normalize(glm.mat3(glm.transpose(glm.inverse(transform_matrix))) * normal))

        # Append vertex data (pos, normal, color)
        for v in [v0, v1, v2]:
            vertex = v * scale
            transformed_vertex = list(transform_matrix * vertex)
            output.append(np.concatenate([transformed_vertex, transformed_normal, color]))

    return np.array(output, dtype=np.float32)