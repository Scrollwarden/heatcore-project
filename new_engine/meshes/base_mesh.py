import numpy as np


class BaseMesh:
    def __init__(self):
        self.context = None
        self.shader_program = None
        self.vbo_format = None
        self.attrs: tuple[str, ...] = None
        self.vertex_data = None
        self.vbo = None
        self.vao = None

    def init_without_context(self): ...

    def init_context(self):
        self.vbo = self.context.buffer(self.vertex_data)
        self.vao = self.context.vertex_array(
            self.shader_program, [(self.vbo, self.vbo_format, *self.attrs)], skip_errors=True
        )

    def render(self):
        self.vao.render()

    def destroy(self):
        self.vbo.release()
        self.vao.release()