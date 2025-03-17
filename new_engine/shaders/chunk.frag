#version 330 core

layout (location = 0) out vec4 fragColor;

in vec3 inNormal;
in vec3 waveNormal;
in vec3 fragPos;
in vec3 inColor;
in float fragRealHeight;
in float fragOriginalHeight;

struct Light {
    vec3 direction;
    vec3 Ia;
    vec3 Id;
    vec3 Is;
};

uniform Light light;
uniform vec3 camPos;

// Apply gamma correction (common value is 2.2)
vec3 gammaCorrect(vec3 color, float value) {
    return pow(color, vec3(1.0 / value));
}

void main() {
    vec3 viewDirection = normalize(camPos - fragPos);
    vec3 color;

    // **Sun Height Influence Factor**
    float sunHeightFactor = max(0.1, (2 * atan(0.9 + 10 * light.direction.y) + 0.74) / 3.74);

    // **Sun Reflection Strictness Factor** (Controls reflections visibility based on sun position)
    // float sunAngle = clamp(light.direction.y * 1.2, -1.0, 1.0);  // Normalize range
    // float sunReflectionFactor = 1 - abs(light.direction.y); // Peaks at horizon, 0 at midday & night
    float sunReflectionFactor;
    float point = 0.05;
    if (light.direction.y <= point) {
        sunReflectionFactor = exp(- pow(15 * (light.direction.y - 0.05), 2));
    } else {
        sunReflectionFactor = 1 - pow(light.direction.y - point, 1 / 2) * (light.direction.y - point);
    }

    if (fragOriginalHeight <= 0) {
        vec3 normal = normalize(waveNormal);
        vec3 waterBaseColor = vec3(0.05, 0.3, 0.6);  // Deep water
        vec3 waveHighlightColor = vec3(0.2, 0.5, 0.8);  // Lighter waves
        vec3 skyColor = vec3(0.3, 0.5, 0.9); // Sky reflection

        // Fresnel Effect - More reflection at shallow angles
        float fresnelFactor = pow(1.0 - max(dot(viewDirection, normal), 0.0), 3.0);
        fresnelFactor = mix(0.2, 1.0, fresnelFactor);

        // Sun Reflection Radius (Strict Control)
        vec3 lightReflectDir = reflect(-light.direction, normal);
        float sunSize = 0.1; 
        float sunGlare = smoothstep(1.0 - sunSize, 1.0, dot(viewDirection, lightReflectDir));
        sunGlare *= sunReflectionFactor; // Removes reflections at midday & night

        // Improved Specular Highlight - Sharper reflections
        float spec = pow(max(dot(viewDirection, lightReflectDir), 0.0), 128.0);
        vec3 specular = spec * light.Is * fresnelFactor * 2.5 * sunGlare;

        // Warm Sun Tint
        vec3 sunHighlight = mix(vec3(1.0), vec3(1.0, 0.85, 0.65), 0.3);
        vec3 reflectionColor = mix(waterBaseColor, sunHighlight, sunGlare * 1.2);

        // Ensure White Accents in the Sun Reflection
        reflectionColor = mix(reflectionColor, vec3(1.0), sunGlare * 0.7);

        // **Contrast Between Waves**
        float waveFactor = clamp(dot(normal, light.direction) * 1.5, 0.0, 1.0); // Highlights on wave peaks
        vec3 finalWaterColor = mix(waterBaseColor, waveHighlightColor, waveFactor * 0.5); // Creates visible waves

        // Environmental Reflection - Mix sky and water
        vec3 envReflection = mix(finalWaterColor, skyColor, fresnelFactor * 0.3);

        // Blend Everything Together
        color = mix(envReflection, (reflectionColor + specular), fresnelFactor);

        // Shallow Water Foam Effect
        if (fragOriginalHeight >= -0.04 && abs(fragOriginalHeight - fragRealHeight) <= 0.04) {
            color = mix(color, vec3(1.0, 1.0, 1.0), 0.8);
        }
    } else {
        vec3 normal = normalize(inNormal);

        // Regular Terrain Lighting
        vec3 ambient = light.Ia;

        // Reduce ambient when sun aligns with view direction
        float alignment = max(dot(light.direction, viewDirection), 0.0);
        ambient *= (1.0 - alignment * 0.5);  

        float diff = max(dot(light.direction, normal), 0.0);
        vec3 diffuse = diff * light.Id;

        vec3 reflectDir = reflect(-light.direction, normal);
        float spec = pow(max(dot(viewDirection, reflectDir), 0.0), 32.0);
        vec3 specular = spec * light.Is;

        color = (ambient + diffuse + specular) * inColor;
    }

    // fragColor = vec4(gammaCorrect(color, 2.2), 1.0);
    fragColor = vec4(color * sunHeightFactor, 1.0);
}
