import numpy as np
from new_engine.meshes.base_mesh import BaseMesh


class ChunkMesh(BaseMesh):
    def __init__(self, app, chunk, init_context: bool = True):
        super().__init__()
        self.app = app
        self.chunk = chunk
        self.context = self.app.context
        self.shader_program = self.app.scene.shader_programs['chunk'].get_program()

        self.vbo_format = '3f 3f 1u1'
        self.attrs = ('in_position', 'in_normal', 'in_id')
        self.init_without_context()
        if init_context:
            self.init_context()

    def init_without_context(self):
        num_triangles = len(self.chunk.triangles)

        dtype = np.dtype([
            ('position', np.float32, (3,)),  # 3 floats for vertex position (x, y, z)
            ('normal', np.float32, (3,)),  # 3 floats for face normal (nx, ny, nz)
            ('id', np.uint8)  # 1 unsigned int for triangle ID
        ])
        self.vertex_data = np.zeros(num_triangles * 3, dtype=dtype)

        for index, triangle in enumerate(self.chunk.triangles):
            vertices = np.array([self.chunk.vertices[i] for i in triangle], dtype=np.float32)
            normal = np.cross(vertices[1] - vertices[0], vertices[2] - vertices[0])
            normal = normal / np.linalg.norm(normal)
            face_id = self.chunk.triangle_ids[index]

            for i in range(3):
                self.vertex_data[3 * index + i] = (vertices[i], normal, face_id)

    def __repr__(self):
        return f"ChunkMesh<{self.chunk}>"