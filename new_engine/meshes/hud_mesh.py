from new_engine.meshes.base_mesh import BaseMesh
import numpy as np
import moderngl as mgl

from new_engine.options import SCREEN_WIDTH, SCREEN_HEIGHT

class HUDMesh(BaseMesh):
    def __init__(self, app):
        super().__init__()
        self.context = app.context
        self.shader_program = self.context.program(
            vertex_shader="""
            #version 330
            in vec2 in_pos;
            in vec2 in_uv;
            out vec2 v_uv;
            void main() {
                gl_Position = vec4(in_pos, 0.0, 1.0);
                v_uv = in_uv;
            }
            """,
            fragment_shader="""
            #version 330
            uniform sampler2D ui_texture;
            in vec2 v_uv;
            out vec4 f_color;
            void main() {
                f_color = texture(ui_texture, v_uv);
            }
            """
        )
        self.vbo_format = "2f 2f"
        self.attrs = ('in_pos', 'in_uv')
        self.ui_texture = self.context.texture((SCREEN_WIDTH, SCREEN_HEIGHT), 4)
        self.ui_texture.filter = (mgl.LINEAR, mgl.LINEAR)
        self.init_vertex_data()
        self.init_context()

    def init_vertex_data(self):
        self.vertex_data = np.array([
            #  x,    y,   u,   v
            -1.0, -1.0,  0.0,  0.0,
             1.0, -1.0,  1.0,  0.0,
            -1.0,  1.0,  0.0,  1.0,
             1.0,  1.0,  1.0,  1.0,
        ], dtype='f4')

    def render(self):
        self.ui_texture.use(location=0)
        self.vao.render(mgl.TRIANGLE_STRIP)

    def destroy(self):
        super().destroy()
        self.ui_texture.release()

    def __repr__(self):
        load_string = "NoVertices" if self.vertex_data is None else ""
        context_string = ", NoContext" if self.vao is None else ""
        return f"HUDMesh<{load_string}{context_string}>"