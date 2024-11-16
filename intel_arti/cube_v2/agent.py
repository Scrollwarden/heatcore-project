from typing import Any
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import Dense # type: ignore
from tensorflow.keras import Input, Model # type: ignore
import tensorflow as tf
from random import random, randint

class AgentParameters :
    def __init__(self):
        self.nombre_neurones = 200
        self.nombre_couches = 1
        self.learning_rate = 0.001
        self.optimizer = tf.keras.optimizers.Adam(learning_rate = self.learning_rate)
        self.loss = tf.keras.losses.MeanSquaredError()

class ModelCube(Model) :
    def __init__(self) :
        super().__init__()

class Agent :
    def __init__(self) -> None:
        self.params = AgentParameters()
        self.output_size = 1
        self.exploration_rate = 1.0
        self.memory = []
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
