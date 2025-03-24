import glm
import numpy as np
import struct

import os
ABS_PATH = os.path.dirname(os.path.abspath(__file__))

def open_shaders(app, shader_name):
    with open(f"{ABS_PATH}/shaders/{shader_name}.vert") as file:
        vertex_shader = file.read()

    with open(f"{ABS_PATH}/shaders/{shader_name}.frag") as file:
        fragment_shader = file.read()
    
    program = app.context.program(vertex_shader, fragment_shader)
    return program

class ShaderProgram:
    def __init__(self, app, color_params, shader_name):
        self.app = app
        with open(f"{ABS_PATH}/shaders/{shader_name}.vert") as file:
            vertex_shader = file.read()

        with open(f"{ABS_PATH}/shaders/{shader_name}.frag") as file:
            fragment_shader = file.read()

        self.program = self.app.context.program(vertex_shader, fragment_shader)

        self.on_init(color_params)

    def on_init(self, color_params):
        # light
        self.program['light.position'].write(self.app.light.position)
        self.program['light.Ia'].write(self.app.light.Ia)
        self.program['light.Id'].write(self.app.light.Id)
        self.program['light.Is'].write(self.app.light.Is)
        # mvp
        colors = np.array(color_params.colors, dtype=np.float32) / 255
        colors_256 = np.zeros((256, 3), dtype=np.float32)
        colors_256[:len(colors)] = colors
        print(colors_256.shape)
        print(colors_256.dtype)
        self.program['colors'].write(colors_256.tobytes())
        self.program['m_proj'].write(self.app.camera.m_proj)
        self.program['m_view'].write(self.app.camera.m_view)
        self.program['m_model'].write(glm.mat4())

    def update(self):
        self.program['m_proj'].write(self.app.camera.m_proj)
        self.program['m_view'].write(self.app.camera.view_matrix)
        self.program['camPos'].write(self.app.camera.position)
        self.program['time'].write(struct.pack('f', self.app.time))

    def get_program(self):
        return self.program

    def destroy(self):
        self.program.release()

class ShipShaderProgram:
    def __init__(self, app, shader_name):
        self.app = app
        with open(f"{ABS_PATH}/shaders/{shader_name}.vert") as file:
            vertex_shader = file.read()

        with open(f"{ABS_PATH}/shaders/{shader_name}.frag") as file:
            fragment_shader = file.read()

        self.program = self.app.context.program(vertex_shader, fragment_shader)

        self.on_init()

    def on_init(self):
        # light
        self.program['light.position'].write(self.app.light.position)
        self.program['light.Ia'].write(self.app.light.Ia)
        self.program['light.Id'].write(self.app.light.Id)
        self.program['light.Is'].write(self.app.light.Is)
        # mvp
        self.program['m_proj'].write(self.app.camera.m_proj)
        self.program['m_view'].write(self.app.camera.m_view)
        self.program['m_model'].write(glm.mat4())

    def update(self):
        self.program['m_proj'].write(self.app.camera.m_proj)
        self.program['m_view'].write(self.app.camera.view_matrix)
        self.program['camPos'].write(self.app.camera.position)
        self.program['time'].write(struct.pack('f', self.app.time))

    def get_program(self):
        return self.program

    def destroy(self):
        self.program.release()