import glm
from engine.options import HEIGHT_SCALE, CHUNK_SIZE, CHUNK_SCALE, MAX_FALL_DISTANCE


class AncientStructure:
    def __init__(self, app, mesh, position):
        self.app = app
        self.mesh = mesh
        
        self.position = position
        self.m_model = glm.mat4()
        self.rotation = glm.mat4()
        
        self.won = False
    
    def init_angle(self):
        terrain_normal = self.app.planet.get_normal(self.position)
        angle = glm.atan(terrain_normal.z, terrain_normal.x)
        self.rotation = glm.rotate(angle, glm.vec3(0, 1, 0))
    
    def update(self):
        camera_position = self.app.planet.camera.position.xz / (CHUNK_SIZE * CHUNK_SCALE)
        distance = glm.distance(camera_position, self.position.xz / (CHUNK_SIZE * CHUNK_SCALE))
        
        offset = 3
        if distance <= offset:
            fall_amount = 0.0
        else:
            fall_amount = (distance - offset) ** 2 * MAX_FALL_DISTANCE / ((10 - offset) ** 2)
        
        translation = glm.translate(self.position + glm.vec3(0, fall_amount, 0))
        self.m_model = translation * self.rotation
        self.mesh.shader_program['m_model'].write(self.m_model)
    
    
    def render(self):
        self.update()
        self.mesh.render()