'''
Etudie un model chargé
permet de récupérer différents paramètres.
'''

from agent_morpion import AgentMorpion, Choices
from numpy import reshape
from collections import deque
from statistics import mean
from tensorflow.keras.models import load_model #type: ignore

MODEL_PATH = "model_morpion.h5"

choix = Choices()
agent = AgentMorpion(choix, -1)
agent.model = load_model(MODEL_PATH)
print(agent.model.layers)
weights, bias = agent.model.layers[1].get_weights()


while True :
    NUM_NEURONE = int(input("Numéro du neurone : "))
    print("Bais", bias[NUM_NEURONE])
    liste = []
    for i in range(9) :
        liste.append((i,  weights[i][NUM_NEURONE]))
    liste.sort(key=lambda x: abs(x[1]), reverse=True)

    for i in range(9) :
        print(liste[i][0], ":", liste[i][1])
