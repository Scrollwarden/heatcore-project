from typing import Any
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import Dense # type: ignore
from tensorflow.keras import Input, Model # type: ignore
import tensorflow as tf
from random import random, randint

class ModelCube(Model) :
    def __init__(self) :
        super().__init__()

class Agent :
    def __init__(self) -> None:
        self.output_size = 1
        self.learning_rate = 0.001
        self.exploration_rate = 1.0
        self.memory = []
        self.create_model(1000)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.model(*args, **kwargs)

    def create_model(self, n : int) :
        self.model = Sequential()
        self.model.add(Input(shape=(54,)))
        self.model.add(Dense(n, activation='relu'))
        self.model.compile(optimizer = tf.keras.optimizers.Adam(learning_rate = self.learning_rate),
                  loss = tf.keras.losses.MeanSquaredError())

    
    def create_model1(self) :
        self.model = Sequential()
        self.model.add(Input(shape=(54,)))
        self.model.add(Dense(64, activation='relu'))
        self.model.add(Dense(64, activation='relu'))
        self.model.add(Dense(64, activation='relu'))
        self.model.add(Dense(64, activation='relu'))
        self.model.add(Dense(1, activation='linear'))
        self.model.compile(optimizer = tf.keras.optimizers.Adam(learning_rate = self.learning_rate),
                  loss = tf.keras.losses.MeanSquaredError())
    
    def set_learning_rate(self, learning_rate : float) :
        self.learning_rate = learning_rate
        self.model
    
    def predict(self, x) :
        if random() < self.exploration_rate :
            return randint(0, 26)
        return self.model.predict(x)
