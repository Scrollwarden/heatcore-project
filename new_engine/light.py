import glm

class Light:
    """Class for the light in the Graphic engine"""
    
    def __init__(self, app, normal=(0.0, 0.5, 1.0), direction=(1.0, -0.2, 0.0), color=(1, 1, 1)):
        self.app = app
        self.color = glm.vec3(color)

        self.normal = glm.vec3(normal)
        self.time = 190
        self.starting_direction = glm.vec3(direction)

        self.direction = glm.vec3()
        # self.m_view = glm.lookAt(self.direction, glm.vec3(0, 0, 0))
        self.Ia = glm.vec3()
        self.Id = glm.vec3()
        self.Is = glm.vec3()
        self.set_direction(direction)

    def set_direction(self, direction):
        """Updates the direction and recalculates light intensities."""
        self.direction = glm.normalize(glm.vec3(direction))
        self.update_intensities()

    def update_intensities(self):
        """Dynamically adjusts ambient, diffuse, and specular based on sun height."""
        sun_height = glm.clamp(self.direction.y, 0.0, 1.0)  # 0 when low, 1 when high

        self.Ia = (0.3 + 0.4 * sun_height) * self.color  # More ambient when higher
        self.Id = (0.6 + 0.3 * sun_height) * self.color  # More diffuse when higher
        self.Is = (0.8 + 0.2 * sun_height) * self.color  # Specular slightly increases

    def update(self):
        """Update the light class for each frame"""
        time_full_rotation = 300 # in seconds
        current_direction = glm.rotate(glm.radians(self.time * 360 / time_full_rotation), self.normal) * glm.vec4(self.starting_direction, 0.0)
        self.set_direction(current_direction)
        self.time += self.app.delta_time / 1000 # number of seconds
        print(f"Light time: {self.time}")