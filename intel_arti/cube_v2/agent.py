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
        actions = cube.actions_possibles(coup_interdit)
        situations = ndarray(shape=(0, 54))
        for action in actions :
            scratch = deepcopy(cube)
            scratch.set_state(scratch.grille * joueur, True)
            scratch.jouer(action, 1)
            situations = append(situations, [scratch.get_flatten_state()], 0)
        values = self(situations)
        for i in range(len(situations)) :
            print(situations[i], values[i])
        i_max = 0
        for i in range(1, len(values)) :
            if values[i] > values[i_max] :
                i_max = i
        return actions[i_max]


if __name__ == "__main__" :
    agent = Agent()
    generators = StateGenerator()
    selected_gen = generators.generators_only_partie(55)

    agent.fit(selected_gen, steps_per_epoch=100, epochs=1000)
    agent.model.save(r"models\model9.h5")
    print(generators.gagnants)
