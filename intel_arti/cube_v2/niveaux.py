from agent import Agent


class Partie :
    def __init__(self, agent : Agent):
        self.agent = agent





class GestionnaireParties :
    def __init__(self):
        self.niveau = 0
        self.load_agents()
    
    def load_agents(self) :
        self.agents = []


    def nouvelle_partie(self, niveau : int = None) :
        pass