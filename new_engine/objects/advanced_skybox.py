import glm


class AdvancedSkyBoxObject:
    def __init__(self, app, mesh, position = (0, 0, 0)):
        self.app = app
        self.mesh = mesh

        self.position = glm.vec3(position)
        self.m_model = glm.mat4()

    def update(self):
        self.m_model = glm.translate(self.position)

    def render(self):
        self.update()
        self.mesh.render()