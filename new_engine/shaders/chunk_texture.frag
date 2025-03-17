#version 330 core

layout (location = 0) out vec4 fragColor;

in vec3 inNormal;
in vec3 waveNormal;
in vec3 fragPos;
in float fragRealHeight;
in float fragOriginalHeight;
in vec2 texCoord;

struct Light {
    vec3 direction;
    vec3 Ia;
    vec3 Id;
    vec3 Is;
};

uniform Light light;
uniform vec3 camPos;
uniform sampler2D textureSampler;

void main() {
    vec3 viewDirection = normalize(camPos - fragPos);
    vec3 inColor = texture(textureSampler, texCoord).rgb;
    vec3 color;

    if (fragOriginalHeight <= 0) {
        vec3 normal = normalize(waveNormal);
        vec3 waterBaseColor = vec3(0.05, 0.3, 0.6); // Deeper water color
        vec3 waveHighlightColor = vec3(0.2, 0.5, 0.8); // Lighter parts of waves

        // Fresnel Effect - More reflection at shallow angles
        float fresnelFactor = pow(1.0 - max(dot(viewDirection, normal), 0.0), 3.0);
        fresnelFactor = mix(0.2, 1.0, fresnelFactor);

        // Sun Reflection Radius
        vec3 lightReflectDir = reflect(-light.direction, normal);
        float sunSize = 0.35; // Slightly bigger sun reflection
        float sunGlare = smoothstep(1.0 - sunSize, 1.0, dot(viewDirection, lightReflectDir));

        // Specular Boost - Stronger highlights on waves
        float spec = pow(max(dot(viewDirection, lightReflectDir), 0.0), 128.0);
        vec3 specular = spec * light.Is * fresnelFactor * 2.5 * sunGlare;

        // Warm Sun Tint
        vec3 sunHighlight = mix(vec3(1.0), vec3(1.0, 0.85, 0.65), 0.3);
        vec3 reflectionColor = mix(waterBaseColor, sunHighlight, sunGlare * 1.2);

        // Ensure White Accents in the Sun Reflection
        reflectionColor = mix(reflectionColor, vec3(1.0), sunGlare * 0.6);

        // **Contrast Between Waves**
        float waveFactor = clamp(dot(normal, light.direction) * 1.5, 0.0, 1.0); // Highlights on wave peaks
        vec3 finalWaterColor = mix(waterBaseColor, waveHighlightColor, waveFactor * 0.5); // Creates a visible wave contrast

        // Blend Everything Together
        color = mix(finalWaterColor, reflectionColor + specular, fresnelFactor);

        // Shallow Water Foam Effect
        if (fragOriginalHeight >= -0.04 && abs(fragOriginalHeight - fragRealHeight) <= 0.04) {
            color = mix(color, vec3(1.0, 1.0, 1.0), 0.8);
        }
    } else {
        vec3 normal = normalize(inNormal);

        // Regular Terrain Lighting
        vec3 ambient = light.Ia;

        // Calculate the alignment between the sun's direction and the view direction
        float alignment = max(dot(light.direction, viewDirection), 0.0);

        // Decrease the ambient intensity when the sun is more aligned with the view direction
        ambient *= (1.0 - alignment * 0.5);  // Adjust the factor (0.5) for the strength of the effect

        float diff = max(dot(light.direction, normal), 0.0);
        vec3 diffuse = diff * light.Id;

        vec3 reflectDir = reflect(-light.direction, normal);
        float spec = pow(max(dot(viewDirection, reflectDir), 0.0), 32.0);
        vec3 specular = spec * light.Is;

        color = (ambient + diffuse + specular) * inColor;
    }

    // fragColor = vec4(gammaCorrect(color, 2.2), 1.0);
    fragColor = vec4(color, 1.0);
}
