import glm

class StartingBase:
    def __init__(self, mesh, position = (1, 1, 0)):
        self.mesh = mesh
        
        self.position = glm.vec3(position)
        self.m_model = glm.translate(position)
    
    def update(self):
        self.mesh.shader_program['m_model'].write(self.m_model)
    
    def render(self):
        self.update()
        self.mesh.render()