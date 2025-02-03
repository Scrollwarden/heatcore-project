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
uniform vec3 camPos;

void main() {
    vec3 Normal = normalize(normal);
    vec3 viewDirection = normalize(camPos - fragPos);
    vec3 lightDirection = normalize(light.position - fragPos);
    vec3 color;

    if (fragRealHeight < 0) { 
        // --- Water Shader ---

        // Simulated reflection using screen-space texture
        vec3 reflectionDir = reflect(-viewDirection, Normal);
        vec3 reflectionColor = vec3(0.08, 0.16, 0.18) * (1 - fragPos.y);

        // Refraction effect (water absorbs light)
        vec3 waterBaseColor = vec3(0.0, 0.3, 0.6);
        float depthFactor = clamp(1.0 - abs(fragRealHeight) * 0.1, 0.4, 1.0);
        vec3 refractionColor = mix(waterBaseColor, inColor, 0.4);

        // Fresnel effect for blending reflection/refraction
        float fresnelFactor = pow(1.0 - max(dot(viewDirection, Normal), 0.0), 3.0);
        vec3 waterFinalColor = mix(refractionColor, reflectionColor, fresnelFactor);

        // Final transparency control
        fragColor = vec4(waterFinalColor * depthFactor, 0.7);
    } else {
        // --- Terrain Shader (Unchanged) ---
        vec3 ambient = light.Ia;

        float diff = max(0.0, dot(lightDirection, Normal));
        vec3 diffuse = diff * light.Id;

        vec3 reflectDirection = reflect(-lightDirection, Normal);
        float spec = pow(max(dot(viewDirection, reflectDirection), 0.0), 32.0);
        vec3 specular = spec * light.Is;

        color = (ambient + diffuse + specular) * inColor;
        fragColor = vec4(color, 1.0);
    }
}
