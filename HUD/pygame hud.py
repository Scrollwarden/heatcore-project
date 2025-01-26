import pygame
import sys
from hud_elements import create_compass, create_heatcore_bar

"""This file is purely for HUD testing purposes"""
"""It is not to be refferenced anywhere and will be deleted later on"""

# Initialize Pygame
pygame.init()

# Screen dimensions
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("HUD Example")

# Colors
gray = (100, 100, 100)

# Initialize HUD elements
draw_compass = create_compass(screen)
heatcore_bar = create_heatcore_bar(screen)

# Variables
yaw = 0  # Initial yaw angle
heatcore_count = 0  # Initial heatcore count
space_pressed = False  # Tracks if the space key is currently pressed

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not space_pressed:
                heatcore_count = (heatcore_count + 1) % 4  # Increment heatcore_count by 1
                heatcore_bar.set_heatcore_count(heatcore_count)
                space_pressed = True  # Mark space as pressed
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                space_pressed = False  # Reset space pressed state

    # Handle yaw adjustment with Q and D keys
    keys = pygame.key.get_pressed()
    if keys[pygame.K_q]:
        yaw = (yaw - 0.1) % 360
    if keys[pygame.K_d]:
        yaw = (yaw + 0.1) % 360

    # Fill the screen with gray
    screen.fill(gray)

    # Draw HUD elements
    draw_compass(yaw)
    heatcore_bar.draw()

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
sys.exit()
