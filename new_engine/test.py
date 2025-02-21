import os
import glm
import numpy as np





if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.abspath(__file__))
    path = f"{dir_path}/../3D data/model obj/"
    test = load_vertex_data_obj(path + "spaceship_player")
    print(test[:10])