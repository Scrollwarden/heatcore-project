from typing import Any
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import Dense, Conv2D, Flatten, Concatenate # type: ignore
from tensorflow.keras import Input, Model # type: ignore
import tensorflow as tf
from morpion import PartieIAvsH, Morpion, DataMorpion, PartiesIAvsIA
from numpy import reshape

class Choices :
    def __init__(self) :
        self.num_filters = 10
        self.num_dense = 2
        self.num_neurone = [64, 64]
        self.start_learning_rate = 0.01

class MyModel(Model) :
    def __init__(self) :
        super().__init__()
        self.conv_ligne = Conv2D(10, (1, 3))
        self.conv_col = Conv2D(10, (3, 1))
        self.conv_glob = Conv2D(10, (3, 3))
        self.flatten = Flatten()
        self.concat = Concatenate()
        self.dense = Dense(100, activation='relu')
        self.final_dense = Dense(1, activation='linear')
    
    def __call__(self, x, training:bool=False) :
        out1 = self.conv_ligne(x)
        out1 = self.flatten(out1)
        out2 = self.conv_col(x)
        out2 = self.flatten(out2)
        out3 = self.conv_glob(x)
        out3 = self.flatten(out3)

        out = self.concat([out1, out2, out3])
        out = self.dense(out)
        out = self.final_dense(out)
        return out


class AgentMorpion :
    def __init__(self, choices : Choices, num_model : int = 0) -> None:
        self.choices = choices
        self.learning_rate = self.choices.start_learning_rate
        if num_model == 0 :
            self.create_model()
        elif num_model == 1 :
            self.create_model2()
        else :
            self.create_model3()
    
    def create_model(self) :
        self.model = Sequential()
        self.model.add(Input(shape=(3, 3, 1)))
        self.model.add(Flatten())
        self.model.add(Dense(200, activation='relu'))
        self.model.add(Dense(1, activation='linear'))
        self.model.compile(optimizer = tf.keras.optimizers.Adam(learning_rate = self.learning_rate),
                  loss = tf.keras.losses.MeanAbsoluteError())
    
    def create_model2(self) :
        self.model = Sequential()
        self.model.add(Input(shape=(3, 3, 1)))
        self.model.add(Conv2D(self.choices.num_filters, (3, 3)))
        self.model.add(Flatten())
        for i in range(self.choices.num_dense) :
            self.model.add(Dense(self.choices.num_neurone[i], activation='relu'))
        self.model.add(Dense(1, activation='linear'))
        self.model.compile(optimizer = tf.keras.optimizers.Adam(learning_rate = self.learning_rate),
                  loss = tf.keras.losses.MeanAbsoluteError())
    
    def create_model3(self) :
        self.model = MyModel()
        self.model.compile(optimizer = tf.keras.optimizers.Adam(learning_rate = self.learning_rate),
                  loss = tf.keras.losses.MeanAbsoluteError())
    
    def summary(self) :
        self.model.summary()
    
    def __call__(self, jeu: Morpion, training:bool=False) -> Any:
        maxi = None
        act_max = None
        for action, possibilite in jeu.generate_possibilite() :
            value = self.model(reshape(possibilite.get_state() * jeu.joueur, (1, 3, 3, 1)), training=training)
            if maxi == None or value > maxi :
                maxi = value
                act_max = action
        return act_max
    
    def predict(self, jeu : Morpion, a) :
        maxi = None
        act_max = None
        for action, possibilite in jeu.generate_possibilite() :
            if a :
                value = self.model.predict(reshape(possibilite.get_state(), (1,3,3)))
            else :
                value = self.model.predict(reshape(possibilite.get_state(), (1,3,3,1)))
            if maxi == None or value > maxi :
                maxi = value
                act_max = action
        return act_max
    
    def fit(self, *args, **kwargs) :
        return self.model.fit(*args, **kwargs)

def jouer_contre_ia_ameliorante() :
    data = DataMorpion(1000)
    x, y = data.get_datas()
    choix = Choices()
    agent = AgentMorpion(choix)
    agent.fit(x, y)
    partie = PartieIAvsH()
    while True :
        while not partie.jeu.terminal_state()[0] :
            partie.step(agent(partie.jeu))
            print(partie.jeu)
        print(partie.jeu.terminal_state())
        partie.recommencer()
        data.reset()
        data.add_data(1000)
        x, y = data.get_datas()
        agent.fit(x, y)

def ia_vs_ia() :
    reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
    monitor='loss', 
    factor=0.5, 
    patience=5, 
    min_lr=1e-6
)
    data = DataMorpion(10000)
    x, y = data.get_datas()
    choix = Choices()
    agent1 = AgentMorpion(choix, 0)
    print("Agent 1 : ", end='')
    agent1.fit(x, y, callbacks = [reduce_lr])
    agent2 = AgentMorpion(choix, 2)
    print("Agent 2 : ", end='')
    agent2.fit(x, y, callbacks = [reduce_lr])
    partie = PartiesIAvsIA(agent1, agent2)
    partie.evaluate()
    print(partie.gagnants)
    agent2.summary()
    while True :
        data.reset()
        data.add_data(10000)
        x, y = data.get_datas()
        print("Agent 1 : ", end='')
        agent1.fit(x, y, callbacks = [reduce_lr])
        print("Agent 2 : ", end='')
        agent2.fit(x, y, callbacks = [reduce_lr])
        partie.evaluate()
        print(partie.gagnants)
        input()

def jouer_contre_ia() :
    data = DataMorpion(10000)
    x, y = data.get_datas()
    choix = Choices()
    agent = AgentMorpion(choix)
    agent.fit(x, y)
    partie = PartieIAvsH()
    while True :
        while not partie.jeu.terminal_state()[0] :
            partie.step(agent(partie.jeu))
            print(partie.jeu)
        print(partie.jeu.terminal_state())
        partie.recommencer()
        

if __name__ == "__main__" :
    jouer_contre_ia()
