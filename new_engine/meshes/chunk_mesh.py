import numpy as np
from new_engine.meshes.base_mesh import BaseMesh
from new_engine.chunk import ChunkTerrain, CHUNK_SIZE, LG2_CS
from new_engine.options import MAX_FALL_DISTANCE, CHUNK_SHADER
import glm

class ChunkMesh(BaseMesh):
    """Chunk mesh that can update its details

    """

    DTYPE = np.dtype([
        ('position', np.float32, (3,)),  # 3 floats for vertex position (x, y, z)
        ('normal', np.float32, (3,)),  # 3 floats for face normal (nx, ny, nz)
        ('id', np.uint8)  # 1 unsigned int for triangle ID
    ])

    def __init__(self, app, chunk: ChunkTerrain):
        super().__init__()
        self.app = app
        self.chunk = chunk
        self.context = self.app.context
        self.shader_program = self.app.scene.shader_programs[CHUNK_SHADER].get_program()

        self.vbo_format = '3f 3f 1u1'
        self.attrs = ('in_position', 'in_normal', 'in_id')

        self.vertex_data = None
        self.detail = None

    def update_detail(self, new_level_of_detail: float | int):
        if not (type(new_level_of_detail) in (float, int) and 0 <= new_level_of_detail <= 1):
            raise ValueError(f"The level of detail ({new_level_of_detail}) is not correct,"
                             "it should be an float between 0 and 1")

        if self.chunk.detail is None or new_level_of_detail > self.chunk.detail:
            self.chunk.generate_detail(new_level_of_detail)

        step = 1 << int(LG2_CS * new_level_of_detail)
        self.vertex_data = np.zeros(6 * (CHUNK_SIZE // step) ** 2, dtype=self.DTYPE)

        index = 0
        for x in range(0, CHUNK_SIZE + 1, step):
            for y in range(0, CHUNK_SIZE + 1, step):
                if x == CHUNK_SIZE or y == CHUNK_SIZE:
                    continue

                # Triangles
                if (x // step * y // step) % 2 == 0:
                    triangles = (((x + step, y), (x, y), (x, y + step)),
                                 ((x, y + step), (x + step, y + step), (x + step, y)))
                else:
                    triangles = (((x, y), (x, y + step), (x + step, y + step)),
                                 ((x + step, y + step), (x + step, y), (x, y)))

                # ID taken from the highest point in the triangle
                for k, triangle in enumerate(triangles):
                    vertices = [self.chunk.vertices[i, j] for i, j in triangle]
                    normal = np.cross(vertices[2] - vertices[1], vertices[2] - vertices[0])
                    normal *= 1 / np.linalg.norm(normal)
                    face_id = max([self.chunk.id_data[i, j] for i, j in triangle])
                    for l in range(3):
                        self.vertex_data[index + 3 * k + l] = (vertices[l], normal, face_id)
                index += 6

        self.detail = new_level_of_detail

    def update_model_matrix(self, chunk_distance):
        fall_amount = (chunk_distance) ** 2 * MAX_FALL_DISTANCE * 0.01
        #tilt_angle = factor * glm.pi / 6

        translation = glm.translate(glm.mat4(1.0), glm.vec3(0, fall_amount, 0))

        m_model = translation
        self.shader_program['m_model'].write(m_model)

    def render(self):
        self.vao.render()

    def get_byte_size(self):
        return self.vertex_data.nbytes + self.chunk.get_chunk_size()

    def __repr__(self):
        load_string = ", NotLoaded" if self.vertex_data is None else ""
        context_string = ", NoContext" if self.vao is None else ""
        return f"ChunkMesh<{self.chunk}{load_string}{context_string}>"