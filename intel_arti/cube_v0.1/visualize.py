import numpy as np
import tensorflow as tf
from cube_environement import CubeEnv
from agent_class import DQNAgent

# Load the trained model
model_path = "dqn_test_model_1.keras"


# Initialize the environment and agent
env = CubeEnv()
agent = DQNAgent(state_size=54, action_size=27, no_model=True)
agent.model = tf.keras.models.load_model(model_path) # Use the loaded model

def visualize_game(agent, env):
    state = env.reset()
    state = np.reshape(state, [1, 54])
    done = False
    player = 1  # Cross starts first
    last_action = []
    while not done:
        # Get action from agent
        illegal_moves = [i + 18 for i in range(9) if state[0][i]] + last_action
        action = agent.act(state, illegal_moves, test_model=True)
        if action < 18 :
            if action < 9 :
                last_action = [action + 9]
            else :
                last_action = [action - 9]
        else :
            last_action = []
        node_outputs = agent.model.predict(state)[0]  # Get the model's output probabilities

        # Execute the action in the environment
        next_state, reward, done = env.step(action)
        next_state = np.reshape(next_state, [1, 54])

        # Print the current game state
        print(f"\nPlayer {'X' if player == 1 else 'O'} move:")
        print(f"Action chosen: {action}")
        print(f"Reward given: {reward}")
        print(f"Node outputs (Q-values): {node_outputs}")
        env.render()

        # Update state
        state = next_state
        player = -player  # Switch player

        if done:
            print("\nGame Over!")
            if player == -1:
                print("Player X wins!")
            elif player == 1:
                print("Player O wins!")
            else:
                print("It's a draw!")
            env.render()

# Visualize the agent playing against itself
visualize_game(agent, env)