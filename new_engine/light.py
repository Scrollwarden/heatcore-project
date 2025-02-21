import glm

class Light:
    def __init__(self, position=(0, 5.0, 0), color=(1, 1, 1)):
        self.position = glm.vec3(position)
        self.color = glm.vec3(color)
        self.direction = glm.vec3(0)
        # intensities
        self.Ia = 1.0 * self.color  # ambient
        self.Id = 0.9 * self.color  # diffuse
        self.Is = 1.0 * self.color  # specular
        # view matrix
        self.m_view_light = self.get_view_matrix()

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.direction, glm.vec3(0, 1, 0))
