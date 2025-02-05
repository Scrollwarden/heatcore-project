import pywavefront
import numpy as np
import os

DIR_PATH = os.path.dirname(os.path.abspath(__file__))


import numpy as np

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


def load_obj_with_colors(obj_path, mtl_path):
    """Load an .obj file and assign colors from its corresponding .mtl file."""
    vertices = []
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

            elif parts[0] == "usemtl":  # Assign material to next faces
                current_material = parts[1]

            elif parts[0] == "f":  # Face definition
                face_indices = [int(p.split('/')[0]) - 1 for p in parts[1:]]
                faces.append(face_indices)
                face_materials.append(current_material)  # Store material for this face

    vertices = np.array(vertices, dtype=np.float32)
    output = []

    # Step 2: Process faces
    for i, face in enumerate(faces):
        print(face)
        v0, v1, v2 = vertices[face]  # Extract 3 vertices of the face
        
        # Compute normal using cross product
        normal = np.cross(v1 - v0, v2 - v0)
        normal /= np.linalg.norm(normal)  # Normalize
        
        # Get material color
        material_name = face_materials[i]
        color = [1.0, 1.0, 1.0] # materials.get(material_name, {"Kd": [1.0, 1.0, 1.0]})["Kd"]
        
        # Append vertex data (pos, normal, color)
        for v in [v0, v1, v2]:
            output.append(np.concatenate([v, normal, color]))

    return np.array(output, dtype=np.float32)


def detect_flat_triangles(obj_path):
    """Detects and prints line numbers of flat (degenerate) triangles in an .obj file."""
    vertices = []
    flat_faces = []

    with open(obj_path, 'r') as file:
        for line_num, line in enumerate(file, start=1):
            parts = line.strip().split()
            if not parts:
                continue

            if parts[0] == "v":  # Store vertex positions
                vertices.append(list(map(float, parts[1:4])))

            elif parts[0] == "f":  # Face definition
                face_indices = [int(p.split('/')[0]) - 1 for p in parts[1:]]
                if len(face_indices) != 3:
                    continue  # Ignore non-triangular faces
                
                # Get triangle vertices
                v0, v1, v2 = np.array(vertices)[face_indices]
                
                # Compute normal
                normal = np.cross(v1 - v0, v2 - v0)
                if np.linalg.norm(normal) == 0:
                    flat_faces.append(line_num)

    # Print results
    if flat_faces:
        print(f"Flat triangles detected on lines: {flat_faces}")
        print(f"Total flat triangles: {len(flat_faces)}")
    else:
        print("No flat triangles detected.")
    
    return flat_faces  # Return the list if needed

path = f"{DIR_PATH}/../3D data/obj/spaceship_player.obj"

# Example usage:
list_flat_triangles = detect_flat_triangles(path)
list_flat_triangles = detect_flat_triangles(f"{DIR_PATH}/test.txt")
list_flat_triangles = load_obj_with_colors(f"{DIR_PATH}/test.txt", "")