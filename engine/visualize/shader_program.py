import glm
import os

ABS_PATH = os.path.dirname(os.path.abspath(__file__))

class ShaderProgram:
    def __init__(self, app, shader_name):
        self.app = app
        with open(f"{ABS_PATH}/{shader_name}.vert") as file:
            vertex_shader = file.read()

        with open(f"{ABS_PATH}/{shader_name}.frag") as file:
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
        self.program['m_proj'].write(self.app.camera.get_projection_matrix())
        self.program['m_view'].write(self.app.camera.get_view_matrix())
        self.program['m_model'].write(glm.mat4())

    def update(self):
        self.program['m_view'].write(self.app.camera.view_matrix)
        self.program['camPos'].write(self.app.camera.position)

    def get_program(self):
        return self.program

    def destroy(self):
        self.program.release()