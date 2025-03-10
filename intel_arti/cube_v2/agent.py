import os
from typing import Any
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import Dense # type: ignore
from tensorflow.keras import Input, Model # type: ignore
from tensorflow.keras.models import load_model #type: ignore
from tensorflow import Tensor, constant
import tensorflow as tf
from random import random, randint
from generators import StateGenerator, random_cube_perdant
from cube import Cube, Surface
from copy import deepcopy
from numpy import ndarray, append, array, reshape

from parameters import *



MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models\\generation0\\model17_{}.h5")

class SaveEveryNEpochs(tf.keras.callbacks.Callback):
    def __init__(self, n_epochs=500):
        super(SaveEveryNEpochs, self).__init__()
        self.save_path = MODEL_PATH
        self.n_epochs = n_epochs

    def on_epoch_end(self, epoch, logs=None):
        if (epoch+1) % self.n_epochs == 0:  # +1 car epoch commence à 0
            self.model.save(self.save_path.format(epoch+1))
            print(f"Modèle enregistré à l'époque {epoch+1}")

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
        values = list(self(situations))
        mapper = map(lambda i : values[i], range(len(actions)))
        actions.sort(reverse=True, key=lambda arg : next(mapper))
        values.sort(reverse=True)
        i_max = 0
        for i in range(1, len(values)) :
            if values[i] > values[i_max] :
                i_max = i
        for i in range(len(actions)) :
            print(actions[i], values[i])
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
        values = list(self(situations))
        mapper = map(lambda i : values[i], range(len(actions)))
        actions.sort(reverse = True, key = lambda arg : next(mapper))
        values.sort(reverse = True)
        if values[0] > 0.9 :
            print(actions[0], values[0])
            return actions[0]
        if (mini := values[-1]) < 0 :
            values = list(map(lambda v : (v-mini)**3, values))
        else :
            values = list(map(lambda v : v**3, values))
        print("Actions :")
        for i in range(len(values)) :
            print(actions[i], float(values[i]))
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

    def choisir_reponse(self, situ : ndarray, joueur : int, coup_interdit : int = -1) :
        cube = Cube()
        cube.set_flatten_state(situ)
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
        return Answer(actions[i_max], situations[i_max], values[i_max])


class DeepThought :
    def __init__(self, agent : Agent) :
        self.agent = agent
    
    def choisir_rec(self, etat : ndarray, joueur : int, largeur : int, profondeur : int, coup_interdit : int = -1, info_mode : bool = False) :
        surface = Surface(etat)
        cube = Cube(surface)
        actions = cube.actions_possibles(coup_interdit)
        concrete_largeur = max(min(largeur, len(actions)), 1)
        situations = []
        actions_gagnantes = []
        for action in actions :
            scratch = Cube()
            scratch.set_state(etat, True)
            scratch.jouer(action, joueur)
            if (gagnant := scratch.terminal_state())[0] :
                gain = gagnant[1]
                if gain * joueur >= 1 :
                    return constant(float(gain)) * 10, action
                actions_gagnantes.append((action, gain))
            situations.append(scratch.get_flatten_state())
        values = list(self.agent(array(situations)))
        for action, gagnant in actions_gagnantes :
            values[actions.index(action)] = constant(float(gagnant)) * 10
        if profondeur == 0 :
            if joueur == 1 : # Quand c'est le tour de l'IA
                i = max(range(len(actions)), key=lambda x : values[x])
            else : # Quand c'est le tour de l'adversaire
                i = min(range(len(actions)), key=lambda x : values[x])
            return values[i], actions[i]
        mapper = map(lambda i : values[i], range(len(actions)))
        actions.sort(reverse=joueur==1, key=lambda arg : next(mapper))
        mapper = map(lambda i : values[i], range(len(situations)))
        situations.sort(reverse=joueur==1, key=lambda arg : next(mapper))
        values.sort(reverse=joueur==1)
        values = values[:concrete_largeur]
        """if values[0] * joueur <= -1 :
            return values[0], action[0]"""
        print("Profondeur :", profondeur, "Before :")
        for i in range(concrete_largeur) :
            print(actions[i], values[i])
        for i in range(concrete_largeur) :
            if actions[i] not in actions_gagnantes :
                coup_interdit = (actions[i] + 9) % 18 if actions[i] < 18 else -1
                """print("Coup joué :", actions[i])"""
                new_value = self.choisir_rec(reshape(situations[i], (6, 3, 3)), joueur*-1, largeur, profondeur-1, coup_interdit, info_mode)[0]
                if new_value == int(new_value) :
                    if new_value > 1 :
                        new_value -= 1
                    elif new_value < -1 :
                        new_value += 1
                values[i] = new_value
        """if joueur == 1 :
            mapper = map(lambda i : values[i] if i < concrete_largeur else max(values)+i, range(len(actions)))
        else :
            mapper = map(lambda i : values[i] if i < concrete_largeur else min(values)-i, range(len(actions)))

        actions.sort(reverse=joueur==1, key=lambda arg : next(mapper))
        if joueur == 1 :
            mapper = map(lambda i : values[i] if i < concrete_largeur else max(values)+i, range(len(situations)))
        else :
            mapper = map(lambda i : values[i] if i < concrete_largeur else min(values)-i, range(len(situations)))
        situations.sort(reverse=joueur==1, key=lambda arg : next(mapper))
        values.sort(reverse=joueur==1)"""
        print("Profondeur :", profondeur, "After :")
        for i in range(concrete_largeur) :
            print(actions[i], values[i])
        if joueur == 1 :
            i_max = max(range(concrete_largeur), key=lambda j : values[j])
            i = i_max
            while values[i] <= -1 and i < len(actions) - 1 :
                i = concrete_largeur
                concrete_largeur += 1
                values.append(self.choisir_rec(reshape(situations[i], (6, 3, 3)), joueur*-1, largeur, profondeur-1, coup_interdit, info_mode)[0])
                if values[i_max] < values[i] :
                    i_max = i
        else :
            i_max = min(range(concrete_largeur), key=lambda j : values[j])
            i = i_max
            while values[i] >= 1 and i < len(actions) - 1 :
                i = concrete_largeur
                concrete_largeur += 1
                values.append(self.choisir_rec(reshape(situations[i], (6, 3, 3)), joueur*-1, largeur, profondeur-1, coup_interdit, info_mode)[0])
                if values[i_max] > values[i] :
                    i_max = i
        return values[i_max], actions[i_max]
    
    def choisir_rec2(self, etat : ndarray, joueur : int, largeur : int, profondeur : int, coup_interdit : int = -1, info_mode : bool = False) :
        """Ancien"""
        surface = Surface(etat)
        cube = Cube(surface)
        actions = cube.actions_possibles(coup_interdit)
        concrete_largeur = max(min(largeur, len(actions)), 1)
        situations = []
        actions_gagnantes = []
        for action in actions :
            scratch = Cube()
            scratch.set_state(etat, True)
            scratch.jouer(action, joueur)
            if (gagnant := scratch.terminal_state())[0] :
                actions_gagnantes.append((action, gagnant[1]))
            situations.append(scratch.get_flatten_state())
        values = list(self.agent(array(situations)))
        for action, gagnant in actions_gagnantes :
            values[actions.index(action)] = constant(float(gagnant))
        """if info_mode :
            print("Profondeur :", profondeur, "Joueur :", joueur)
            for i in range(len(actions)) :
                print(actions[i], values[i], ":")
                c = Cube()
                c.set_flatten_state(situations[i])
                print(c)"""
        if profondeur == 0 :
            if joueur == 1 : # Quand c'est le tour de l'IA
                i = max(range(len(actions)), key=lambda x : values[x])
            else : # Quand c'est le tour de l'adversaire
                i = min(range(len(actions)), key=lambda x : values[x])
            """if info_mode :
                c = Cube()
                c.set_flatten_state(situations[i])
                print(cube)
                print(c)
            print(values[i], actions[i], joueur)"""
            return values[i], actions[i]
        mapper = map(lambda i : values[i], range(len(actions)))
        actions.sort(reverse=joueur==1, key=lambda arg : next(mapper))
        mapper = map(lambda i : values[i], range(len(situations)))
        situations.sort(reverse=joueur==1, key=lambda arg : next(mapper))
        values.sort(reverse=joueur==1)
        if joueur == 1 and values[0] > 0.9 : # Si le modèle gagne avec ce coup
            """if info_mode :
                print("Plus que 0.9")
            print(values[0], actions[0])"""
            return values[0], actions[0]
        if joueur == -1 and values[0] < -0.9 : # Si le modèle perd avec ce coup
            """if info_mode :
                print("Moins que -0.9")
            print(values[0], actions[0])"""
            return values[0], actions[0]
        """print(max(values), min(values))"""
        actions = actions[:concrete_largeur]
        situations = situations[:concrete_largeur]
        values = values[:concrete_largeur]
        print("Profondeur :", profondeur, "Before :")
        for i in range(len(actions)) :
            print(actions[i], values[i])
        for i in range(concrete_largeur) :
            coup_interdit = (actions[i] + 9) % 18 if actions[i] < 18 else -1
            """print("Coup joué :", actions[i])"""
            values[i] = self.choisir_rec2(reshape(situations[i], (6, 3, 3)), joueur*-1, largeur, profondeur-1, coup_interdit, info_mode)[0]
        mapper = map(lambda i : values[i], range(len(actions)))
        actions.sort(reverse=joueur==1, key=lambda arg : next(mapper))
        mapper = map(lambda i : values[i], range(len(situations)))
        situations.sort(reverse=joueur==1, key=lambda arg : next(mapper))
        values.sort(reverse=joueur==1)
        print("Profondeur :", profondeur, "After :")
        for i in range(len(actions)) :
            print(actions[i], values[i])
        if joueur == 1 :
            i = max(range(len(actions)), key=lambda x : values[x])
        else :
            i = min(range(len(actions)), key=lambda x : values[x])
        """if info_mode and profondeur == 1 :
            print(cube, joueur, sep='\n')
            c = Cube()
            c.set_flatten_state(situations[i])
            print(c)"""
        return values[i], actions[i]




    
    def choisir(self, cube : Cube, joueur : int,  largeur : int, profondeur : int, coup_interdit : int = -1, info_mode : bool = False) :
        res = self.choisir_rec(cube.get_state()*joueur, 1, largeur, profondeur, coup_interdit, info_mode=info_mode)
        print("Action choisie :", res[1], res[0])
        action = res[1]
        return action

    def choisir_rec_non_det(self, etat : ndarray, joueur : int, largeur : int, profondeur : int, coup_interdit : int = -1, info_mode : bool = False) :
        surface = Surface(etat)
        cube = Cube(surface)
        actions = cube.actions_possibles(coup_interdit)
        concrete_largeur = max(min(largeur, len(actions)), 1)
        situations = []
        for action in actions :
            scratch = Cube()
            scratch.set_state(etat, True)
            scratch.jouer(action, joueur)
            situations.append(scratch.get_flatten_state())
        values = list(self.agent(array(situations)))
        """if info_mode :
            print("Profondeur :", profondeur, "Joueur :", joueur)
            for i in range(len(actions)) :
                print(actions[i], values[i], ":")
                c = Cube()
                c.set_flatten_state(situations[i])
                print(c)"""
        if profondeur == 0 :
            if joueur == 1 : # Quand c'est le tour de l'IA
                i = max(range(len(actions)), key=lambda x : values[x])
            else : # Quand c'est le tour de l'adversaire
                i = min(range(len(actions)), key=lambda x : values[x])
            """if info_mode :
                c = Cube()
                c.set_flatten_state(situations[i])
                print(cube)
                print(c)
            print(values[i], actions[i], joueur)"""
            return values[i], actions[i]
        
        mapper = map(lambda i : values[i], range(len(actions)))
        actions.sort(reverse=joueur==1, key=lambda arg : next(mapper))
        mapper = map(lambda i : values[i], range(len(situations)))
        situations.sort(reverse=joueur==1, key=lambda arg : next(mapper))
        values.sort(reverse=joueur==1)
        if joueur == 1 and values[0] > 8 : # Si le modèle gagne avec ce coup
            """if info_mode :
                print("Plus que 0.9")
            print(values[0], actions[0])"""
            return values[0], actions[0]
        if joueur == -1 and values[0] < -8 : # Si le modèle perd avec ce coup
            """if info_mode :
                print("Moins que -0.9")
            print(values[0], actions[0])"""
            return values[0], actions[0]
        """print(max(values), min(values))"""
        actions = actions[:concrete_largeur]
        situations = situations[:concrete_largeur]
        values = values[:concrete_largeur]
        print("Profondeur :", profondeur, "Before :")
        for i in range(len(actions)) :
            print(actions[i], values[i])
        for i in range(concrete_largeur) :
            coup_interdit = (actions[i] + 9) % 18 if actions[i] < 18 else -1
            """print("Coup joué :", actions[i])"""
            values[i] = self.choisir_rec(reshape(situations[i], (6, 3, 3)), joueur*-1, largeur, profondeur-1, coup_interdit, info_mode)[0]
        mapper = map(lambda i : values[i], range(len(actions)))
        actions.sort(reverse=joueur==1, key=lambda arg : next(mapper))
        mapper = map(lambda i : values[i], range(len(situations)))
        situations.sort(reverse=joueur==1, key=lambda arg : next(mapper))
        values.sort(reverse=joueur==1)
        print("Profondeur :", profondeur, "After :")
        for i in range(len(actions)) :
            print(actions[i], values[i])
        if joueur == 1 :
            i = max(range(len(actions)), key=lambda x : values[x])
        else :
            i = min(range(len(actions)), key=lambda x : values[x])
        """if info_mode and profondeur == 1 :
            print(cube, joueur, sep='\n')
            c = Cube()
            c.set_flatten_state(situations[i])
            print(c)"""
        return values[i], actions[i]
    
    def choisir_non_det(self, cube : Cube, joueur : int,  largeur : int, profondeur : int, coup_interdit : int = -1, info_mode : bool = False) :
        action = self.choisir_rec_non_det(cube.get_state()*joueur, 1, largeur, profondeur, coup_interdit, info_mode=info_mode)[1]
        return action


class Answer :
    def __init__(self, action : int, situation : ndarray, value : float) :
        self.action = action
        self.situation = situation
        self.value = value
    
    def explore(self, agent : Agent, largeur : int, profondeur : int, coup_interdit : int = -1) :
        if profondeur == 0 :
            return self
        
        next_level = agent.choisir_reponse(self.situation, -1, )
        return self.explore(agent, largeur, profondeur-1)








if __name__ == "__main__" :
    agent = Agent()
    generators = StateGenerator()
    selected_gen = generators.generator_perfection(55)

    agent.fit(selected_gen, steps_per_epoch=100, epochs=10000, callbacks=[SaveEveryNEpochs()])
    agent.model.save(r"models\generation0\model17.h5")
    print(generators.gagnants)
    """agent = Agent(True)
    agent.model = load_model(MODEL_PATH)
    deep_thoughts = DeepThought(agent)
    cube = random_cube_perdant()
    for _ in range(5) :
        cube.set_pion((randint(0, 5), randint(0, 2), randint(0, 2)), 1)
    cube.set_colonne(3, 2, array((-1, -1, -1)))
    print(cube)
    print(cube.terminal_state())
    print(agent(reshape(cube.get_flatten_state(), (1, 54))))"""
    {0: 6248, 1: 546852, -1: 433544, 2: 7616, -2: 5587, 3: 92, -3: 76, 4: 1}
