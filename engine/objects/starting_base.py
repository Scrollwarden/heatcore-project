import glm
from engine.options import HEIGHT_SCALE, CHUNK_SIZE, CHUNK_SCALE, MAX_FALL_DISTANCE

class StartingBase:
    def __init__(self, app, mesh, position = (1, 1, 0)):
        self.app = app
        self.mesh = mesh
        
        self.position = glm.vec3(position)
        self.m_model = glm.translate(position)
    
    def update(self):
        camera_position = self.app.planet.camera.position.xz / (CHUNK_SIZE * CHUNK_SCALE)
        distance = glm.distance(camera_position, self.position.xz / (CHUNK_SIZE * CHUNK_SCALE))
        
        offset = 3
        if distance <= offset:
            fall_amount = 0.0
        else:
            fall_amount = (distance - offset) ** 2 * MAX_FALL_DISTANCE / ((10 - offset) ** 2)
        
        self.m_model = glm.translate(self.position + glm.vec3(0, fall_amount, 0))
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