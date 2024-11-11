import tensorflow as tf # pip install tensorflow
import numpy as np # pip install numpy
import time
from cube_environement import CubeEnv
from tqdm import tqdm # pip install tqdm
from agent_class import DQNAgent

# Initialize environment and agent
env = CubeEnv()
agent = DQNAgent(state_size=54, action_size=27)


# Training parameters
epochs = 300
batch_size = 32

# Le nom du modèle
model_name = "dqn_test_model"

# Training loop
start_time = time.time()
for e in range(epochs):
    # On recommence depuis le début
    state = env.reset()
    state = np.reshape(state, (1, 54))
    last_action = []
    for i in tqdm(range(500), desc=f"Episode {e + 1}/{epochs}", unit="step"):
        # L'agent aggit
        illegal_moves = [i + 18 for i in range(9) if state[0][i]] + last_action
        action = agent.act(state, illegal_moves)
        if action < 18 :
            if action < 9 :
                last_action = [action + 9]
            else :
                last_action = [action - 9]
        else :
            last_action = []
        # On regarde les récompense et tout
        next_state, reward, done = env.step(action)
        if not done and reward < 0 :
            agent.remember_bad(state, action, reward)
        next_state = np.reshape(next_state, (1, 54))
        # L'agent se souvient de la position
        #agent.remember(state, action, reward, next_state, done)
        # On passe à la prochaine position
        
        if done:
            if reward > 0 :
                agent.remember_winning(state, action, reward)
            else :
                agent.remember_losing(state, action, reward)
            # On demande à l'agent d'apprendre de ses erreurs
            agent.replay_wins()
            agent.replay_losses()
            agent.replay_bad()
            """if len(agent.memory) > batch_size :
                agent.replay(batch_size)"""
            # On arrête l'épisode quand la partie est finie, on affiche le temps pris et on sauvegarde le modèle
            print(f"Episode: {e + 1}/{epochs}, Score: {reward}")
            elapsed_time = time.time() - start_time
            print(f"Episode {e + 1}/{epochs} took: {int(elapsed_time // 3600)}h{int((elapsed_time % 3600) // 60):02}min{int(elapsed_time % 60):02}")
            if not (e+1) % 10 :
                model_path = f"{model_name}_{e+1}.h5"
                agent.model.save(model_path)
                print(f"Model saved to {model_path}")
            break
        state = next_state