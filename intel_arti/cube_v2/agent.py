from typing import Any
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import Dense # type: ignore
from tensorflow.keras import Input, Model # type: ignore
import tensorflow as tf
from random import random, randint
from generators import StateGenerator
from cube import Cube
from copy import deepcopy
from numpy import ndarray, append

from parameters import *

def all_neg(liste : list) :
    for elt in liste :
        if elt >= 0 :
            return False
    return True

class AgentParameters :
    def __init__(self):
        self.nombre_neurones = NB_NEURONES
        self.nombre_couches = NB_COUCHES
        self.learning_rate = LEARNING_RATE
        self.optimizer = tf.keras.optimizers.Adam(learning_rate = self.learning_rate)
        self.loss = tf.keras.losses.MeanSquaredError()

class ModelCube(Model) :
    def __init__(self) :
        super().__init__()

class Agent :
    def __init__(self, no_model=False) -> None:
        self.params = AgentParameters()
        self.output_size = 1
        self.exploration_rate = 1.0
        self.memory = []
        # L'action maximum que le modèle peut choisir
        self.max_action = 3
        if not no_model :
            self.create_model()
    
    def __call__(self, *args, **kwargs):
        return self.model(*args, **kwargs)
    
    def fit(self, *args, **kwargs) :
        self.model.fit(*args, **kwargs)
    
    def entrainer(self, generateur) :
        self.fit(generateur)
    
    def create_model(self) :
        self.model = Sequential()
        self.model.add(Input(shape=(54,)))
        for _ in range(self.params.nombre_couches) :
            self.model.add(Dense(self.params.nombre_neurones, activation='relu'))
        self.model.add(Dense(1, activation='linear'))
        self.model.compile(optimizer = self.params.optimizer,
                  loss = self.params.loss)
    
    def create_model_try(self) :
        self.model = Sequential()
        self.model.add(Input(shape=(54,)))
        self.model.add(Dense(64, activation='relu'))
        self.model.add(Dense(64, activation='relu'))
        self.model.add(Dense(64, activation='relu'))
        self.model.add(Dense(64, activation='relu'))
        self.model.add(Dense(1, activation='linear'))
        self.model.compile(optimizer = self.params.optimizer,
                  loss = self.params.loss)
    
    def set_learning_rate(self, learning_rate : float) :
        self.params.learning_rate = learning_rate
    
    def predict(self, x, training = False) :
        if training and random() < self.exploration_rate :
            return randint(0, 26)
        return self.model.predict(x)

    def choisir(self, cube : Cube, joueur : int, coup_interdit : int = -1) :
        """Renvoie le numéro de l'action que le modèle considère comme la meilleure.
        Note : La légalité de l'action choisie est garantie.
        Attention : ce choix est purement déterministe.

        Params :
        --------
            cube (Cube) : L'état actuel du cube 
        """
        actions = cube.actions_possibles(coup_interdit)
        situations = ndarray(shape=(0, 54))
        for action in actions :
            scratch = deepcopy(cube)
            scratch.set_state(scratch.grille * joueur, True)
            scratch.jouer(action, 1)
            situations = append(situations, [scratch.get_flatten_state()], 0)
        values = self(situations)
        i_max = 0
        for i in range(1, len(values)) :
            if values[i] > values[i_max] :
                i_max = i
        return actions[i_max]
    
    def choisir_sit(self, cube : Cube, joueur : int, coup_interdit : int = -1) :
        """Renvoie le numéro de l'action que le modèle considère comme la meilleure.

        Attention : ce choix est purement déterministe.

        Params :
        --------
            cube (Cube) : L'état actuel du cube 
        """
        actions = cube.actions_possibles(coup_interdit)
        situations = ndarray(shape=(0, 54))
        for action in actions :
            scratch = deepcopy(cube)
            scratch.set_state(scratch.grille * joueur, True)
            scratch.jouer(action, 1)
            situations = append(situations, [scratch.get_flatten_state()], 0)
        values = self(situations)
        i_max = max(range(0, len(values)), key=lambda i : values[i])
        return situations[i_max], actions[i_max]
    
    def choisir_non_deterministe(self, cube : Cube, joueur : int, coup_interdit : int = -1, disable_print : bool=True) :
        actions = cube.actions_possibles(coup_interdit)
        situations = ndarray(shape=(0, 54))
        for action in actions :
            scratch = deepcopy(cube)
            scratch.set_state(scratch.grille * joueur, True)
            scratch.jouer(action, 1)
            situations = append(situations, [scratch.get_flatten_state()], 0)
        values = list(self(situations))
        if not disable_print :
            for i in range(len(situations)) :
                print(actions[i], values[i][0])
        if all_neg(values) :
            i_max = max(range(len(actions)), key=lambda i : values[i])
            if not disable_print :
                print("All neg :", i_max)
            return actions[i_max]
        i = 0
        while i < len(actions) :
            if values[i] < 0 :
                actions.pop(i)
                values.pop(i)
            else :
                i += 1
        if not disable_print :
            print("Not neg :")
            for i in range(len(actions)) :
                print(actions[i], values[i][0])
        values = list(map(lambda x : x**2, values))
        somme = sum(values)
        if not disable_print :
            print("Somme :", somme)
        choix = random() * somme
        if not disable_print :
            print("Choix :", choix)
        i = 0
        while choix > sum(values[:i+1]) :
            i += 1
        if not disable_print :
            print("Action :", actions[i])
        return actions[i]
    
    def choisir_non_deterministe2(self, cube : Cube, joueur : int, coup_interdit : int = -1) :
        actions = cube.actions_possibles(coup_interdit)
        situations = ndarray(shape=(0, 54))
        for action in actions :
            scratch = deepcopy(cube)
            scratch.set_state(scratch.grille * joueur, True)
            scratch.jouer(action, 1)
            situations = append(situations, [scratch.get_flatten_state()], 0)
        values = self(situations)
        if max(values) > 0.9 :
            return max(range(len(values)), key=lambda i : values[i])
        if (mini := min(values)) < 0 :
            values = list(map(lambda v : (v-mini)**2, values))
        else :
            values = list(map(lambda v : v**2, values))
        somme = sum(values)
        choix = random() * somme
        i = 0
        somme = values[0]
        while choix > somme :
            i += 1
            somme += values[i]
        return actions[i]
    
    def choisir_non_det_sit(self, cube : Cube, joueur : int, coup_interdit : int = -1) :
        actions = cube.actions_possibles(coup_interdit)
        situations = ndarray(shape=(0, 54))
        for action in actions :
            scratch = deepcopy(cube)
            scratch.set_state(scratch.grille * joueur, True)
            scratch.jouer(action, 1)
            situations = append(situations, [scratch.get_flatten_state()], 0)
        values = self(situations)
        if max(values) > 0.9 :
            return situations[i_max := max(range(len(values)), key=lambda i : values[i])], actions[i_max]
        if (mini := min(values)) < 0 :
            values = list(map(lambda v : (v-mini), values))
        somme = sum(values)
        choix = random() * somme
        i = 0
        somme = values[0]
        while choix > somme :
            i += 1
            somme += values[i]
        return situations[i], actions[i]


if __name__ == "__main__" :
    agent = Agent()
    generators = StateGenerator()
    selected_gen = generators.generator_perfection(55)

    agent.fit(selected_gen, steps_per_epoch=100, epochs=1000)
    agent.model.save(r"models\generation0\model14.h5")
    print(generators.gagnants)