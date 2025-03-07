import glm
from new_engine.options import HEIGHT_SCALE

class HeatCore:
    def __init__(self, app, mesh, position = (0, 1, 0)):
        self.app = app
        self.mesh = mesh
        
        self.position = glm.vec3(position)
        self.m_model = glm.mat4()
    
    def update(self):
        angle = self.app.time
        position = self.position + glm.vec3(0, glm.sin(1.5 * angle), 0) * 0.00025 * HEIGHT_SCALE
        
        axis_rotation = glm.normalize(glm.vec3(-0.15925, 0.59725, 0.45675))
        
        self.m_model = glm.translate(position) * glm.rotate(angle, axis_rotation)
        self.mesh.shader_program['m_model'].write(self.m_model)
        # self.update_wild()
    
    def update_wild(self):
        angle = self.app.time
        
        # Chaotic position movement
        position = self.position + glm.vec3(
            0.005 * glm.sin(2.1 * angle),  # Small side-to-side sway
            0.00025 * HEIGHT_SCALE * glm.sin(1.5 * angle),  # Vertical bounce
            0.005 * glm.cos(1.8 * angle)  # Forward-back sway
        )

        # Three crazy independent rotations
        rotation_x = glm.rotate(angle * 2.3, glm.vec3(1, 0, 0))  # Fast pitch
        rotation_y = glm.rotate(angle * 3.1, glm.vec3(0, 1, 0))  # Even faster yaw
        rotation_z = glm.rotate(angle * 4.7, glm.vec3(0, 0, 1))  # Insane roll
        
        # Combine rotations in a crazy order
        self.m_model = glm.translate(position) * rotation_x * rotation_y * rotation_z
        self.mesh.shader_program['m_model'].write(self.m_model)

    
    def render(self):
        self.update()
        self.mesh.render()