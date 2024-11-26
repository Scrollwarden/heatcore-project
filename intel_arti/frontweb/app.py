from flask import Flask, render_template, request, jsonify
from tensorflow.keras.models import load_model # type: ignore
import sys
import numpy as np

#sys.path.append("/home/matthew/Documents/GitHub/heatcore-project/intel_arti/cube_v2")

from cube import Cube
from agent import Agent

app = Flask(__name__)

# Screen constants
MODEL_PATH = r"/home/matthew/Documents/GitHub/heatcore-project/intel_arti/cube_v2/models/model3.h5"

KEY_MAP = {
}

KEY_NUM = {
}

# Initialize the agent and cube
agent = Agent(True)
agent.model = load_model(MODEL_PATH)
cube = Cube()
player = 1
coup_interdit = -1
reverse_display = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/keypress', methods=['POST'])
def keypress():
    global player, coup_interdit, reverse_display
    data = request.json
    key = data['key']

    # Handle key presses
    if key in KEY_MAP:
        if 'shiftKey' in data and data['shiftKey']:
            action = cube.string_to_move(KEY_MAP[key] + "'", player, False)
        else:
            action = cube.string_to_move(KEY_MAP[key], player, False)
        if action in cube.actions_possibles(coup_interdit):
            print(f"WARNING !!! Coup interdit joué par le joueur{player}")
        if action < 18:
            if action < 9:
                coup_interdit = action + 9
            else:
                coup_interdit = action - 9
        else:
            coup_interdit = -1
        player *= -1
    elif key in KEY_NUM:
        action = KEY_NUM.index(key)
        cube.jouer(action, player)
        if action in cube.actions_possibles(coup_interdit):
            print(f"WARNING !!! Coup interdit joué par le joueur{player}")
        if action < 18:
            if action < 9:
                coup_interdit = action + 9
            else:
                coup_interdit = action - 9
        else:
            coup_interdit = -1
        player *= -1
    elif key == 'space':
        reverse_display = not reverse_display
    elif key == 'p':
        cube.reset()
        player = 1
        coup_interdit = -1

    return jsonify({'status': 'success'})

@app.route('/cube_data', methods=['GET'])
def cube_data():
    cube_state = cube.get_state()
    vertices = []
    faces = []
    colors = []

    for face in range(6):
        for i in range(3):
            for j in range(3):
                value = cube_state[face, i, j]
                color = [1, 0, 0] if value == 1 else [0, 1, 0] if value == -1 else [1, 1, 1]
                colors.append(color)
                vertices.append([i, j, face])

    return jsonify({'vertices': vertices, 'colors': colors})

if __name__ == '__main__':
    app.run(debug=True)
