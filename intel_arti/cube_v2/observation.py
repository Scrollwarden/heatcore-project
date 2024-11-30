from agent import Agent
from cube import Cube
from numpy import reshape
from collections import deque
from statistics import mean
from tensorflow.keras.models import load_model #type: ignore

NUM_MODEL = 9
MODEL_PATH = f"models\\model{NUM_MODEL}.h5"

cube = Cube()

agent = Agent(True)
agent.model = load_model(MODEL_PATH)
weights, bias = agent.model.layers[1].get_weights()


while True :
    NUM_NEURONE = int(input("Numéro du neurone : "))
    print("Bais", bias[NUM_NEURONE])
    liste = []
    for i in range(54) :
        liste.append((i,  weights[i][NUM_NEURONE]))
    liste.sort(key=lambda x: abs(x[1]), reverse=True)

    for i in range(54) :
        print(liste[i][0], ":", liste[i][1])

"""
parmi_premiers = [0]*400
for i in range(54) :
    positif = 0
    maxi = [0]*7
    for j in range(400) :
        if weights[i][j] > 0 :
            positif += 1
        if weights[i][j] > weights[i][maxi[-1]] :
            maxi.append(j)
            maxi.sort(key=lambda x : weights[i][x], reverse=True)
            maxi.pop()
            parmi_premiers[j] += 1
    print(i, ":")
    print("Moyenne :", mean(weights[i]))
    print("Positifs :", positif)
    print("Maximums :", *maxi)

quantite = 0
for i in range(200) :
    print(i, ":", parmi_premiers[i])
    if not parmi_premiers[i] :
        quantite += 1
print("Nombre :", quantite)

"""

"""
for action in range(18, 27) :
    cube.reset()
    cube.jouer(action, 1)
    print(agent(reshape(cube.get_flatten_state(), (1, 54))))
"""