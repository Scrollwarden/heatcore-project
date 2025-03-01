import glm

class HeatCore:
    def __init__(self, app, mesh, position = (0, 1, 0)):
        self.app = app
        self.mesh = mesh
        
        self.position = glm.vec3(position)
        self.m_model = glm.mat4()
    
    def update(self):
        angle = self.app.time / 1000
        rotation = glm.rotate(angle, glm.vec3(0, 1, 0))
        translation = glm.translate(self.position)
        self.m_model = translation * rotation
        self.mesh.shader_program['m_model'].write(self.m_model)
    
    def render(self):
        self.update()
        self.mesh.render()