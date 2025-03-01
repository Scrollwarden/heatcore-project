from new_engine.meshes.obj_base_mesh import DefaultObjMesh, GameObjMesh
from new_engine.options import HEIGHT_SCALE
from new_engine.objects.starting_base import StartingBase
from new_engine.objects.heatcore import HeatCore
import glm

class Scene:
    def __init__(self, app):
        self.app = app
        self.meshes = {}
        self.objects = []
        self.load()
    
    def load(self):
        self.meshes["heatcore"] = GameObjMesh(self.app, "heat_core", "obj",
                                              scale=0.01)
        self.meshes["starting_base"] = GameObjMesh(self.app, "starting_base", "obj",
                                                   scale=0.005)
        
        position = glm.vec3(0, 0, 0)
        terrain_height = self.app.chunk_manager.get_perlin_height(position, 2)
        position.y = max(0, terrain_height) + 0.02 * HEIGHT_SCALE
        starting_base = StartingBase(self.meshes["starting_base"], position)
        self.objects.append(starting_base)
        
        position = glm.vec3(1, 0, 0)
        terrain_height = self.app.chunk_manager.get_perlin_height(position, 2)
        position.y = max(0, terrain_height) + 0.02 * HEIGHT_SCALE
        heatcore = HeatCore(self.app, self.meshes["heatcore"], position)
        self.objects.append(heatcore)
    
    def update(self):
        for mesh in self.meshes.values():
            mesh.update()
        for obj in self.objects:
            obj.update()
    
    def render(self):
        """Render all chunks within the active radius."""
        self.update()
        for obj in self.objects:
            obj.render()
    
    def destroy(self):
        [obj.destroy() for obj in self.objects]