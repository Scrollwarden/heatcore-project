#version 330 core

layout (location = 0) out vec4 fragColor;

in vec3 normal;
in vec3 fragPos;
in vec3 inColor;
in float fragRealHeight;

struct Light {
    vec3 position;
    vec3 Ia;
    vec3 Id;
    vec3 Is;
};

uniform Light light;
uniform sampler2D u_texture_0;
uniform vec3 camPos;

void main() {
    vec3 Normal = normalize(normal);
    vec3 viewDirection = normalize(camPos - fragPos);
    vec3 lightDirection = normalize(light.position - fragPos);

    vec3 color;

    // Water surface effects
    if (fragRealHeight < 0) {
        // Simulate water with a blue tint and reflection
        vec3 reflectDirection = reflect(-viewDirection, Normal);
        vec3 refractDirection = refract(-viewDirection, Normal, 1.0 / 1.33); // Approximate refraction for water

        vec3 reflectionColor = vec3(0.08, 0.16, 0.18) * (1 - fragPos.y);
        vec3 refractionColor = inColor;
        float fresnelFactor = pow(1.0 - max(dot(viewDirection, Normal), 0.0), 3.0);
        color = mix(refractionColor, reflectionColor, fresnelFactor);

        // Add some blue tint to simulate underwater light absorption
        color = mix(color, vec3(0.0, 0.4, 0.7), 0.2); // Adjust blue tint as needed
    } else {
        // Regular lighting for non-water regions
        vec3 ambient = light.Ia;

        float difference = max(0.0, dot(lightDirection, Normal));
        vec3 diffuse = difference * light.Id;

        vec3 reflectDirection = reflect(-lightDirection, Normal);
        float spec = pow(max(dot(viewDirection, reflectDirection), 0.0), 32.0);
        vec3 specular = spec * light.Is;

        color = (ambient + diffuse + specular) * inColor;
    }

    fragColor = vec4(color, 1.0);
}