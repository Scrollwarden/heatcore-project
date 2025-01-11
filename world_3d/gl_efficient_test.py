import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from Chunk_Generator import ChunkTerrain, generate_chunk, HeightParams, ColorParams
from tqdm import tqdm

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
HEIGHT_SCALE = 5.0

class Camera:
    def __init__(self, position: float, rotation: float, speed: float = 0.5, sensitivity: float = 0.2):
        self.position = np.array(position, dtype=np.float32)
        self.rotation = np.array(rotation, dtype=np.float32)  # [pitch, yaw]
        self.speed = speed
        self.sensitivity = sensitivity

    def update(self, keys, mouse_dx, mouse_dy):
        # Mouse look
        self.rotation[1] += mouse_dx * self.sensitivity  # Yaw
        self.rotation[0] += mouse_dy * self.sensitivity  # Pitch
        self.rotation[0] = np.clip(self.rotation[0], -89, 89)  # Clamp pitch

        # Movement
        forward = np.array([
            np.sin(np.radians(self.rotation[1])),
            0,
            -np.cos(np.radians(self.rotation[1]))
        ], dtype=np.float32)
        right = np.cross(forward, np.array([0, 1, 0], dtype=np.float32))
        move_direction = np.zeros(3, dtype=np.float32)

        if keys[pygame.K_z]:
            move_direction += forward
        if keys[pygame.K_s]:
            move_direction -= forward
        if keys[pygame.K_d]:
            move_direction += right
        if keys[pygame.K_q]:
            move_direction -= right
        if keys[pygame.K_SPACE]:
            move_direction[1] += 1
        if keys[pygame.K_LCTRL]:
            move_direction[1] -= 1

        if np.linalg.norm(move_direction) > 0:
            move_direction /= np.linalg.norm(move_direction)  # Normalize
        self.position += move_direction * self.speed

    def apply(self):
        glRotatef(self.rotation[0], 1, 0, 0)  # Pitch
        glRotatef(self.rotation[1], 0, 1, 0)  # Yaw
        glTranslatef(-self.position[0], -self.position[1], -self.position[2])

def initialize_opengl():
    """Initialize OpenGL settings."""
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.6, 0.8, 1.0, 1.0)  # Light blue background
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glShadeModel(GL_SMOOTH)

    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 500)  # Extended far clipping plane
    glMatrixMode(GL_MODELVIEW)

def create_chunk_buffers(chunk: ChunkTerrain):
    """Generate VAO and VBO for a chunk."""
    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)

    # Buffer vertex data
    vertices = chunk.vertices.astype(np.float32)
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

    # Buffer color data
    triangle_colors = (chunk.colors.astype(np.float32) / 255.0).clip(0.0, 1.0)
    cbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, cbo)
    glBufferData(GL_ARRAY_BUFFER, triangle_colors.nbytes, triangle_colors, GL_STATIC_DRAW)
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)

    # Buffer element (index) data
    indices = chunk.triangles.flatten().astype(np.uint32)
    ebo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

    glBindVertexArray(0)
    return vao, vbo, cbo, ebo, indices.size

def draw_chunk_vao(vao, vbo, cbo, ebo, index_count):
    """Render a chunk using its VAO and bound buffers."""
    glBindVertexArray(vao)

    # Bind buffers explicitly (necessary even though they're part of VAO)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)  # First bind the vertex buffer
    glBindBuffer(GL_ARRAY_BUFFER, cbo)  # Then bind the color buffer
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)

    # Draw elements
    glDrawElements(GL_TRIANGLES, index_count, GL_UNSIGNED_INT, None)

    # Unbind buffers (optional)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindBuffer(GL_ARRAY_BUFFER, 0)  # Unbind color buffer
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    glBindVertexArray(0)

def debug_triangle():
    glBegin(GL_TRIANGLES)
    glColor3f(1.0, 0.0, 0.0)  # Red
    glVertex3f(-0.5, -0.5, -1.0)
    glColor3f(0.0, 1.0, 0.0)  # Green
    glVertex3f(0.5, -0.5, -1.0)
    glColor3f(0.0, 0.0, 1.0)  # Blue
    glVertex3f(0.0, 0.5, -1.0)
    glEnd()

def reset_color_state():
    glColor3f(1.0, 1.0, 1.0)  # Reset to default white color

def compile_shader(vertex_code, fragment_code):
    """Compile and link a shader program."""
    program = glCreateProgram()

    # Vertex Shader
    vertex = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(vertex, vertex_code)
    glCompileShader(vertex)
    if not glGetShaderiv(vertex, GL_COMPILE_STATUS):
        raise RuntimeError(glGetShaderInfoLog(vertex).decode())
    glAttachShader(program, vertex)

    # Fragment Shader
    fragment = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(fragment, fragment_code)
    glCompileShader(fragment)
    if not glGetShaderiv(fragment, GL_COMPILE_STATUS):
        raise RuntimeError(glGetShaderInfoLog(fragment).decode())
    glAttachShader(program, fragment)

    # Link Program
    glLinkProgram(program)
    if not glGetProgramiv(program, GL_LINK_STATUS):
        raise RuntimeError(glGetProgramInfoLog(program).decode())

    # Clean up
    glDeleteShader(vertex)
    glDeleteShader(fragment)

    return program

vertex_shader_code = """
#version 330 core
layout (location = 0) in vec3 position;
layout (location = 1) in vec3 color;

out vec3 fragColor;

uniform mat4 modelViewProjection;

void main() {
    gl_Position = modelViewProjection * vec4(position, 1.0);
    fragColor = color;
}
"""

fragment_shader_code = """
#version 330 core
in vec3 fragColor;
out vec4 outColor;

void main() {
    outColor = vec4(fragColor, 1.0);
}
"""

def main():
    pygame.init()
    pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF | OPENGL)
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    initialize_opengl()

    # Generate chunks
    height_param = HeightParams(5.0)
    color_param = ColorParams()
    scale = 3.0
    seed = 1
    chunk_positions = [(x, y) for x in range(-5, 5) for y in range(-5, 5)]  # A grid of 10x10 chunks
    chunk_vaos = []
    for x_chunk, y_chunk in tqdm(chunk_positions, desc="Generating chunks..."):
        chunk = generate_chunk(x_chunk, y_chunk, height_param, color_param, seed, 50, 5)
        chunk.update_detail(0, scale)
        vao, vbo, cbo, ebo, index_count = create_chunk_buffers(chunk)
        chunk_vaos.append((vao, vbo, cbo, ebo, index_count))

    # Camera setup
    camera = Camera(position=[0.0, 5.0, 0.0], rotation=[0.0, 0.0])

    clock = pygame.time.Clock()
    running = True
    while running:
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Mouse movement
        mouse_dx, mouse_dy = pygame.mouse.get_rel()

        # Update camera
        keys = pygame.key.get_pressed()
        camera.update(keys, mouse_dx, mouse_dy)

        # Rendering
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        camera.apply()

        # Draw all chunks
        for vao, vbo, cbo, ebo, index_count in chunk_vaos:
            draw_chunk_vao(vao, vbo, cbo, ebo, index_count)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()