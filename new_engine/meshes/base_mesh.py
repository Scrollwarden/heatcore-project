class BaseMesh:
    def __init__(self):
        self.context = None
        self.shader_program = None
        self.vbo_format = None
        self.attrs: tuple[str, ...] = None
        self.vertex_data = None
        self.vbo = None
        self.vao = None
    
    def init_shader(self): ...

    def init_context(self):
        self.vbo = self.context.buffer(self.vertex_data)
        self.vao = self.context.vertex_array(
            self.shader_program, [(self.vbo, self.vbo_format, *self.attrs)], skip_errors=True
        )
    
    def init_vertex_data(self): ...

    def update(self): ...

    def render(self):
        self.update()
        self.vao.render()

    def destroy(self):
        self.vbo.release()
        self.vao.release()
        if self.shader_program:
            self.shader_program.destroy()

    def __repr__(self):
        load_string = "NoVertices" if self.vertex_data is None else ""
        context_string = ", NoContext" if self.vao is None else ""
        return f"BaseMesh<{load_string}{context_string}>"