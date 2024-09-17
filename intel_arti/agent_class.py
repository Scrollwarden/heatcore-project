import numpy as np # pip install numpy
import tensorflow as tf # pip install tensorflow
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import Dense # type: ignore
from tensorflow.keras import Input # type: ignore
import random
from collections import deque
tf.keras.utils.disable_interactive_logging()

def create_model(state_size, action_size):
    # À quoi ressemble notre modèle
    model = Sequential()
    model.add(Input(shape=(state_size,)))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(action_size, activation='linear'))
    model.compile(optimizer = tf.keras.optimizers.Adam(learning_rate = 0.001),
                  loss = tf.keras.losses.MeanSquaredError())
    #print("Weights :", model.get_weights())
    return model

# C'est fait pour fermer la gueule de self.model.fit() c'est tout
# Parce que sinon il spam le terminal à mort
import sys
from io import StringIO


class SilentCallback(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs=None):
        pass


def suppress_stdout(func):
    def wrapper(*args, **kwargs):
        # Save the current stdout
        original_stdout = sys.stdout
        # Redirect stdout to suppress output
        sys.stdout = StringIO()
        try:
            return func(*args, **kwargs)
        finally:
            # Restore the original stdout
            sys.stdout = original_stdout
    return wrapper

class DQNAgent:
    def __init__(self, state_size: int, action_size: int, no_model : bool = False) -> None:
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.win_memory = deque(maxlen=32)
        self.losing_memory = deque(maxlen=32)
        self.bad_memory = deque(maxlen=32)
        self.gamma = 0.95  # Discount factor
        self.epsilon = 1.0  # Chance (de 0 à 1) de répondre aléatoirement pour explorer au lieu de jouer comme un con
        self.epsilon_min = 0.01 # Quand est-ce que l'IA arrête d'explorer
        self.epsilon_decay = 0.95 # À chaque fois, on multiplie self.epsilon par self.epsilon_decay pour qu'il commence à répondre tout seul
        if not no_model :
            self.model = create_model(state_size, action_size)
        
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
    
    def remember_winning(self, state, action, reward) :
        self.win_memory.append((state, action, reward))
    
    def remember_losing(self, state, action, reward) :
        self.losing_memory.append((state, action, reward))
    
    def remember_bad(self, state, action, reward) :
        self.bad_memory.append((state, action, reward))

    def max_legal(self, liste : list[int], illegal_moves : list[int]) :
        if 9 not in illegal_moves :
            indice = 9 
        else :
            indice = 10
        for i in range(len(liste)) :
            if i not in illegal_moves and liste[indice] < liste[i]:
                indice = i
        return indice
    
    def act(self, state, illegal_moves : list[int], test_model: bool=False):
        """On lui demande de préduire la réponse grâce à l'état du cube

        Args:
            state (np.array): L'état du cube (les neuronnes du début)
            test_model (bool, optional): True pour qu'il ne réponde jamais aléatoirement, juste pour le tester. Defaults to False.

        Returns:
            np.array: La prédiciton
        """
        if not test_model:
            if np.random.rand() <= self.epsilon:
                valeur = random.randrange(self.action_size)
                while valeur in illegal_moves :
                    valeur = random.randrange(self.action_size)
                return valeur
        act_values = self.model.predict(state)[0]

        return self.max_legal(act_values, illegal_moves)
    
    @suppress_stdout
    def replay(self, batch_size):
        """Fonction pour entrainer l'IA
        Elle regarde chaque position dans sa mémoire, regarde les récompenses et apprend

        Args:
            batch_size (int): Le nombre de position (choisi aléatoirement dans la mémoire) à laquelle l'IA va apprendre
        """
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target += self.gamma * np.amax(self.model.predict(next_state)[0])
            target_f = self.model.predict(state, verbose=0)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0, callbacks=[SilentCallback()])
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        self.memory = deque()

    def replay_wins(self) :
        for state, action, reward in self.win_memory :
            target = self.model.predict(state, verbose=0)
            target[0][action] = reward
            self.model.fit(state, target, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def replay_losses(self) :
        for state, action, reward in self.losing_memory :
            target = self.model.predict(state, verbose=0)
            target[0][action] = reward
            self.model.fit(state, target, epochs=1, verbose=0)
    
    def replay_bad(self) :
        for state, action, reward in self.bad_memory :
            target = self.model.predict(state, verbose=0)
            target[0][action] = reward
            self.model.fit(state, target, epochs=1, verbose=0)

create_model(54, 27)