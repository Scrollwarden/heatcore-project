import numpy as np
import glm
import os, time

ABS_PATH = os.path.dirname(os.path.abspath(__file__))


class Cube:
    def __init__(self, app):
        self.app = app
        self.context = app.context
        self.vbo = self.get_vbo()
        self.shader_program = self.get_shader_program('default')
        self.vao = self.get_vao()
        self.m_model = glm.mat4()
        self.on_init()

    def update(self):
        self.shader_program['m_view'].write(self.app.camera.view_matrix)
        self.shader_program['camPos'].write(self.app.camera.position)

    def on_init(self):
        # light
        self.shader_program['light.position'].write(self.app.light.position)
        self.shader_program['light.Ia'].write(self.app.light.Ia)
        self.shader_program['light.Id'].write(self.app.light.Id)
        self.shader_program['light.Is'].write(self.app.light.Is)
        # mvp
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['m_model'].write(self.m_model)

    def render(self):
        self.update()
        self.vao.render()

    def destroy(self):
        self.vbo.release()
        self.shader_program.release()
        self.vao.release()

    def get_vao(self):
        vao = self.context.vertex_array(self.shader_program,
                                        [(self.vbo, '3f 3f 3f', 'in_position', 'in_normal', 'in_color')])
        return vao

    def get_vertex_data(self):
        vertices = [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
                    (-1, 1, -1), (-1, -1, -1), (1, -1, -1), (1, 1, -1)]
        indices = [(0, 2, 3), (0, 1, 2),
                   (1, 7, 2), (1, 6, 7),
                   (6, 5, 4), (4, 7, 6),
                   (3, 4, 5), (3, 5, 0),
                   (3, 7, 4), (3, 2, 7),
                   (0, 6, 1), (0, 5, 6)]

        vertex_data = []
        for inds in indices:
            a, b, c = [glm.vec3(position) for position in (vertices[i] for i in inds)]
            normal = glm.cross(c - a, a - b)
            color = (1.0, 0.0, 0.0)
            vertex_data.append((*a, *normal, *color))
            vertex_data.append((*b, *normal, *color))
            vertex_data.append((*c, *normal, *color))

        vertex_data = np.array(vertex_data, dtype=np.float32)
        return vertex_data

    def get_vbo(self):
        vertex_data = self.get_vertex_data()
        vbo = self.context.buffer(vertex_data)
        return vbo

    def get_shader_program(self, shader_name):
        with open(f"{ABS_PATH}/shaders/{shader_name}.vert") as file:
            vertex_shader = file.read()

        with open(f"{ABS_PATH}/shaders/{shader_name}.frag") as file:
            fragment_shader = file.read()

        program = self.context.program(vertex_shader, fragment_shader)
        return program


class ChunkModel:
    def __init__(self, app, chunk):
        self.app = app
        self.context = app.context
        self.chunk_coord = chunk.coord

        self.coord_scale = 5
        self.vertex_data = self.get_vertex_data(chunk)
        self.m_model = glm.mat4()
        self.shader_program = None
        self.vbo = None
        self.vao = None

    def init_context(self):
        self.shader_program = self.get_shader_program('default')
        self.vbo = self.get_vbo()
        self.vao = self.get_vao()
        self.init_shader_program()

    def update(self):
        self.shader_program['m_view'].write(self.app.camera.view_matrix)
        self.shader_program['camPos'].write(self.app.camera.position)

    def init_shader_program(self):
        # light
        self.shader_program['light.position'].write(self.app.light.position)
        self.shader_program['light.Ia'].write(self.app.light.Ia)
        self.shader_program['light.Id'].write(self.app.light.Id)
        self.shader_program['light.Is'].write(self.app.light.Is)
        # mvp
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['m_model'].write(self.m_model)

    def reset_data(self, chunk):
        self.vbo = self.get_vbo(chunk)
        self.vao = self.get_vao()

    def get_vertex_data(self, chunk):
        num_triangles = len(chunk.triangles)
        num_vertices = num_triangles * 3  # 3 vertices per triangle

        vertex_data = np.zeros((num_vertices, 9), dtype=np.float32)

        scaled_vertices = self.coord_scale * chunk.vertices

        for i in range(num_triangles):
            triangle, color = chunk.triangles[i], chunk.colors[i]
            a, b, c = (scaled_vertices[j] for j in triangle)
            nx, ny, nz = glm.cross(c - a, a - b)
            red, green, blue = color / 255.0

            base_index = i * 3
            vertex_data[base_index] = (*a, nx, ny, nz, red, green, blue)
            vertex_data[base_index + 1] = (*b, nx, ny, nz, red, green, blue)
            vertex_data[base_index + 2] = (*c, nx, ny, nz, red, green, blue)

        return vertex_data

    def get_vbo(self):
        vbo = self.context.buffer(self.vertex_data)
        return vbo

    def get_vao(self):
        vao = self.context.vertex_array(self.shader_program,
                                        [(self.vbo, '3f 3f 3f', 'in_position', 'in_normal', 'in_color')],
                                        skip_errors=True)
        return vao

    def get_shader_program(self, shader_name):
        with open(f"{ABS_PATH}/shaders/{shader_name}.vert") as file:
            vertex_shader = file.read()

        with open(f"{ABS_PATH}/shaders/{shader_name}.frag") as file:
            fragment_shader = file.read()

        program = self.context.program(vertex_shader, fragment_shader)
        return program

    def render(self):
        self.update()
        self.vao.render()

    def destroy(self):
        self.vbo.release()
        self.shader_program.release()
        self.vao.release()

    def __repr__(self):
        return f"ChunkModel<{self.chunk_coord}>"