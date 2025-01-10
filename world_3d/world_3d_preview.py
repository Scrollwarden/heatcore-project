import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy as np
from Chunk_Generator import ChunkTerrain, generate_chunk, HeightParams, ColorParams
import time

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
HEIGHT_SCALE = 5.0

def initialize_opengl():
    """Initialize OpenGL settings."""
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glClearColor(0.6, 0.8, 1.0, 1)  # Light blue background
    glShadeModel(GL_SMOOTH)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 50)
    glMatrixMode(GL_MODELVIEW)

def draw_chunk(chunk: ChunkTerrain):
    """Render a chunk in 3D."""
    glBegin(GL_TRIANGLES)
    for i in range(len(chunk.triangles)):
        vertices = [chunk.vertices[x, y] for x, y in chunk.triangles[i]]
        color_index = chunk.colors[i]
        color = chunk.color_data[color_index[0], color_index[1]] / 255  # Normalize to 0-1 for OpenGL
        glColor3f(color[0], color[1], color[2])
        for vertex in vertices:
            glVertex3f(vertex[0], vertex[1] * HEIGHT_SCALE, vertex[2])
    glEnd()

def main():
    pygame.init()
    pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF | OPENGL)
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)  # Lock the mouse to the window

    initialize_opengl()

    # Generate chunks
    height_param = HeightParams()
    color_param = ColorParams()
    chunks = []
    scale = 3.0
    seed = 1
    chunk_positions = [(x, y) for x in range(-5, 5) for y in range(-5, 5)]  # A grid of 10x10 chunks
    for x_chunk, y_chunk in chunk_positions:
        chunk = generate_chunk(x_chunk, y_chunk, height_param, color_param, seed, 50, 5)
        chunk.update_detail(0, scale)
        chunks.append(chunk)

    # Camera setup
    camera_pos = [0.0, 5.0, 0.0]  # Starting position
    camera_rot = [0.0, 0.0]  # Pitch and yaw
    camera_speed = 0.5
    sensitivity = 0.2

    clock = pygame.time.Clock()
    last_time = time.time()
    
    running = True
    while running:
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Mouse look
        mouse_dx, mouse_dy = pygame.mouse.get_rel()
        camera_rot[1] += mouse_dx * sensitivity  # Yaw
        camera_rot[0] += mouse_dy * sensitivity  # Pitch
        camera_rot[0] = max(-89, min(89, camera_rot[0]))  # Clamp pitch

        # Movement
        keys = pygame.key.get_pressed()
        forward = np.array([
            np.sin(np.radians(camera_rot[1])),
            0,
            -np.cos(np.radians(camera_rot[1]))
        ])
        right = np.array([
            np.cos(np.radians(camera_rot[1])),
            0,
            np.sin(np.radians(camera_rot[1]))
        ])
        up = np.array([0, 1, 0])

        move_direction = np.array([0.0, 0.0, 0.0])
        if keys[pygame.K_z]:
            move_direction += forward
        if keys[pygame.K_s]:
            move_direction -= forward
        if keys[pygame.K_d]:
            move_direction += right
        if keys[pygame.K_q]:
            move_direction -= right
        if keys[pygame.K_SPACE]:
            move_direction += up
        if keys[pygame.K_LCTRL]:
            move_direction -= up

        if np.linalg.norm(move_direction) > 0:
            move_direction = move_direction / np.linalg.norm(move_direction)  # Normalize
        camera_pos += move_direction * camera_speed

        # Rendering
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glRotatef(camera_rot[0], 1, 0, 0)  # Pitch
        glRotatef(camera_rot[1], 0, 1, 0)  # Yaw
        glTranslatef(-camera_pos[0], -camera_pos[1], -camera_pos[2])

        for chunk in chunks:
            draw_chunk(chunk)

        pygame.display.flip()
        clock.tick(60)
        
        end_time = time.time()
        print(f"FPS: {1 / (end_time - last_time)}")
        last_time = end_time
        

    pygame.quit()

if __name__ == "__main__":
    main()
