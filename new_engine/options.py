import math
import glm

# Main
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
BACKGROUND_COLOR = (0.0, 0.35, 0.7)
FPS = 60

CHUNK_SHADER = 'chunk'

# Chunk
CHUNK_SIZE = 16 # How long is the side of each chunk
LG2_CS = int(math.log2(CHUNK_SIZE)) # Log2 of the Chunk size in int (useful for detail)

# Scene
CHUNK_SCALE = 0.1 # By how much we scale every axis
HEIGHT_SCALE = 10.0 # By how much we scale the height
INV_NOISE_SCALE = 4.0 # How much info we put in a chunk

THREADS_LIMIT = 12 # Maximum number of threads at the same time
TASKS_PER_FRAME = 2 # How many threads can we create per frame (do not overload CPU)

# Chunk mesh
MAX_FALL_DISTANCE = - 0.7 * HEIGHT_SCALE * CHUNK_SCALE # By how much the 10th chunk fall out in the distanceT

# Player mesh
PLAYER_SCALE = 0.02 * CHUNK_SCALE

# Camera
FOV = 50
NEAR = 0.001
FAR = 100
SPEED = 0.01 * CHUNK_SCALE
SENSITIVITY = 0.05
SHIP_OFFSET = glm.vec3(5, -2, 0) * CHUNK_SCALE

# Player
FORWARD_FRICTION = 0.94
YAW_FRICTION = 0.9
YAW_ACCELERATION = 0.1
MAX_YAW_SPEED = 5.0
FORWARD_ACCELERATION = 0.5
BACKWARD_ACCELERATION = 0.5
MAX_SPEED = 0.01 * CHUNK_SCALE
MIN_SPEED = - 0.5 * MAX_SPEED