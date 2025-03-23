from typing import Any
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import Dense # type: ignore
from tensorflow.keras import Input, Model # type: ignore
import tensorflow as tf
from random import random, randint
from intel_arti.cube_v2.generators import StateGenerator
from intel_arti.cube_v2.cube import Cube
from copy import deepcopy
from numpy import ndarray, append
import numpy as np

from intel_arti.cube_v2.parameters import *

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

class Agent:
    def __init__(self, no_model=False) -> None:
        self.params = AgentParameters()
        self.output_size = 1
        self.exploration_rate = 1.0
        self.memory = []
        # L'action maximum que le modèle peut choisir
        self.max_action = 3
        self.model = None
        if not no_model:
            self.create_model()

    def __call__(self, *args, **kwargs):
        # If a model is loaded, call it; otherwise return a random value for each input row.
        if self.model is not None:
            return self.model(*args, **kwargs)
        else:
            # Expecting the first argument to be an ndarray of situations with shape (n, 54)
            if args and isinstance(args[0], np.ndarray):
                n = args[0].shape[0]
                # Return random values between 0 and 1 for each situation, shaped (n, 1)
                return np.random.rand(n, 1)
            else:
                # Fallback if no argument provided.
                return None

    def fit(self, *args, **kwargs):
        if self.model is not None:
            self.model.fit(*args, **kwargs)

    def entrainer(self, generateur):
        self.fit(generateur)

    def create_model(self):
        self.model = Sequential()
        self.model.add(Input(shape=(54,)))
        for _ in range(self.params.nombre_couches):
            self.model.add(Dense(self.params.nombre_neurones, activation='relu'))
        self.model.add(Dense(1, activation='linear'))
        self.model.compile(optimizer=self.params.optimizer,
                           loss=self.params.loss)

    def create_model_try(self):
        self.model = Sequential()
        self.model.add(Input(shape=(54,)))
        self.model.add(Dense(64, activation='relu'))
        self.model.add(Dense(64, activation='relu'))
        self.model.add(Dense(64, activation='relu'))
        self.model.add(Dense(64, activation='relu'))
        self.model.add(Dense(1, activation='linear'))
        self.model.compile(optimizer=self.params.optimizer,
                           loss=self.params.loss)

    def set_learning_rate(self, learning_rate: float):
        self.params.learning_rate = learning_rate

    def predict(self, x, training=False):
        if training and random() < self.exploration_rate:
            return randint(0, 26)
        if self.model is not None:
            return self.model.predict(x)
        else:
            return np.random.rand(x.shape[0], 1)

    def choisir(self, cube: Cube, joueur: int, coup_interdit: int = -1):
        """
        Renvoie le numéro de l'action que le modèle considère comme la meilleure.
        Note : La légalité de l'action choisie est garantie.
        Attention : ce choix est purement déterministe.
        """
        actions = cube.actions_possibles(coup_interdit)
        situations = np.ndarray(shape=(0, 54))
        for action in actions:
            scratch = deepcopy(cube)
            scratch.set_state(scratch.grille * joueur, True)
            scratch.jouer(action, 1)
            situations = np.append(situations, [scratch.get_flatten_state()], axis=0)
        values = self(situations)
        i_max = 0
        for i in range(1, len(values)):
            if values[i] > values[i_max]:
                i_max = i
        return actions[i_max]

    def choisir_sit(self, cube: Cube, joueur: int, coup_interdit: int = -1):
        """
        Renvoie le numéro de l'action que le modèle considère comme la meilleure.
        Attention : ce choix est purement déterministe.
        """
        actions = cube.actions_possibles(coup_interdit)
        situations = np.ndarray(shape=(0, 54))
        for action in actions:
            scratch = deepcopy(cube)
            scratch.set_state(scratch.grille * joueur, True)
            scratch.jouer(action, 1)
            situations = np.append(situations, [scratch.get_flatten_state()], axis=0)
        values = self(situations)
        i_max = max(range(0, len(values)), key=lambda i: values[i])
        return situations[i_max], actions[i_max]

    def choisir_non_deterministe(self, cube: Cube, joueur: int, coup_interdit: int = -1, disable_print: bool = True):
        actions = cube.actions_possibles(coup_interdit)
        situations = np.ndarray(shape=(0, 54))
        for action in actions:
            scratch = deepcopy(cube)
            scratch.set_state(scratch.grille * joueur, True)
            scratch.jouer(action, 1)
            situations = np.append(situations, [scratch.get_flatten_state()], axis=0)
        values = list(self(situations))
        if not disable_print:
            for i in range(len(situations)):
                print(actions[i], values[i][0])
        if all(v < 0 for v in values):
            i_max = max(range(len(actions)), key=lambda i: values[i])
            if not disable_print:
                print("All neg :", i_max)
            return actions[i_max]
        i = 0
        while i < len(actions):
            if values[i] < 0:
                actions.pop(i)
                values.pop(i)
            else:
                i += 1
        if not disable_print:
            print("Not neg :")
            for i in range(len(actions)):
                print(actions[i], values[i][0])
        values = list(map(lambda x: x**2, values))
        somme = sum(values)
        if not disable_print:
            print("Somme :", somme)
        choix = random() * somme
        if not disable_print:
            print("Choix :", choix)
        i = 0
        while choix > sum(values[:i+1]):
            i += 1
        if not disable_print:
            print("Action :", actions[i])
        return actions[i]

    def choisir_non_deterministe2(self, cube: Cube, joueur: int, coup_interdit: int = -1):
        actions = cube.actions_possibles(coup_interdit)
        situations = np.ndarray(shape=(0, 54))
        for action in actions:
            scratch = deepcopy(cube)
            scratch.set_state(scratch.grille * joueur, True)
            scratch.jouer(action, 1)
            situations = np.append(situations, [scratch.get_flatten_state()], axis=0)
        values = self(situations)
        if max(values) > 0.9:
            return max(range(len(values)), key=lambda i: values[i])
        mini = min(values)
        if mini < 0:
            values = list(map(lambda v: (v - mini)**2, values))
        else:
            values = list(map(lambda v: v**2, values))
        somme = sum(values)
        choix = random() * somme
        i = 0
        somme_acc = values[0]
        while choix > somme_acc:
            i += 1
            somme_acc += values[i]
        return actions[i]

    def choisir_non_det_sit(self, cube: Cube, joueur: int, coup_interdit: int = -1):
        actions = cube.actions_possibles(coup_interdit)
        situations = np.ndarray(shape=(0, 54))
        for action in actions:
            scratch = deepcopy(cube)
            scratch.set_state(scratch.grille * joueur, True)
            scratch.jouer(action, 1)
            situations = np.append(situations, [scratch.get_flatten_state()], axis=0)
        values = self(situations)
        if max(values) > 0.9:
            i_max = max(range(len(values)), key=lambda i: values[i])
            return situations[i_max], actions[i_max]
        mini = min(values)
        if mini < 0:
            values = list(map(lambda v: (v - mini), values))
        somme = sum(values)
        choix = random() * somme
        i = 0
        somme_acc = values[0]
        while choix > somme_acc:
            i += 1
            somme_acc += values[i]
        return situations[i], actions[i]


import os
from random import choice
from copy import deepcopy
from numpy import ndarray, append, reshape, array
from cube import Cube, Surface
from tensorflow import constant
from tensorflow.keras.models import load_model  # type: ignore


class SuperAgent:
    def __init__(self, path: str, niveau: int):
        self.path = path
        self.niveau = niveau
        self.models = []
        self.load_models()

    def load_models(self):
        self.models = [load_model(self.path.format(i)) for i in range(3)]

    def choisir(self, cube: Cube, joueur: int, coup_interdit: int = -1):
        if self.niveau == 0:
            return self.choisir_morpion(cube, joueur, coup_interdit)
        elif self.niveau in (1, 2):
            return self.choisir_normal(cube, joueur, self.niveau, coup_interdit)
        elif self.niveau == 3:
            return self.choisir_deep_thought(cube, joueur, 5, 1, coup_interdit)
        else:
            return self.choisir_deep_thought(cube, joueur, 5, 2, coup_interdit)

    def choisir_morpion(self, cube: Cube, joueur: int, coup_interdit: int = -1):
        actions = sorted(cube.actions_possibles())
        if actions[-1] < 18:
            return choice(actions)
        new_actions = []
        for action in actions:
            if action >= 18:
                new_actions.append(action)
        situations = ndarray(shape=(0, 9))
        for action in new_actions:
            scratch = deepcopy(cube)
            scratch.set_state(scratch.grille * joueur, True)
            scratch.jouer(action, 1)
            situations = append(situations, [scratch.get_flatten_state()[:9]], 0)
        values = self.models[0](situations)
        i_max = 0
        for i in range(1, len(values)):
            if values[i] > values[i_max]:
                i_max = i
        return new_actions[i_max]

    def choisir_normal(self, cube: Cube, joueur: int, niveau: int, coup_interdit: int = -1):
        actions = cube.actions_possibles(coup_interdit)
        situations = ndarray(shape=(0, 54))
        for action in actions:
            scratch = deepcopy(cube)
            scratch.set_state(scratch.grille * joueur, True)
            scratch.jouer(action, 1)
            situations = append(situations, [scratch.get_flatten_state()], 0)
        values = self.models[niveau - 1](situations)
        i_max = 0
        for i in range(1, len(values)):
            if values[i] > values[i_max]:
                i_max = i
        return actions[i_max]

    def choisir_deep_rec(self, etat: ndarray, joueur: int, largeur: int, profondeur: int, coup_interdit: int = -1):
        surface = Surface(etat)
        cube = Cube(surface)
        actions = cube.actions_possibles(coup_interdit)
        concrete_largeur = max(min(largeur, len(actions)), 1)
        situations = []
        actions_gagnantes = []
        for action in actions:
            scratch = Cube()
            scratch.set_state(etat, True)
            scratch.jouer(action, joueur)
            if (gagnant := scratch.terminal_state())[0]:
                gain = gagnant[1]
                if gain * joueur >= 1:
                    return constant(float(gain)) * 10, action
                actions_gagnantes.append((action, gain))
            situations.append(scratch.get_flatten_state())
        values = list(self.models[-1](array(situations)))
        for action, gagnant in actions_gagnantes:
            values[actions.index(action)] = constant(float(gagnant)) * 10
        if profondeur == 0:
            if joueur == 1:  # Quand c'est le tour de l'IA
                i = max(range(len(actions)), key=lambda x: values[x])
            else:  # Quand c'est le tour de l'adversaire
                i = min(range(len(actions)), key=lambda x: values[x])
            return values[i], actions[i]
        mapper = map(lambda i: values[i], range(len(actions)))
        actions.sort(reverse=joueur == 1, key=lambda arg: next(mapper))
        mapper = map(lambda i: values[i], range(len(situations)))
        situations.sort(reverse=joueur == 1, key=lambda arg: next(mapper))
        values.sort(reverse=joueur == 1)
        values = values[:concrete_largeur]
        for i in range(concrete_largeur):
            if actions[i] not in actions_gagnantes:
                coup_interdit = (actions[i] + 9) % 18 if actions[i] < 18 else -1
                new_value = self.choisir_rec(reshape(situations[i], (6, 3, 3)), joueur * -1, largeur, profondeur - 1,
                                             coup_interdit)[0]
                if new_value == int(new_value):
                    if new_value > 1:
                        new_value -= 1
                    elif new_value < -1:
                        new_value += 1
                values[i] = new_value
        if joueur == 1:
            i_max = max(range(concrete_largeur), key=lambda j: values[j])
            i = i_max
            while values[i] <= -1 and i < len(actions) - 1:
                i = concrete_largeur
                concrete_largeur += 1
                values.append(
                    self.choisir_deep_rec(reshape(situations[i], (6, 3, 3)), joueur * -1, largeur, profondeur - 1,
                                          coup_interdit)[0])
                if values[i_max] < values[i]:
                    i_max = i
        else:
            i_max = min(range(concrete_largeur), key=lambda j: values[j])
            i = i_max
            while values[i] >= 1 and i < len(actions) - 1:
                i = concrete_largeur
                concrete_largeur += 1
                values.append(
                    self.choisir_deep_rec(reshape(situations[i], (6, 3, 3)), joueur * -1, largeur, profondeur - 1,
                                          coup_interdit)[0])
                if values[i_max] > values[i]:
                    i_max = i
        return values[i_max], actions[i_max]

    def choisir_deep_thought(self, cube: Cube, joueur: int, largeur: int, profondeur: int, coup_interdit: int = -1):
        res = self.choisir_deep_rec(cube.get_state() * joueur, 1, largeur, profondeur, coup_interdit)
        action = res[1]
        return action


if __name__ == "__main__" :
    agent = Agent()
    generators = StateGenerator()
    selected_gen = generators.generator_perfection(55)

    agent.fit(selected_gen, steps_per_epoch=100, epochs=1000)
    agent.model.save(r"models\generation0\model14.h5")
    print(generators.gagnants)