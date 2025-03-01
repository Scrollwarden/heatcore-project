import glm



class HeatCore:
    def __init__(self, app, position = (0, 1, 0)):
        self.app = app
        self.position = glm.vec3(position)
        self.m_model = glm.translate(self.position)
        self.mesh = app.meshes["heatcore"]
    
    def render(self):
        
    
    
    