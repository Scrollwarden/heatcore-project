import numpy as np
import glm
import os

MATERIAL_INFO_TYPE = {'Ns', 'Ka', 'Kd', 'Ks', 'Ke', 'Ni', 'd', 'illum'}

def load_materials(mtl_path):
    """Parse the .mtl file to extract material colors."""
    materials = {}
    current_material = None
    
    path = os.path.splitext(mtl_path)[0] + ".mtl"

    with open(path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if not parts:
                continue

            if parts[0] == "newmtl":
                current_material = parts[1]
                materials[current_material] = {"Kd": [1.0, 1.0, 1.0]}  # Default white
            elif parts[0] in MATERIAL_INFO_TYPE and len(parts) >= 2:
                materials[current_material][parts[0]] = list(map(float, parts[1:]))

    return materials


def load_triangles(obj_path):
    """Load the triangles of a obj

    Args:
        obj_path (str): the path (relative or absolute) to the obj, adding the extension is optional.
    
    Return:
        vertices (np.array): All the unique vertices of the obj
        normals (np.array): All the unique normals of the obj
        faces (np.array): List of indices for vertices and normal
        face_material (np.array): List of the material for each face
    """
    vertices = []
    normals = []
    faces = []
    face_materials = []
    
    path = os.path.splitext(obj_path)[0] + ".obj"

    current_material = None
    with open(path, 'r') as file:
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
    return vertices, normals, faces, face_materials


def load_vertex_data_obj(path, scale = 1.0, transform_matrix = glm.mat4(1.0)):
    """Load an .obj file and assign colors from its corresponding .mtl file."""
    
    # Step 1: Load materials
    materials = load_materials(path)
    vertices, normals, faces, face_materials = load_triangles(path)

    output = []
    # Step 2: Process faces
    for i, (face, normal_indices) in enumerate(faces):
        if len(face) != 3:
            continue
        v0, v1, v2 = vertices[face]  # Extract 3 vertices of the face
        
        computed_normal, _, _ = normals[normal_indices]
        
        # Get material color
        material_name = face_materials[i]
        color = materials.get(material_name, {"Kd": [1.0, 1.0, 1.0]})["Kd"]

        transformed_normal = list(glm.normalize(glm.mat3(glm.transpose(glm.inverse(transform_matrix))) * computed_normal))

        # Append vertex data (pos, normal, color)
        for v in [v0, v1, v2]:
            vertex = v * scale
            transformed_vertex = list(transform_matrix * vertex)
            output.append(np.concatenate([transformed_vertex, transformed_normal, color]))

    return np.array(output, dtype=np.float32)