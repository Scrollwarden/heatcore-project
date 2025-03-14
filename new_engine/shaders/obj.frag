#version 330 core

layout (location = 0) out vec4 fragColor;

in vec3 inNormal;
in vec3 fragPos;
in vec3 inColor;

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
    vec3 normal = inNormal;

    // Ambient
    vec3 ambient = light.Ia;

    // Diffuse
    float difference = max(0.0, dot(light.direction, normal));
    vec3 diffuse = difference * light.Id;

    // Specular
    vec3 reflectDirection = reflect(-light.direction, normal);
    float spec = pow(max(dot(viewDirection, reflectDirection), 0.0), 32.0);
    vec3 specular = spec * light.Is;

    vec3 color = (ambient + diffuse + specular) * inColor;

    fragColor = vec4(gammaCorrect(color, 2.2), 1.0);
}