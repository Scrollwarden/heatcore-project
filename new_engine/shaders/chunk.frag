#version 330 core

layout (location = 0) out vec4 fragColor;

in vec3 inNormal;
in vec3 waveNormal;
in vec3 fragPos;
in vec3 inColor;
in float fragRealHeight;
in float fragOriginalHeight;

struct Light {
    vec3 position;
    vec3 Ia;
    vec3 Id;
    vec3 Is;
};

uniform Light light;
uniform vec3 camPos;

void main() {
    vec3 viewDirection = normalize(camPos - fragPos);
    vec3 lightDirection = normalize(light.position - fragPos);

    vec3 color;

    // Water surface effects
    if (fragOriginalHeight <= 0) {
        vec3 normal = waveNormal;
        vec3 waterColor = vec3(0.0, 0.4, 0.7);

        // Simulate water with a blue tint and reflection
        vec3 reflectDirection = reflect(-viewDirection, normal);
        vec3 refractDirection = refract(-viewDirection, normal, 1.0 / 1.33); // Approximate refraction for water

        vec3 reflectionColor = vec3(0.08, 0.16, 0.18) * (1 - fragOriginalHeight);
        vec3 refractionColor = inColor;
        float fresnelFactor = pow(1.0 - max(dot(viewDirection, normal), 0.0), 2.0);
        color = mix(refractionColor, reflectionColor, fresnelFactor);

        // Add some blue tint to simulate underwater light absorption
        color = mix(color, waterColor, 0.7); // Adjust blue tint as needed
        if (fragOriginalHeight >= -0.04 && abs(fragOriginalHeight - fragRealHeight) <= 0.04) {
            color = mix(color, vec3(1.0, 1.0, 1.0), 0.8);
        }
    } else {
        vec3 normal = inNormal;
        
        // Regular lighting for non-water regions
        vec3 ambient = light.Ia;

        float difference = max(0.0, dot(lightDirection, normal));
        vec3 diffuse = difference * light.Id;

        vec3 reflectDirection = reflect(-lightDirection, normal);
        float spec = pow(max(dot(viewDirection, reflectDirection), 0.0), 32.0);
        vec3 specular = spec * light.Is;

        color = (ambient + diffuse + specular) * inColor;
    }

    fragColor = vec4(color, 1.0);
}