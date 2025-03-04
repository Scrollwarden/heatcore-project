"""Generateur de la génération 1"""
import os
from random import choice
from copy import deepcopy
from numpy import ndarray, append, zeros, array
from cube import Cube
from agent import Agent
from generators import GeneratorWinState
from tensorflow.keras.models import load_model #type: ignore


MODEL_PATH = os.path.join(os.path.abspath(__file__).rstrip("gen_gen1.py"), "models\\generation0\\model{}.h5")

class PartieIAvsRandom :
    def __init__(self, agent : Agent):
        self.agent = agent
        self.joueur = 1
        self.coup_interdit = -1
        self.cube = Cube()
        self.pl_ia = choice((1, -1))
        self.states = ndarray((0, 54))
        self.gagnant = 0
        self.jouer()
        self.eval_states()
    
    def step(self) :
        if self.joueur == self.pl_ia :
            situation, action = self.agent.choisir_non_det_sit(self.cube, self.joueur, self.coup_interdit)
            self.states = append(self.states, [situation], 0)
            self.cube.set_flatten_state(situation)
        else :
            action = choice(self.cube.actions_possibles(self.coup_interdit))
            copie = deepcopy(self.cube.get_state())
            self.cube.jouer(action, self.joueur)
            while action < 18 and (situation := self.cube.get_state()) == copie :
                action = choice(self.cube.actions_possibles(self.coup_interdit))
                self.cube.jouer(action, self.joueur)
            self.states = append(self.states, [situation], 0)
        self.cube.set_flatten_state(situation)
        self.joueur *= -1
        if action < 18 :
            self.coup_interdit = (action + 9) % 18
        else :
            self.coup_interdit = -1




class PartieIAvsIA :
    def __init__(self, agent1 : Agent, agent2 : Agent) :
        """Initialise une partie."""
        self.joueur = 1
        self.coup_interdit = -1
        self.cube = Cube()
        self.agent1 = agent1
        self.agent2 = agent2
        self.pl_ia1 = choice((1, -1))
        self.states = ndarray((0, 54))
        self.gagnant = 0
        self.jouer()
        self.eval_states()

    def step(self) :
        if self.joueur == self.pl_ia1 :
            agent = self.agent1
        else :
            agent = self.agent2
        situation, action = agent.choisir_non_det_sit(self.cube, self.joueur, self.coup_interdit)
        self.states = append(self.states, [situation], 0)
        self.cube.set_flatten_state(situation*self.joueur)
        self.joueur *= -1
        if action < 18 :
            self.coup_interdit = (action + 9) % 18
        else :
            self.coup_interdit = -1
    
    def eval_states(self) :
        self.rewards = zeros((len(self.states)))
        if self.gagnant >= 1 : # Le joueur 1 a gagné
            for i in range(0, len(self.states), 2) :
                self.rewards[i] = self.gagnant/(1<<(len(self.states)-i)//2)
            for i in range(1, len(self.states), 2) :
                self.rewards[i] = -self.gagnant/(1<<(len(self.states)-i-1)//2)
        elif self.gagnant <= -1 : # Le joueur -1 (ou 2) a gagné
            for i in range(1, len(self.states), 2) :
                self.rewards[i] = -self.gagnant/(1<<(len(self.states)-i)//2)
            for i in range(0, len(self.states), 2) :
                self.rewards[i] = self.gagnant/(1<<(len(self.states)-i-1)//2)
        else : # Egalite
            pass
    
    def jouer(self) :
        while not (gagnant := self.cube.terminal_state())[0] :
            self.step()
        self.gagnant = gagnant[1]
    
    def get_data(self) :
        return self.states, self.rewards

class PartieGenerator :
    def __init__(self, agent1 : Agent, agent2 : Agent):
        self.gagnants = {}
        self.agent1 = agent1
        self.agent2 = agent2
    
    def generator_basic(self, batch_size : int) :
        """Génère des situations gagnées par l'équipe 1"""
        gen = GeneratorWinState()
        while True :
            partie = PartieIAvsIA(self.agent1, self.agent2)
            self.gagnants[partie.gagnant] = self.gagnants.get(partie.gagnant, 0) + 1
            states, rewards = partie.get_data()
            rewards = rewards.flatten()
            if (nb_overflow_data := states.shape[0] - batch_size) > 0 :
                states = states[nb_overflow_data:]
                rewards = rewards[nb_overflow_data:]
            elif (manque := batch_size - states.shape[0]) > 0 :
                if manque > 10 :
                    partie = PartieIAvsIA(self.agent1, self.agent2)
                    self.gagnants[partie.gagnant] = self.gagnants.get(partie.gagnant, 0) + 1
                    x, y = partie.get_data()
                    states = append(states, x, 0)
                    rewards = append(rewards, y.flatten())
                    if (nb_overflow_data := states.shape[0] - batch_size) > 0 :
                        states = states[nb_overflow_data:]
                        rewards = rewards[nb_overflow_data:]
                gen.generate_end_states(manque)
                states = append(states, array(gen.liste_win_state), 0)
                rewards = append(rewards, array(gen.liste_eval))
            yield states, rewards

if __name__ == "__main__" :
    agent = Agent()
    agent1 = Agent(True)
    agent1.model = load_model(MODEL_PATH.format(14))
    generators = PartieGenerator(agent1, agent1)
    selected_gen = generators.generator_basic(25)

    agent.fit(selected_gen, steps_per_epoch=100, epochs=500)
    agent.model.save(r"models\generation1\model2.h5")
    print(generators.gagnants)
    """
    agent1 = Agent(True)
    agent1.model = load_model(MODEL_PATH.format(14))
    partie = PartieIAvsIA(agent1, agent1)
    cube = Cube()
    for ele in partie.states :
        cube.set_flatten_state(ele)
        print(cube)"""