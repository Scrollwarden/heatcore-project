import os
from sys import stdout
from random import choice
from agent import Agent
from generators import Partie
from tensorflow.keras.models import load_model #type: ignore

num1, num2 = map(int, input("Veuillez entrée les numéros des modèles voulus :").split())
agent1 = Agent(True)
agent2 = Agent(True)
MODEL_PATH = os.path.join(os.path.abspath(__file__).rstrip("ia_vs_ia.py"), "models\\generation0\\model{}.h5")
agent1.model = load_model(MODEL_PATH.format(num1))
agent2.model = load_model(MODEL_PATH.format(num2))

"""
while True :
    finie = False
    pl_ia1 = choice((1, -1))
    partie = Partie()
    coup_interdit = -1
    while not finie :
        if partie.joueur == pl_ia1 :
            action = agent1.choisir_non_deterministe(partie.cube, partie.joueur, partie.coup_interdit)
        else :
            action = agent2.choisir_non_deterministe(partie.cube, partie.joueur, partie.coup_interdit)
        print("Le joueur", partie.joueur, f"(modèle {num1 if partie.joueur==pl_ia1 else num2}) a choisi l'action", action)
        partie.step(action, True)
        print(partie.cube)
        if (gagnant := partie.cube.terminal_state())[0] :
            finie = True
            print("Le joueur", gagnant[1], "a gagné.")
        input()
"""
# [Egalité, [IA 1 ronds, IA 1 croix], [IA 2 ronds, IA 2 croix]]
gagnants = [0, [0, 0], [0, 0]]
coups = {}
for i in range(1000) :
    stdout.flush()
    finie = False
    pl_ia1 = choice((1, -1))
    partie = Partie()
    coup_interdit = -1
    nb_coups = 0
    while not finie :
        if partie.joueur == pl_ia1 :
            situation, action = agent1.choisir_sit(partie.cube, partie.joueur, partie.coup_interdit)
        else :
            situation, action = agent1.choisir_non_det_sit(partie.cube, partie.joueur, partie.coup_interdit)
        partie.known_step(situation, action)
        nb_coups += 1
        if (gagnant := partie.cube.terminal_state())[0] or nb_coups > 200:
            if nb_coups > 200 :
                print(partie.cube)
            finie = True
            coups[nb_coups] = coups.get(nb_coups, 0) + 1
            if gagnant[1] == 0 :
                gagnants[0] += 1
            elif gagnant[1] // abs(gagnant[1]) == pl_ia1 :
                gagnants[1][pl_ia1==1] += 1
            else :
                gagnants[2][pl_ia1==-1] += 1
    stdout.write("\r" + str(i + 1) + " : " + str(gagnants))
print("\n", coups)