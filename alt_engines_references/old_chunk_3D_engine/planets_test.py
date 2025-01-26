"""
Script pour faire des test astronomiques sur une planète et son orbite
Fait bien évidemment par chatgpt avec ma supervision (façon stylé de dire qu'il faisait n'imp des fois)
Raisons:
* Je n'y connais rien en astronomie
* Trop la flemme de me tapper 3 heures de code quand je peux le faire en 1 heure (ça prend un peu de temps n'empêche)
* Trop la flemme x2
"""

import pygame
import numpy as np
from collections import deque

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 800  # Screen dimensions
SCALE = 2e6 # Scale to fit objects on the screen
FPS = 60  # Frames per second

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)

def calculate_mass(density, radius):
    """Calculate mass from density and radius using the formula for the volume of a sphere."""
    return density * (4/3) * np.pi * radius**3

def calculate_temperature_from_kelvin(temperature):
    return temperature - 272.15

def calculate_temperature_from_celcius(temperature):
    return temperature + 272.15

class SpaceObject:
    def __init__(self, name, density, mass, position, velocity, color):
        self.name = name
        self.density = density  # kg/m³
        self.mass = mass        # kg
        self.position = np.array(position, dtype=float)  # meters
        self.velocity = np.array(velocity, dtype=float)  # meters/second
        self.radius = self.calculate_radius()           # meters
        self.color = color
        self.trail = deque()  # List to store trail points

    def calculate_radius(self):
        """Calculate the radius based on mass and density."""
        volume = self.mass / self.density
        radius = (3 * volume / (4 * np.pi)) ** (1/3)
        return radius

    def update_position(self, force, dt):
        """Update position and velocity using the gravitational force."""
        acceleration = force / self.mass
        self.velocity += acceleration * dt
        self.position += self.velocity * dt
        # Add position to the trail
        self.trail.append(self.position.copy())
        if len(self.trail) > 10000:  # Limit trail length
            self.trail.popleft()

    def display(self, screen, scale = 1.0):
        """Draw the object on the screen."""
        # Scale the position and radius for display
        scaled_pos = (self.position / SCALE + np.array([WIDTH / 2, HEIGHT / 2])).astype(int)
        pygame.draw.circle(screen, self.color, scaled_pos, max(int(self.radius / SCALE * scale), 2))  # Scaled size
        # Draw the trail
        if len(self.trail) > 1:
            trail_points = [(p / SCALE + np.array([WIDTH / 2, HEIGHT / 2])).astype(int) for p in self.trail]
            pygame.draw.lines(screen, self.color, False, trail_points, 1)
    
    def __repr__(self):
        # Use __dict__ to automatically represent all attributes
        attributes = ', '.join(f"{key}: {value}" for key, value in self.__dict__.items())
        return f"SpaceObject<{attributes}>"

def calculate_gravitational_force(obj1, obj2):
    """Calculate the gravitational force exerted by obj2 on obj1."""
    G = 6.67430e-11  # Gravitational constant (m³/kg/s²)
    displacement = obj2.position - obj1.position
    distance = np.linalg.norm(displacement)
    if distance == 0:
        return np.array([0, 0])  # Avoid division by zero
    force_magnitude = G * obj1.mass * obj2.mass / distance**2
    force_direction = displacement / distance
    return force_magnitude * force_direction

def calculate_planet_temperature(sun_mass, distance_to_sun, albedo=0.3):
    """Calculates the effective temperature of a planet based on the distance from the Sun, Sun's mass, and albedo."""
    stefan_boltzmann_constant = 5.670374419e-8  # Stefan-Boltzmann constant in W/m^2/K^4
    luminosity_constant = 3.846e26  # Solar luminosity for 1 solar mass in Watts

    # Calculate the luminosity of the Sun based on its mass
    luminosity = luminosity_constant * (sun_mass / 1.989e30) ** 3.5  # Relative luminosity formula
    solar_radiation = luminosity / (4 * np.pi * distance_to_sun**2) # Calculate solar radiation at the planet's distance
    absorbed_radiation = (1 - albedo) * solar_radiation # Adjust for the planet's albedo

    # Calculate the effective temperature using the Stefan-Boltzmann law
    effective_temperature = ((absorbed_radiation) / (4 * stefan_boltzmann_constant))**(1/4)

    return effective_temperature

def find_distance_for_temperature(sun_mass, desired_temp, albedo=0.3):
    """Finds the distance based on desired temperature."""
    stefan_boltzmann_constant = 5.670374419e-8  # Stefan-Boltzmann constant in W/m^2/K^4
    luminosity_constant = 3.846e26  # Solar luminosity for 1 solar mass in Watts
    luminosity = luminosity_constant * (sun_mass / 1.989e30) ** 3.5  # Sun's luminosity

    # Use the effective temperature equation: T = ((L * (1 - A)) / (4 * π * d^2 * σ))^(1/4) and solve for distance d
    distance = np.sqrt((luminosity * (1 - albedo)) / (4 * np.pi * stefan_boltzmann_constant * desired_temp**4))
    return distance

def create_orbiting_objects(sun_mass, sun_density, planet_mass, planet_density, f, perihelion_distance):
    """
    Creates SpaceObject instances for a sun and a planet with the given parameters.
    
    Parameters:
        sun_mass (float): Mass of the sun (kg).
        sun_density (float): Density of the sun (kg/m^3).
        planet_mass (float): Mass of the planet (kg).
        planet_density (float): Density of the planet (kg/m^3).
        f (float): Perihelion-to-aphelion distance factor.
        perihelion_distance (float): Closest approach of the planet to the sun (meters).
    
    Returns:
        tuple: SpaceObject instances for the sun and the planet.
    """
    # Calculate the aphelion distance based on the factor f
    aphelion_distance = f * perihelion_distance
    
    # Semi-major axis of the elliptical orbit
    semi_major_axis = (perihelion_distance + aphelion_distance) / 2
    
    # Calculate the velocity at perihelion using orbital mechanics
    gravitational_constant = 6.67430e-11  # m^3 kg^-1 s^-2
    perihelion_velocity = np.sqrt(
        gravitational_constant * sun_mass * (2 / perihelion_distance - 1 / semi_major_axis)
    )
    
    center = semi_major_axis - perihelion_distance
    
    # Create SpaceObject instances
    sun = SpaceObject(name="Sun", density=sun_density, mass=sun_mass, position=[center, 0], velocity=[0, 0], color=YELLOW)
    planet = SpaceObject(name="Planet", density=planet_density, mass=planet_mass, 
                         position=[perihelion_distance + center, 0],  # Starting at perihelion
                         velocity=[0, perihelion_velocity],  # Initial velocity at perihelion
                         color=BLUE)
    
    return sun, planet

def calculate_distances_for_temperature(sun_radius, planet_radius, desired_temp_perihelion, desired_temp_aphelion, albedo=0.3):
    """Calculates the distances for a planet to meet the desired temperatures at perihelion and aphelion."""

    # Calculate mass of Sun based on its radius and density
    sun_density = 1408 # Typical density of the Sun in kg/m^3
    sun_mass = calculate_mass(sun_density, sun_radius)
    planet_density = 5500 # Density of the Earth in kg/m^3
    planet_mass = calculate_mass(planet_density, planet_radius)

    # Find distances for perihelion and aphelion
    distance_perihelion = find_distance_for_temperature(sun_mass, desired_temp_perihelion, albedo)
    distance_aphelion = find_distance_for_temperature(sun_mass, desired_temp_aphelion, albedo)
    print(f"{distance_perihelion:e}", f"{distance_aphelion:e}")

    # Use the existing create_orbiting_objects function to generate the SpaceObject instances for Sun and Planet
    return create_orbiting_objects(sun_mass=sun_mass, sun_density=sun_density,
                                   planet_mass=planet_mass, planet_density=planet_density,
                                   f=distance_aphelion / distance_perihelion, 
                                   perihelion_distance=distance_perihelion)

# Example usage:
sun_radius = 206340000  # Sun's radius in meters
planet_radius = 2371000  # Planet's radius in meters
desired_temp_perihelion = calculate_temperature_from_celcius(20)  # Desired temperature at perihelion in Kelvin
desired_temp_aphelion = calculate_temperature_from_celcius(-100)  # Desired temperature at aphelion in Kelvin

sun, planet = calculate_distances_for_temperature(desired_temp_perihelion=desired_temp_perihelion, 
                                                  desired_temp_aphelion=desired_temp_aphelion, 
                                                  sun_radius=sun_radius, 
                                                  planet_radius=planet_radius)

print(sun)
print(planet)

def frames_to_time(frames, time_step):
    time_in_seconds = frames * time_step  # Total time in seconds
    
    # Define the time thresholds for each unit
    time_units = [
        (31536000, 'y'),  # years
        (86400, 'd'),    # days
        (3600, 'h'),     # hours
        (60, 'min'),     # minutes
        (1, 's'),        # seconds
        (1e-3, 'ms'),    # milliseconds
        (1e-9, 'ns'),    # nanoseconds
    ]
    
    # Find the most appropriate unit
    for unit_threshold, unit_name in time_units:
        if time_in_seconds >= unit_threshold:
            time = time_in_seconds / unit_threshold
            return f"{time:.2f} {unit_name}"
    
    # If the time is less than 1 second, return time in nanoseconds
    return f"{time_in_seconds * 1e-9:.2f} ns"

# Simulation parameters
time_step = 60  # seconds per frame
frames = 0  # Track the number of frames

# Pygame setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Orbital Simulation")
clock = pygame.time.Clock()

# Set up fonts for displaying text
pygame.font.init()
font = pygame.font.SysFont("Arial", 24)


# Main simulation loop
running = True
for _ in range(FPS // 2):
    screen.fill(BLACK)
    sun.display(screen)
    planet.display(screen)
    elapsed_time = frames_to_time(frames, time_step)

    # Render the time text at the top of the screen
    time_text = font.render(f"Time: {elapsed_time}", True, WHITE)
    screen.blit(time_text, (10, 10))  # Position the time text at the top-left

    pygame.display.flip()
    
    clock.tick(FPS)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Calculate gravitational forces
    force_on_planet = calculate_gravitational_force(planet, sun)
    force_on_sun = -force_on_planet  # Equal and opposite force

    # Update positions
    sun.update_position(force_on_sun, time_step)
    planet.update_position(force_on_planet, time_step)

    # Increment frame counter
    frames += 1

    # Calculate the time elapsed in the appropriate units
    elapsed_time = frames_to_time(frames, time_step)

    # Draw everything
    screen.fill(BLACK)
    sun.display(screen)
    planet.display(screen, 2)

    # Render the time text at the top of the screen
    time_text = font.render(f"Time: {elapsed_time}", True, WHITE)
    screen.blit(time_text, (10, 10))  # Position the time text at the top-left

    pygame.display.flip()

    clock.tick(FPS)

pygame.quit()
